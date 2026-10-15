#!/usr/bin/env python3
# NEXUS-CORE-MANAGED-LAUNCHER
"""Standalone, user-scoped entry point; never imports a candidate Nexus venv.

The installer embeds immutable installation paths into a user-private copy.
This is Ubuntu-first (system python3); it cannot elevate privileges or
repair an already missing current runtime. Use nexus-core-recover instead.
"""
import json
import os
from pathlib import Path
import re
import stat
import sys

_INSTALL_HOME = None
_CREDENTIALS_PATH = None
_VERSION = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$", re.ASCII)


class LauncherError(ValueError):
    """Safe error which must not include paths, passwords or environment."""


def _private_folder(folder: Path) -> None:
    if folder.is_symlink() or not folder.is_dir():
        raise LauncherError("Diretório privado da instalação inválido.")
    info = folder.stat()
    if info.st_uid != os.getuid() or info.st_mode & 0o077:
        raise LauncherError("Diretório da instalação sem permissões privadas.")


def validate_current(home: Path) -> Path:
    """Resolve only an owned non-symlink executable in a direct version slot."""
    _private_folder(home)
    marker = home / ".activation-intent.json"
    if marker.is_symlink() or marker.exists():
        raise LauncherError(
            "Ativação interrompida; consulte nexus-core-recover --activation-status."
        )
    versions = home / "versions"
    _private_folder(versions)
    current = home / "current"
    if not current.is_symlink():
        raise LauncherError("Instalação gerenciada sem versão ativa.")
    try:
        target = current.resolve(strict=True)
        root = versions.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise LauncherError("Versão ativa inacessível.") from exc
    if target.parent != root or _VERSION.fullmatch(target.name) is None:
        raise LauncherError("Versão ativa não pertence à instalação.")
    _private_folder(target)
    executable = target / "bin" / "python"
    if executable.is_symlink() or not executable.is_file():
        raise LauncherError("Python ativo inválido.")
    info = executable.stat()
    if (info.st_uid != os.getuid() or info.st_mode & 0o022
            or not info.st_mode & stat.S_IXUSR):
        raise LauncherError("Executável ativo inseguro.")
    return executable


def load_local_password(credentials: Path | None) -> str | None:
    """Read only one small owner-private credential file; never print it."""
    if credentials is None or credentials.is_symlink() or not credentials.is_file():
        return None
    if credentials.parent.is_symlink():
        return None
    try:
        data = credentials.stat()
        if (data.st_uid != os.getuid() or data.st_mode & 0o077
                or data.st_size > 4096):
            return None
        payload = json.loads(credentials.read_text(encoding="utf-8"))
        if type(payload) is dict and type(payload.get("database_password")) is str:
            password = payload["database_password"]
            if 0 < len(password) <= 1024:
                return password
    except (OSError, ValueError, UnicodeError):
        pass
    return None


def launch(argv=None, *, home=None, credentials=None, execv=None) -> None:
    """Select the pinned managed runtime; never follow arbitrary current links."""
    if os.geteuid() == 0:
        raise LauncherError("Não executar o assistente gerenciado como root.")
    home = Path(_INSTALL_HOME) if home is None and _INSTALL_HOME is not None else home
    if home is None:
        raise LauncherError("Inicializador não provisionado pelo instalador.")
    home = Path(home)
    if not home.is_absolute():
        raise LauncherError("Instalação gerenciada deve ter caminho absoluto.")
    python = validate_current(home)
    secret = (Path(_CREDENTIALS_PATH) if credentials is None
              and _CREDENTIALS_PATH is not None else credentials)
    password = load_local_password(Path(secret)) if secret is not None else None
    if password is not None:
        os.environ.setdefault("NEXUS_DATABASE_PASSWORD", password)
    os.environ["NEXUS_RUNNING_MANAGED"] = "1"
    os.environ["NEXUS_MANAGED_HOME"] = str(home)
    args = sys.argv[1:] if argv is None else list(argv)
    executor = os.execv if execv is None else execv
    executor(str(python), [str(python), "-I", "-m", "nexus.updates.launcher", *args])


def cli() -> int:
    try:
        launch()
    except (LauncherError, OSError, RuntimeError):
        print(
            "NEXUS CORE: instalação local inválida; use nexus-core-recover --status.",
            file=sys.stderr,
        )
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
