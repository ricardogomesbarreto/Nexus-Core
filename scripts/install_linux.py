"""Interactive Ubuntu/Debian bootstrap for Nexus Core user-managed installation.

Run from a reviewed source checkout with Python 3.12+:
    python3 scripts/install_linux.py

No shell pipelines, root-owned venv, auto-added Docker group, or unapproved
system changes. Other distributions receive a dependency report instead.
"""
import json
import os
from pathlib import Path
import secrets
import shutil
import subprocess
import sys
import tempfile
import venv


ROOT = Path(__file__).resolve().parents[1]
MIN_VERSION = (3, 12)
SYSTEM_PACKAGES = (
    "python3-venv", "python3-tk", "postgresql", "xdotool",
    "espeak-ng", "alsa-utils", "ffmpeg",
)


def confirm(question: str) -> bool:
    if not sys.stdin.isatty():
        return False
    try:
        return input(question + " [s/N]: ").strip().lower() in ("s", "sim")
    except (EOFError, KeyboardInterrupt):
        return False


def installed(command: str) -> bool:
    return shutil.which(command) is not None


def _run(args: list[str], *, input_text=None, timeout=300,
         capture=False) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, input=input_text, text=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, timeout=timeout, check=True,
    )


def _debian_family() -> bool:
    try:
        info = Path("/etc/os-release").read_text(encoding="utf-8")
    except OSError:
        return False
    return any(line.startswith("ID=" + distro) or line.startswith("ID_LIKE=" + distro)
               for distro in ("ubuntu", "debian")) or " debian" in info


def system_requirements() -> list[str]:
    missing = []
    for binary in ("psql", "xdotool", "espeak-ng", "arecord", "ffmpeg"):
        if not installed(binary):
            missing.append(binary)
    try:
        import tkinter
        del tkinter
    except ImportError:
        missing.append("python3-tk")
    return missing


def install_system_packages() -> None:
    missing = system_requirements()
    if not missing:
        print("Dependências de sistema encontradas.")
        return
    print("Dependências ausentes: " + ", ".join(missing))
    if not _debian_family() or not installed("apt-get") or not installed("sudo"):
        print("Distribuição sem instalador apt/sudo suportado; "
              "instale os componentes pelo gerenciador oficial do Linux.")
        return
    if not confirm("Instalar pacotes oficiais via sudo apt-get?"):
        print("Instalação de pacotes de sistema recusada.")
        return
    try:
        _run(["sudo", "apt-get", "update"], timeout=300)
        _run(["sudo", "apt-get", "install", "-y", *SYSTEM_PACKAGES], timeout=600)
    except (OSError, subprocess.SubprocessError):
        print("Não foi possível concluir apt-get; verifique os pacotes manualmente.")


def _credentials_file() -> Path:
    config = os.environ.get("XDG_CONFIG_HOME")
    base = Path(config).expanduser() if config and Path(config).is_absolute() else Path.home() / ".config"
    return base / "nexus-core" / "credentials.json"


def _existing_credentials() -> bool:
    file = _credentials_file()
    return file.is_file() and not file.is_symlink() and file.stat().st_mode & 0o077 == 0


def provision_postgresql() -> None:
    if _existing_credentials():
        print("Credenciais locais de PostgreSQL já configuradas; nenhuma senha foi alterada.")
        return
    if not installed("psql") or not installed("sudo"):
        print("PostgreSQL precisa ser configurado antes do primeiro uso.")
        return
    if not confirm("Configurar banco local exclusivo 'nexus' e usuário 'nexus'?"):
        print("Banco não configurado automaticamente.")
        return
    try:
        def query(sql: str) -> str:
            result = _run(["sudo", "-u", "postgres", "psql", "-X",
                           "-v", "ON_ERROR_STOP=1", "-tA", "-d", "postgres"],
                          input_text=sql, timeout=30, capture=True)
            return result.stdout.strip()
        role_exists = query("SELECT 1 FROM pg_roles WHERE rolname='nexus';") == "1"
        db_exists = query("SELECT 1 FROM pg_database WHERE datname='nexus';") == "1"
        if role_exists or db_exists:
            print("Usuário ou banco existente: configuração preservada. "
                  "Configure NEXUS_DATABASE_PASSWORD manualmente.")
            return
        password = secrets.token_urlsafe(36)
        # SQL goes on stdin, never argv or printed output.
        query(f"CREATE ROLE nexus LOGIN PASSWORD '{password}';")
        query("CREATE DATABASE nexus OWNER nexus;")
        file = _credentials_file()
        if file.is_symlink() or file.parent.is_symlink():
            raise RuntimeError("Caminho de credenciais inseguro.")
        file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
        file.parent.chmod(0o700)
        fd, temp_name = tempfile.mkstemp(prefix=".db-", dir=file.parent)
        try:
            with os.fdopen(fd, "w", encoding="utf-8") as stream:
                os.fchmod(stream.fileno(), 0o600)
                json.dump({"database_password": password}, stream)
            os.replace(temp_name, file)
        finally:
            Path(temp_name).unlink(missing_ok=True)
        print("PostgreSQL local configurado e credenciais protegidas (0600).")
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print("Provisionamento do PostgreSQL incompleto; confira a configuração "
              "antes de usar o assistente. Nenhuma senha foi exibida.")


