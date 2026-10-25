"""Interactive Ubuntu bootstrap for Nexus Core user-managed installation.

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
import tarfile
import tempfile
import venv
import zipfile


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
MIN_VERSION = (3, 12)
from nexus.platforms import UBUNTU_PACKAGES, linux_profile, platform_capabilities
SYSTEM_PACKAGES = UBUNTU_PACKAGES
PACKAGES_FOR_MISSING = {
    "psql": ("postgresql", "postgresql-client"),
    "pg_isready": ("postgresql", "postgresql-client"),
    "espeak-ng": ("espeak-ng",),
    "arecord": ("alsa-utils",),
    "ffmpeg": ("ffmpeg",),
    "xdg-settings": ("xdg-utils",),
    "gtk-launch": ("libgtk-3-bin",),
    "python3-tk": ("python3-tk",),
    "python3-venv": ("python3-venv",),
}


def confirm(question: str) -> bool:
    if not sys.stdin.isatty():
        return False
    try:
        return input(question + " [s/N]: ").strip().lower() in ("s", "sim")
    except (EOFError, KeyboardInterrupt):
        return False


def installed(command: str) -> bool:
    return shutil.which(command) is not None


def _service_active_for_install(scope: str, unit: str) -> bool:
    args = ["systemctl", "--user"] if scope == "user" else ["systemctl"]
    try:
        _run([*args, "is-active", "--quiet", unit], timeout=5)
        return True
    except (OSError, subprocess.SubprocessError):
        return False


def _run(args: list[str], *, input_text=None, timeout=300,
         capture=False, progress=False, cwd=None, env=None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args, input=input_text, text=True,
        stdout=subprocess.PIPE if capture else (None if progress else subprocess.DEVNULL),
        stderr=None if progress else subprocess.DEVNULL, timeout=timeout, check=True,
        cwd=cwd, env=env,
    )


def _ubuntu_supported() -> bool:
    """Never infer package-manager permissions from ID_LIKE=debian."""
    return linux_profile().installer_supported


def system_requirements() -> list[str]:
    """Passively inspect required desktop helpers; no service connection."""
    report = platform_capabilities()
    missing = list(report["missing_required"])
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
    if any(requirement not in PACKAGES_FOR_MISSING for requirement in missing):
        print("Dependência sem pacote Ubuntu conhecido; instalação interrompida.")
        return False
    packages = [package for package in SYSTEM_PACKAGES
                if any(package in PACKAGES_FOR_MISSING[requirement]
                       for requirement in missing)]
    if not installed("apt-get") or not installed("sudo"):
        print("apt-get/sudo indisponíveis: instalação guiada interrompida.")
        return False
    if not confirm("Instalar pacotes oficiais Ubuntu via sudo apt-get?"):
        print("Instalação de pacotes recusada; nenhuma etapa seguinte foi executada.")
        return False
    try:
        _run(["sudo", "apt-get", "update"], timeout=300)
        _run(["sudo", "apt-get", "install", "-y", *packages], timeout=600)
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
    # Apply the same validation as the managed launcher. A private but
    # malformed file must not make installation appear complete.
    from nexus.updates.managed_entrypoint import load_local_password
    return load_local_password(_credentials_file()) is not None


def _save_credentials(password: str, database_name: str, database_user: str) -> None:
    """Store credentials only in an owner-private file; never replace one."""
    file = _credentials_file()
    if file.is_symlink() or file.parent.is_symlink() or file.exists():
        raise RuntimeError("Caminho de credenciais já existente ou inseguro.")
    file.parent.mkdir(mode=0o700, parents=True, exist_ok=True)
    file.parent.chmod(0o700)
    fd, temp_name = tempfile.mkstemp(prefix=".db-", dir=file.parent)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            os.fchmod(stream.fileno(), 0o600)
            json.dump({"database_password": password,
                       "database_name": database_name,
                       "database_user": database_user}, stream)
        os.replace(temp_name, file)
    finally:
        Path(temp_name).unlink(missing_ok=True)


def provision_postgresql() -> bool:
    if _existing_credentials():
        print("Credenciais locais de PostgreSQL já configuradas; nenhuma senha foi alterada.")
        return True
    if os.environ.get("NEXUS_DATABASE_PASSWORD", "").strip():
        print("Senha PostgreSQL informada pelo ambiente; configuração manual preservada.")
        return True
    if not installed("psql") or not installed("sudo"):
        print("PostgreSQL precisa ser configurado antes do primeiro uso.")
        return False
    if not confirm("Configurar banco local exclusivo 'nexus' e usuário 'nexus'?"):
        print("Banco não configurado automaticamente.")
        return False
    try:
        def query(sql: str) -> str:
            result = _run(["sudo", "-u", "postgres", "psql", "-X",
                           "-v", "ON_ERROR_STOP=1", "-tA", "-d", "postgres"],
                          input_text=sql, timeout=30, capture=True)
            return result.stdout.strip()
        database_name = "nexus"
        role_exists = query("SELECT 1 FROM pg_roles WHERE rolname='nexus';") == "1"
        db_exists = query("SELECT 1 FROM pg_database WHERE datname='nexus';") == "1"
        if role_exists or db_exists:
            print("Usuário ou banco 'nexus' existente: configuração preservada.")
            if not confirm("Criar usuário e banco exclusivos 'nexus_core' para este assistente?"):
                print("Banco não configurado automaticamente.")
                return False
            database_name = "nexus_core"
            if (query("SELECT 1 FROM pg_roles WHERE rolname='nexus_core';") == "1"
                    or query("SELECT 1 FROM pg_database WHERE datname='nexus_core';") == "1"):
                print("Usuário ou banco 'nexus_core' já existe; nenhuma senha foi alterada. "
                      "Configure credenciais manualmente.")
                return False
        password = secrets.token_urlsafe(36)
        # SQL goes on stdin, never argv or printed output.
        query(f"CREATE ROLE {database_name} LOGIN PASSWORD '{password}';")
        query(f"CREATE DATABASE {database_name} OWNER {database_name};")
        _save_credentials(password, database_name, database_name)
        print("PostgreSQL local configurado e credenciais protegidas (0600).")
        return _existing_credentials()
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print("Provisionamento do PostgreSQL incompleto; confira a configuração "
              "antes de usar o assistente. Nenhuma senha foi exibida.")
        return False


def _user_ollama_service(binary: Path) -> None:
    """Start local Ollama on demand; never enable autostart at user login."""
    unit_dir = Path.home() / ".config" / "systemd" / "user"
    if unit_dir.is_symlink():
        raise RuntimeError("Pasta de serviços do usuário insegura.")
    unit_dir.mkdir(parents=True, mode=0o700, exist_ok=True)
    unit = unit_dir / "nexus-core-ollama.service"
    if unit.exists() or unit.is_symlink():
        raise RuntimeError("Serviço Ollama do Nexus já existe; confira manualmente.")
    executable = str(binary).replace("%", "%%").replace("\\", "\\\\").replace('"', '\\"')
    # A static user unit is startable but has no [Install] section and
    # cannot be automatically enabled for login. The desktop workload must
    # not silently remain resident or consume RAM on subsequent boots.
    content = ("[Unit]\nDescription=Ollama local do Nexus Core\n"
               "[Service]\nType=simple\nExecStart=\"" + executable + "\" serve\n"
               "Environment=OLLAMA_HOST=127.0.0.1:11434\nRestart=on-failure\n")
    unit.write_text(content, encoding="utf-8")
    unit.chmod(0o600)
    _run(["systemctl", "--user", "daemon-reload"], timeout=30)
    _run(["systemctl", "--user", "start", unit.name], timeout=30)
    from nexus.platforms.session_services import record_started_service
    if not record_started_service("user", unit.name):
        print("Serviço Ollama iniciado pelo instalador sem registro para parada "
              "automática; confira a sessão e pare manualmente ao terminar.")


def prepare_local_models() -> bool:
    """Ensure local LLM and Portuguese recognition assets before activation."""
    from nexus.config.settings import settings
    from nexus.platforms.preflight import ollama_model_probe
    from scripts.local_models import install_ollama_runtime, install_portuguese_voice_model
    from time import monotonic, sleep

    binary = shutil.which("ollama")
    managed = settings.data_dir / "runtime" / "ollama" / "bin" / "ollama"
    if binary is None and managed.is_file() and not managed.is_symlink():
        binary = str(managed)
        if installed("systemctl"):
            try:
                already_running = _service_active_for_install("user", "nexus-core-ollama.service")
                _run(["systemctl", "--user", "start", "nexus-core-ollama.service"], timeout=30)
                if not already_running:
                    from nexus.platforms.session_services import record_started_service
                    if not record_started_service("user", "nexus-core-ollama.service"):
                        print("Ollama iniciado sem registro para parada automática; "
                              "pare manualmente ao terminar.")
            except (OSError, subprocess.SubprocessError):
                print("Não foi possível iniciar o serviço Ollama do usuário.")
                return False
    if binary is None:
        if not confirm("Instalar Ollama oficial no diretório privado do usuário (download grande)?"):
            print("Ollama necessário para conversar; instalação incompleta.")
            return False
        if not installed("systemctl"):
            print("systemd de usuário indisponível; instale/inicie Ollama e tente novamente.")
            return False
        if not installed("zstd"):
            if not installed("sudo") or not confirm("Instalar zstd pelos pacotes Ubuntu?"):
                print("zstd é necessário para descompactar o pacote oficial Ollama.")
                return False
            try:
                _run(["sudo", "apt-get", "update"], timeout=300)
                _run(["sudo", "apt-get", "install", "-y", "zstd"], timeout=600)
            except (OSError, subprocess.SubprocessError):
                print("Não foi possível instalar zstd.")
                return False
        try:
            print("Baixando Ollama do site oficial para o usuário atual…")
            binary = str(install_ollama_runtime(managed.parents[1]))
            _user_ollama_service(Path(binary))
        except (OSError, ValueError, RuntimeError, tarfile.TarError,
                subprocess.SubprocessError):
            print("Instalação Ollama incompleta; confira o serviço do usuário e tente novamente.")
            return False

    probe = ollama_model_probe(model_name=settings.local_model_name)
    if (probe["status"] == "service_unavailable" and binary != str(managed)
            and installed("sudo") and installed("systemctl")
            and confirm("Iniciar o serviço Ollama existente via sudo systemctl?")):
        try:
            already_running = _service_active_for_install("system", "ollama.service")
            _run(["sudo", "systemctl", "start", "ollama"], timeout=30)
            if not already_running:
                from nexus.platforms.session_services import record_started_service
                if not record_started_service("system", "ollama.service"):
                    print("Ollama iniciado sem registro para parada automática; "
                          "pare manualmente ao terminar.")
        except (OSError, subprocess.SubprocessError):
            print("Serviço Ollama não pôde ser iniciado.")
            return False
    if probe["status"] == "service_unavailable":
        deadline = monotonic() + 15
        while probe["status"] == "service_unavailable" and monotonic() < deadline:
            sleep(1)
            probe = ollama_model_probe(model_name=settings.local_model_name)
    if not probe["installed"]:
        if probe["status"] == "service_unavailable":
            print("Serviço Ollama não responde em 127.0.0.1:11434.")
            return False
        if not confirm(f"Baixar modelo Ollama {settings.local_model_name} (aprox. 1,4 GB)?"):
            print("Modelo de conversa ausente; instalação incompleta.")
            return False
        try:
            print("Baixando o modelo de conversa com Ollama…")
            _run([binary, "pull", settings.local_model_name], timeout=3600, progress=True)
        except (OSError, subprocess.SubprocessError):
            print("Download do modelo Ollama falhou; pode ser retomado ao reinstalar.")
            return False
        deadline = monotonic() + 15
        while not ollama_model_probe(model_name=settings.local_model_name)["installed"]:
            if monotonic() >= deadline:
                print("Ollama não confirmou a presença do modelo baixado.")
                return False
            sleep(1)
    else:
        print(f"Modelo Ollama {settings.local_model_name} já disponível; download dispensado.")

    # Text and vision models are distinct: qwen3:1.7b cannot inspect PNGs.
    # A multi-gigabyte model is never pulled without an explicit decision.
    vision_model = os.environ.get("NEXUS_VISION_MODEL", "gemma3:4b").strip()
    from nexus.vision.local import LocalVision
    try:
        vision_model = LocalVision.validate_model(vision_model)
    except (ValueError, TypeError):
        print("NEXUS_VISION_MODEL inválido; escolha um identificador Ollama local.")
        vision_model = "gemma3:4b"
    vision_probe = ollama_model_probe(model_name=vision_model)
    if not vision_probe.get("installed", False):
        if confirm(
            f"Instalar modelo visual Ollama {vision_model} (download de vários GB)? "
            "Necessário para compreender imagens, webcam e tela."
        ):
            try:
                _run([binary, "pull", vision_model], timeout=7200, progress=True)
                if not ollama_model_probe(model_name=vision_model).get("installed", False):
                    print("Modelo visual ainda não confirmado; verifique ollama list.")
            except (OSError, subprocess.SubprocessError):
                print("Download do modelo visual falhou; a conversa por texto continua disponível.")
        else:
            print(
                f"Visão ficará indisponível até instalar o modelo: ollama pull {vision_model}"
            )
    else:
        print(f"Modelo visual {vision_model} já instalado.")

    default = settings.data_dir / "voice" / "vosk-model-small-pt-0.3"
    voice_path = settings.voice_model_path or default
    if not voice_path.is_dir():
        if voice_path != default:
            print("Modelo Vosk configurado em caminho personalizado ausente.")
            return False
        if not confirm("Baixar o modelo Vosk oficial em português (31 MB)?"):
            print("Modelo de voz ausente; instalação incompleta.")
            return False
        try:
            print("Baixando modelo Vosk em português…")
            install_portuguese_voice_model(default)
        except (OSError, ValueError, zipfile.BadZipFile):
            print("Download do modelo Vosk falhou; tente novamente.")
            return False
    else:
        print("Modelo Vosk em português já disponível; download dispensado.")
    return True


def prepare_neural_voice(home: Path) -> bool:
    """Optional local neural TTS; its failure cannot invalidate text chat."""
    from nexus.config.settings import settings
    from scripts.local_models import PIPER_VOICE, install_piper_voice

    destination = settings.data_dir / "voice" / "piper" / (PIPER_VOICE + ".onnx")
    python = home / "current" / "bin" / "python"
    binary = home / "current" / "bin" / "piper"
    if destination.is_file() and destination.with_suffix(".onnx.json").is_file() and binary.is_file():
        print("Voz neural masculina Piper já instalada.")
        return True
    if not confirm("Instalar voz neural masculina em português (Piper, download adicional)?"):
        print("Voz neural dispensada; síntese eSpeak NG continua disponível.")
        return False
    try:
        _run([str(python), "-m", "pip", "install", "--disable-pip-version-check",
              "--no-input", "piper-tts>=1.3,<2"], timeout=600, cwd=home,
             progress=True)
        install_piper_voice(destination)
        print("Voz neural masculina instalada; selecione Masculina na janela.")
        return True
    except (OSError, ValueError, RuntimeError, subprocess.SubprocessError):
        print("Voz neural indisponível neste Ubuntu/Python; "
              "a instalação de conversa e eSpeak NG foi preservada.")
        return False


def prepare_female_voice() -> bool:
    """Install Ubuntu's open RHVoice Leticia voice when explicitly selected."""
    from nexus.voice.local import LocalSpeaker
    if LocalSpeaker.female_voice_ready():
        print("Voz feminina RHVoice Letícia já instalada.")
        return True
    if not installed("sudo") or not confirm(
        "Instalar voz feminina RHVoice Letícia pelos pacotes Ubuntu (multiverse)?"
    ):
        print("Voz feminina eSpeak NG continua disponível.")
        return False
    try:
        _run(["sudo", "apt-get", "install", "-y", "rhvoice",
              "rhvoice-brazilian-portuguese"], timeout=600, progress=True)
    except (OSError, subprocess.SubprocessError):
        print("RHVoice indisponível nos repositórios habilitados; "
              "a voz feminina eSpeak NG continua disponível.")
        return False
    if not LocalSpeaker.female_voice_ready():
        print("Voz RHVoice não foi encontrada após a instalação dos pacotes.")
        return False
    print("Voz feminina RHVoice Letícia instalada.")
    return True


