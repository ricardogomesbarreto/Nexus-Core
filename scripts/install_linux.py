"""Interactive Ubuntu 24.04 LTS bootstrap for Nexus Core user-managed installation.

Run from a reviewed source checkout with Python 3.12+:
    python3 scripts/install_linux.py

No shell pipelines, root-owned venv, auto-added Docker group, or unapproved
system changes. Other distributions receive a passive report; installation refuses mutations.
"""
import argparse
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
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MIN_VERSION = (3, 12)
from nexus.platforms import UBUNTU_PACKAGES, linux_profile, platform_capabilities
SYSTEM_PACKAGES = UBUNTU_PACKAGES


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
         capture=False, cwd=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, input=input_text, text=True,
        stdout=subprocess.PIPE if capture else subprocess.DEVNULL,
        stderr=subprocess.DEVNULL, timeout=timeout, check=True,
        cwd=cwd,
    )


def _ubuntu_supported() -> bool:
    """Never infer package-manager permissions from ID_LIKE=debian."""
    return linux_profile().installer_supported


def system_requirements() -> list[str]:
    """Passively inspect required desktop helpers; no service connection."""
    report = platform_capabilities()
    missing = list(report["missing_required"])
    if not installed("xdotool"):
        # X11 automation is optional for Wayland, but should be installed on
        # Ubuntu to permit the separate physical X11 acceptance tests.
        missing.append("xdotool")
    return missing


def install_system_packages() -> bool:
    """Install official Ubuntu packages only with explicit operator consent.

    A refusal or unresolved dependency blocks the bootstrap rather than
    falsely reporting the application as fully installed.
    """
    if not _ubuntu_supported():
        print("Instalador não habilitado nesta distribuição; rode --check.")
        return False
    missing = system_requirements()
    if not missing:
        print("Dependências de sistema encontradas.")
        return True
    print("Dependências ausentes: " + ", ".join(missing))
    if not installed("apt-get") or not installed("sudo"):
        print("apt-get/sudo indisponíveis: instalação guiada interrompida.")
        return False
    if not confirm("Instalar pacotes oficiais Ubuntu via sudo apt-get?"):
        print("Instalação de pacotes recusada; nenhuma etapa seguinte foi executada.")
        return False
    try:
        _run(["sudo", "apt-get", "update"], timeout=300)
        _run(["sudo", "apt-get", "install", "-y", *SYSTEM_PACKAGES], timeout=600)
    except (OSError, subprocess.SubprocessError):
        print("apt-get falhou; verifique os pacotes antes de tentar novamente.")
        return False
    unresolved = system_requirements()
    if unresolved:
        print("Dependências ainda ausentes: " + ", ".join(unresolved))
        return False
    return True


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
    # Regular local package install: unlike pip -e, it does not depend on
    # keeping the development checkout in the same filesystem location.
    _run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check",
         "--no-input", str(ROOT) + "[voice,vision]"],
        timeout=600, cwd=ROOT,
    )
    _run([str(python), "-m", "pip", "check"], timeout=30)
    verified = _run(
        [str(python), "-m", "nexus.main", "--version"],
        timeout=20, capture=True, cwd=home,
    )
    if verified.stdout.strip() != "Nexus Core " + settings.version:
        raise RuntimeError("A instalação Python retornou versão divergente.")
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


def write_recovery_launcher(home: Path) -> Path:
    """Deploy standalone stdlib recovery before the managed Python can break.

    Unlike calling the installed Nexus package, this helper still runs
    through Ubuntu's system python3 even after a failed update.
    """
    from nexus.updates.manager import _private_directory
    _private_directory(home)
    bin_dir = Path.home() / ".local" / "bin"
    if bin_dir.is_symlink():
        raise RuntimeError("Diretório de executáveis é um link simbólico.")
    bin_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination = bin_dir / "nexus-core-recover"
    marker = '"""Standalone Ubuntu recovery entry point'
    if destination.is_symlink():
        raise RuntimeError("Link simbólico para recuperação não autorizado.")
    if destination.exists() and marker not in destination.read_text(encoding="utf-8")[:300]:
        raise RuntimeError("Não substituir utilitário de recuperação desconhecido.")
    source = (ROOT / "nexus" / "updates" / "recovery.py").read_text(encoding="utf-8")
    placeholder = "_INSTALL_HOME = None"
    if source.count(placeholder) != 1 or marker not in source[:300]:
        raise RuntimeError("Código de recuperação não possui contrato reconhecido.")
    embedded = source.replace(placeholder, "_INSTALL_HOME = " + repr(str(home)))
    fd, name = tempfile.mkstemp(prefix=".nexus-recover-", dir=bin_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o700)
            stream.write(embedded)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, destination)
    finally:
        Path(name).unlink(missing_ok=True)
    return destination


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="NEXUS CORE — instalação Ubuntu Desktop")
    parser.add_argument("--check", action="store_true",
                        help="mostra diagnóstico somente leitura, em qualquer distribuição")
    args = parser.parse_args(argv)
    if args.check:
        print(json.dumps(platform_capabilities(), ensure_ascii=False))
        return 0
    if os.geteuid() == 0:
        print("Execute como usuário comum; sudo só quando autorizado.", file=sys.stderr)
        return 2
    if sys.version_info < MIN_VERSION:
        print("Python 3.12 ou superior é necessário.", file=sys.stderr)
        return 2
    if sys.platform != "linux":
        print("Somente Linux é suportado.", file=sys.stderr)
        return 2
    profile = linux_profile()
    if not profile.installer_supported:
        print("Instalação automática validada apenas para Ubuntu Desktop 24.04 LTS; "
              "em outras distribuições use --check. Nada foi instalado.", file=sys.stderr)
        return 2
    print("NEXUS CORE — instalação guiada para Ubuntu Desktop 24.04 LTS.")
    if not install_system_packages():
        print("Instalação interrompida: requisitos do Ubuntu ainda ausentes.", file=sys.stderr)
        return 2
    provision_postgresql()
    try:
        home = install_managed_python()
        executable = write_launcher(home)
        recovery = write_recovery_launcher(home)
        from nexus.updates.manager import set_autoupdate
        enabled = confirm("Ativar verificação automática de releases estáveis?")
        set_autoupdate(enabled, home)
    except (OSError, RuntimeError, subprocess.SubprocessError) as exc:
        print("Falha na instalação do ambiente Python do usuário.", file=sys.stderr)
        return 2
    print(f"Instalação concluída: {executable}")
    print(f"Recuperação offline instalada: {recovery}")
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