def install_managed_python():
    from nexus.config.settings import settings
    from nexus.updates.manager import (
        _private_directory, _switch_current, managed_home,
    )
    home = _private_directory(managed_home())
    versions = _private_directory(home / "versions")
    target = versions / ("v" + settings.version)
    if target.is_symlink():
        raise RuntimeError("Ambiente de instalação inseguro.")
    if not target.exists():
        venv.create(target, with_pip=True, symlinks=False)
    python = target / "bin/python"
    _run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check",
         "--no-input", "-e", ".[voice,vision]"],
        timeout=600,
    )
    _run([str(python), "-m", "pip", "check"], timeout=30)
    _run([str(python), "-m", "nexus.main", "--version"], timeout=20)
    _switch_current(home, target)
    return home


def write_launcher(home: Path) -> Path:
    bin_dir = Path.home() / ".local" / "bin"
    bin_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination = bin_dir / "nexus-core"
    marker = "# NEXUS-CORE-MANAGED-LAUNCHER"
    if destination.is_symlink():
        raise RuntimeError("Não substituímos links simbólicos de executáveis.")
    if destination.exists() and marker not in destination.read_text(encoding="utf-8")[:250]:
        raise RuntimeError("Há outro executável nexus-core; não será substituído.")
    content = f"""#!/usr/bin/env python3
{marker}
import json
import os
import pathlib
import sys
home = pathlib.Path({str(home)!r})
secret = pathlib.Path({str(_credentials_file())!r})
if secret.is_file() and not secret.is_symlink():
    info = secret.stat()
    if info.st_uid == os.getuid() and info.st_mode & 0o077 == 0:
        try:
            value = json.loads(secret.read_text(encoding="utf-8"))
            if isinstance(value.get("database_password"), str):
                os.environ.setdefault(
                    "NEXUS_DATABASE_PASSWORD", value["database_password"]
                )
        except (OSError, ValueError, AttributeError):
            pass
os.environ["NEXUS_RUNNING_MANAGED"] = "1"
python = home / "current" / "bin" / "python"
os.execv(str(python), [str(python), "-m", "nexus.updates.launcher", *sys.argv[1:]])
"""
    fd, name = tempfile.mkstemp(prefix=".nexus-launcher-", dir=bin_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fchmod(stream.fileno(), 0o700)
        os.replace(name, destination)
    finally:
        Path(name).unlink(missing_ok=True)
    return destination


def main() -> int:
    if os.geteuid() == 0:
        print("Execute como usuário comum; sudo só quando autorizado.", file=sys.stderr)
        return 2
    if sys.version_info < MIN_VERSION:
        print("Python 3.12 ou superior é necessário.", file=sys.stderr)
        return 2
    if sys.platform != "linux":
        print("Somente Linux é suportado.", file=sys.stderr)
        return 2
    print("NEXUS CORE — instalação guiada e gerenciada (sem custos adicionais).")
    install_system_packages()
    provision_postgresql()
    try:
        home = install_managed_python()
        executable = write_launcher(home)
        from nexus.updates.manager import set_autoupdate
        enabled = confirm("Ativar verificação automática de releases estáveis?")
        set_autoupdate(enabled, home)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print("Falha na instalação do ambiente Python do usuário.", file=sys.stderr)
        return 2
    print(f"Instalação concluída: {executable}")
    print("Executar: ~/.local/bin/nexus-core")
    print("Atualizações automáticas: " + ("ativadas" if enabled else "desativadas"))
    if not installed("ollama"):
        print("Ollama ainda ausente: instale pelo canal oficial; nunca executamos curl|bash.")
    else:
        print("Ollama detectado. Instale modelos explicitamente, se necessário: "
              "ollama pull qwen3:1.7b")
    if not installed("docker"):
        print("Docker não detectado; recursos de sandbox exigem instalação/configuração independente.")
    print("Modelos de voz Vosk, permissões de áudio/câmera e testes físicos "
          "continuam sujeitos ao diagnóstico na máquina do usuário.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