class PostgreSQLAuthenticationError(RuntimeError):
    """The configured local credentials were not proved by a read-only login."""


def verify_local_postgresql(python: Path, home: Path) -> None:
    """Authenticate through the installed runtime before making it current.

    The password is passed only in the child environment, never in argv or
    diagnostics. An Ollama/Vosk failure does not invalidate a PostgreSQL login.
    """
    from nexus.updates.managed_entrypoint import load_local_database_config
    password = os.environ.get("NEXUS_DATABASE_PASSWORD")
    config = load_local_database_config(_credentials_file())
    if not password and config is not None:
        password = config["database_password"]
    if not password:
        raise PostgreSQLAuthenticationError("Credenciais locais indisponíveis.")
    environment = os.environ.copy()
    environment["NEXUS_DATABASE_PASSWORD"] = password
    if config is not None:
        environment.setdefault("NEXUS_DATABASE_NAME", config["database_name"])
        environment.setdefault("NEXUS_DATABASE_USER", config["database_user"])
    try:
        result = _run(
            [str(python), "-I", "-m", "nexus.main", "--ubuntu-preflight"],
            timeout=25, capture=True, cwd=home, env=environment,
        )
        if len(result.stdout) > 65_536:
            raise ValueError("Resposta de diagnóstico extensa.")
        report = json.loads(result.stdout)
        if (type(report) is not dict
                or report.get("schema") != "nexus.ubuntu-preflight.v1"
                or type(report.get("checks")) is not dict
                or report["checks"].get("postgresql_authenticated") is not True
                or type(report.get("status")) is not dict
                or report["status"].get("postgresql") != "authenticated_read_only"):
            raise PostgreSQLAuthenticationError("Login PostgreSQL não confirmado.")
    except (OSError, subprocess.SubprocessError, ValueError, TypeError) as exc:
        raise PostgreSQLAuthenticationError("Login PostgreSQL não confirmado.") from exc


def ensure_postgresql_running_for_install() -> bool:
    """Request one-time service start when PostgreSQL is stopped.

    Never enable services at boot or change cluster settings. The subsequent
    verify_local_postgresql() must still authenticate with SELECT 1; pg_isready
    by itself is not a successful authentication test.
    """
    import re
    from time import monotonic, sleep

    port_text = os.environ.get("NEXUS_DATABASE_PORT", "5432")
    if not port_text.isdecimal() or not 1 <= int(port_text) <= 65535:
        print("Porta PostgreSQL inválida; instalação não alterada.")
        return False
    if not installed("pg_isready"):
        print("Cliente pg_isready indisponível; configure PostgreSQL antes de instalar.")
        return False

    def ready() -> bool:
        try:
            _run(
                ["pg_isready", "-q", "-h", "127.0.0.1", "-p", port_text],
                timeout=5,
            )
            return True
        except (OSError, subprocess.SubprocessError):
            return False

    if ready():
        return True
    print(f"PostgreSQL local na porta {port_text} está parado.")
    if not (installed("pg_lsclusters") and installed("systemctl") and installed("sudo")):
        print("Inicie o PostgreSQL local manualmente e repita o instalador.")
        return False
    try:
        found = _run(["pg_lsclusters", "--no-header"], capture=True, timeout=5)
    except (OSError, subprocess.SubprocessError):
        print("Clusters PostgreSQL não puderam ser consultados.")
        return False
    units = []
    for line in found.stdout.splitlines():
        fields = line.split()
        if (len(fields) >= 4 and fields[2] == port_text
                and re.fullmatch(r"[0-9]+", fields[0])
                and re.fullmatch(r"[A-Za-z0-9_-]+", fields[1])):
            units.append(f"postgresql@{fields[0]}-{fields[1]}.service")
    if len(units) != 1:
        print("Não foi possível identificar um cluster PostgreSQL único para a porta.")
        return False
    unit = units[0]
    if not confirm(f"Iniciar apenas {unit} para autenticar a instalação agora?"):
        print("Inicie o PostgreSQL quando for instalar; nenhuma unidade habilitada.")
        return False
    try:
        already_running = _service_active_for_install("system", unit)
        _run(["sudo", "systemctl", "start", unit], timeout=35)
        if not already_running:
            from nexus.platforms.session_services import record_started_service
            if not record_started_service("system", unit):
                print("PostgreSQL iniciado sem registro para parada automática; "
                      "pare manualmente ao terminar.")
    except (OSError, subprocess.SubprocessError):
        print("PostgreSQL não pôde ser iniciado. Confira o estado do serviço.")
        return False
    deadline = monotonic() + 12
    while monotonic() < deadline:
        if ready():
            print("PostgreSQL local iniciado para validar a instalação.")
            return True
        sleep(0.5)
    print("PostgreSQL iniciou, mas a porta local não ficou pronta a tempo.")
    return False


def install_managed_python():
    from nexus.updates.recovery import RecoveryError, maintenance_lock
    from nexus.updates.manager import _private_directory, managed_home
    home = _private_directory(managed_home())
    try:
        with maintenance_lock(home):
            return _install_managed_python_locked(home)
    except RecoveryError as exc:
        raise RuntimeError("Instalação já está em manutenção.") from exc


def _install_managed_python_locked(home: Path):
    from nexus.config.settings import settings
    from nexus.updates.manager import (
        _private_directory, _switch_current, managed_home,
    )
    versions = _private_directory(home / "versions")
    target = versions / ("v" + settings.version)
    if target.is_symlink():
        raise RuntimeError("Ambiente de instalação inseguro.")
    if not target.exists():
        venv.create(target, with_pip=True, symlinks=False)
    # The launcher must never execute a runtime from a public folder.
    target.chmod(0o700)
    python = target / "bin/python"
    # Regular local package install: unlike pip -e, it does not depend on
    # keeping the development checkout in the same filesystem location.
    _run(
        [str(python), "-m", "pip", "install", "--disable-pip-version-check",
         "--no-input", str(ROOT) + "[voice,vision,maps]"],
        timeout=600, cwd=ROOT,
    )
    from nexus.updates.verification import (
        validate_platform_report, validate_version_output,
    )
    # Verify from an isolated interpreter, not the checkout. No GUI/db starts.
    _run([str(python), "-I", "-m", "pip", "check"], timeout=30, cwd=home)
    verified = _run(
        [str(python), "-I", "-m", "nexus.main", "--version"],
        timeout=20, capture=True, cwd=home,
    )
    validate_version_output(verified.stdout, settings.version)
    platform = _run(
        [str(python), "-I", "-m", "nexus.main", "--platform-check"],
        timeout=20, capture=True, cwd=home,
    )
    validate_platform_report(platform.stdout)
    verify_local_postgresql(python, home)
    if not _existing_credentials():
        password = os.environ.get("NEXUS_DATABASE_PASSWORD")
        if password:
            _save_credentials(password, os.environ.get("NEXUS_DATABASE_NAME", "nexus"),
                              os.environ.get("NEXUS_DATABASE_USER", "nexus"))
    _switch_current(home, target)
    return home


def write_launcher(home: Path) -> Path:
    """Install a self-contained, private launcher with a pinned managed home."""
    from nexus.updates.manager import _private_directory
    _private_directory(home)
    bin_dir = Path.home() / ".local" / "bin"
    if bin_dir.is_symlink():
        raise RuntimeError("Diretório de executáveis não pode ser link simbólico.")
    bin_dir.mkdir(mode=0o700, parents=True, exist_ok=True)
    destination = bin_dir / "nexus-core"
    marker = "# NEXUS-CORE-MANAGED-LAUNCHER"
    if destination.is_symlink():
        raise RuntimeError("Não substituímos links simbólicos de executáveis.")
    if destination.exists() and marker not in destination.read_text(encoding="utf-8")[:250]:
        raise RuntimeError("Há outro executável nexus-core; não será substituído.")
    source = (ROOT / "nexus" / "updates" / "managed_entrypoint.py").read_text(
        encoding="utf-8"
    )
    if source.count("_INSTALL_HOME = None") != 1 or source.count("_CREDENTIALS_PATH = None") != 1 or marker not in source[:250]:
        raise RuntimeError("Modelo de inicialização não reconhecido.")
    content = source.replace(
        "_INSTALL_HOME = None", "_INSTALL_HOME = " + repr(str(home))
    ).replace(
        "_CREDENTIALS_PATH = None",
        "_CREDENTIALS_PATH = " + repr(str(_credentials_file())),
    )
    fd, name = tempfile.mkstemp(prefix=".nexus-launcher-", dir=bin_dir)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as stream:
            stream.write(content)
            stream.flush()
            os.fchmod(stream.fileno(), 0o700)
            os.fsync(stream.fileno())
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
        print("Instalação requer Ubuntu reconhecido e Python 3.12+; "
              "em outras distribuições use --check. Nada foi instalado.", file=sys.stderr)
        return 2
    print(f"NEXUS CORE — instalação guiada para Ubuntu {profile.release}.")
    if not install_system_packages():
        print("Instalação interrompida: requisitos do Ubuntu ainda ausentes.", file=sys.stderr)
        return 2
    if not provision_postgresql():
        print("Instalação interrompida: configure credenciais PostgreSQL locais "
              "e tente novamente.", file=sys.stderr)
        return 2
    # The user's PostgreSQL cluster may be stopped deliberately to conserve
    # RAM. Check it BEFORE downloading or preparing large local models.
    # Starting the cluster is explicit; no unit is enabled at boot.
    if not ensure_postgresql_running_for_install():
        print("Instalação adiada: PostgreSQL local precisa estar ativo para "
              "validar as credenciais; o ambiente anterior foi preservado.",
              file=sys.stderr)
        return 2
    if not prepare_local_models():
        print("Instalação interrompida: modelos locais de conversa e voz ainda ausentes.",
              file=sys.stderr)
        return 2
    try:
        home = install_managed_python()
        executable = write_launcher(home)
        recovery = write_recovery_launcher(home)
        female_voice = prepare_female_voice()
        neural_voice = prepare_neural_voice(home)
        from nexus.updates.manager import set_autoupdate
        enabled = confirm("Ativar verificação automática de releases estáveis?")
        set_autoupdate(enabled, home)
    except PostgreSQLAuthenticationError:
        print("Instalação interrompida: autenticação PostgreSQL local não confirmada. "
              "Revise usuário, senha, banco e serviço; a nova versão não foi ativada.",
              file=sys.stderr)
        return 2
    except (OSError, RuntimeError, subprocess.SubprocessError):
        print("Falha na instalação do ambiente Python do usuário.", file=sys.stderr)
        return 2
    print(f"Instalação concluída: {executable}")
    print(f"Recuperação offline instalada: {recovery}")
    print("Executar: ~/.local/bin/nexus-core")
    print("PostgreSQL: login local somente leitura confirmado antes da ativação.")
    print("Diagnóstico adicional: ~/.local/bin/nexus-core --ubuntu-preflight "
          "(sem teste físico de áudio, câmera ou inferência).")
    print("Atualizações automáticas: " + ("ativadas" if enabled else "desativadas"))
    print("Ollama e modelo de conversa encontrados; inferência real depende do teste local.")
    if not installed("docker"):
        print("Docker não detectado; recursos de sandbox exigem instalação/configuração independente.")
    print("Modelo Vosk em português encontrado. Permissões de áudio/câmera "
          "e operação física exigem teste no desktop.")
    if neural_voice:
        print("Voz masculina neural local pronta; voz feminina eSpeak NG disponível.")
    if female_voice:
        print("Voz feminina RHVoice Letícia pronta para seleção na janela.")
    print("Teste físico do microfone: ~/.local/bin/nexus-core --microphone-test")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
