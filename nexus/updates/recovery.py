#!/usr/bin/env python3
"""Standalone Ubuntu recovery entry point for a managed Nexus Core install.

This file is stdlib-only by design. Installer copies the complete file to
~/.local/bin/nexus-core-recover, with a pinned managed home, so recovery
works even if current/bin/python or the Nexus package is broken.

Rollback is interactive and opt-in. It affects executable selection only:
NO database schema rollback, files deleted, process restart or downloads.
"""
import argparse
from contextlib import contextmanager
import fcntl
import json
import os
from pathlib import Path
import re
import stat
import sys
import tempfile


_INSTALL_HOME = None
VERSION = re.compile(r"^v(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)$", re.ASCII)


class RecoveryError(ValueError):
    """A sanitized error: never reveal home paths or secrets."""


def home_directory() -> Path:
    if _INSTALL_HOME is not None:
        return Path(_INSTALL_HOME)
    root = os.environ.get("XDG_DATA_HOME")
    base = (Path(root).expanduser()
            if root and Path(root).is_absolute()
            else Path.home() / ".local" / "share")
    return base / "nexus-core" / "managed"


def _owned_private_directory(path: Path) -> None:
    if path.is_symlink() or not path.is_dir():
        raise RecoveryError("Diretório gerenciado inválido.")
    try:
        mode = path.stat()
    except OSError as exc:
        raise RecoveryError("Diretório inacessível.") from exc
    if mode.st_uid != os.getuid() or (mode.st_mode & 0o077):
        raise RecoveryError("Diretório gerenciado deve pertencer ao usuário e ser privado.")


@contextmanager
def maintenance_lock(home: Path):
    """Non-blocking per-installation Linux flock, shared with the updater.

    A persistent lock file is expected; the kernel releases ownership if
    the process crashes. Never wait while a second process changes versions.
    """
    _owned_private_directory(home)
    flags = os.O_RDWR | os.O_CREAT | os.O_CLOEXEC | os.O_NOFOLLOW
    fd = None
    try:
        fd = os.open(home / ".maintenance.lock", flags, 0o600)
        info = os.fstat(fd)
        if (not stat.S_ISREG(info.st_mode) or info.st_uid != os.getuid()
                or info.st_nlink != 1 or info.st_mode & 0o077):
            raise RecoveryError("Arquivo de bloqueio não confiável.")
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except (BlockingIOError, InterruptedError) as exc:
            raise RecoveryError("Outra manutenção do NEXUS CORE está em execução.") from exc
        yield
    except OSError as exc:
        raise RecoveryError("Não foi possível proteger a instalação.") from exc
    finally:
        if fd is not None:
            os.close(fd)


def _version_slot(home: Path, name: str) -> Path:
    """Resolve a symlink to an owned, direct child of versions/ only."""
    versions = home / "versions"
    _owned_private_directory(versions)
    slot = home / name
    if not slot.is_symlink():
        raise RecoveryError("Versão gerenciada não encontrada.")
    try:
        target = slot.resolve(strict=True)
        version_root = versions.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise RecoveryError("Referência de versão inválida.") from exc
    if target.parent != version_root or VERSION.fullmatch(target.name) is None:
        raise RecoveryError("Referência fora do conjunto de versões autorizado.")
    if target.is_symlink() or not target.is_dir():
        raise RecoveryError("Diretório de versão inválido.")
    mode = target.stat()
    if mode.st_uid != os.getuid() or (mode.st_mode & 0o022):
        raise RecoveryError("Versão instalada não pertence ao usuário.")
    executable = target / "bin" / "python"
    if executable.is_symlink() or not executable.is_file():
        raise RecoveryError("Executável da versão não verificado.")
    meta = executable.stat()
    if meta.st_uid != os.getuid() or not (meta.st_mode & stat.S_IXUSR):
        raise RecoveryError("Executável da versão é inválido.")
    return target


def recovery_status(home: Path | None = None) -> dict:
    home = home_directory() if home is None else Path(home)
    _owned_private_directory(home)
    current = _version_slot(home, "current")
    previous = None
    try:
        previous = _version_slot(home, "previous")
    except RecoveryError:
        pass
    option = home / "auto-update.enabled"
    auto = False
    if not option.is_symlink() and option.is_file():
        try:
            auto = option.read_text(encoding="ascii").strip() == "1"
        except (OSError, UnicodeError):
            auto = False
    return {
        "schema": "nexus.recovery.v1",
        "mode": "offline_read_only",
        "current": current.name,
        "previous": previous.name if previous is not None else None,
        "rollback_available": previous is not None and previous != current,
        "auto_updates_enabled": auto,
        "database_modified": False,
        "process_restarted": False,
    }


def _safe_replace_link(home: Path, name: str, target: Path) -> None:
    temporary = home / ("." + name + "-recovery-next")
    if temporary.exists() or temporary.is_symlink():
        raise RecoveryError("Outra operação de recuperação está em andamento.")
    try:
        temporary.symlink_to(target)
        os.replace(temporary, home / name)
    finally:
        temporary.unlink(missing_ok=True)


def _disable_updates(home: Path) -> None:
    setting = home / "auto-update.enabled"
    if setting.is_symlink():
        raise RecoveryError("Configuração de atualização insegura.")
    fd, name = tempfile.mkstemp(prefix=".recovery-option-", dir=home)
    path = Path(name)
    try:
        with os.fdopen(fd, "w", encoding="ascii") as handle:
            os.fchmod(handle.fileno(), 0o600)
            handle.write("0\n")
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(path, setting)
    finally:
        path.unlink(missing_ok=True)


def rollback(home: Path | None = None, *, input_fn=input, tty=None) -> dict:
    """Switch executable symlinks without importing or executing either venv."""
    home = home_directory() if home is None else Path(home)
    status = recovery_status(home)
    if not status["rollback_available"]:
        raise RecoveryError("Nenhuma versão anterior válida disponível.")
    if tty is None:
        tty = sys.stdin.isatty()
    if not tty:
        raise RecoveryError("Recuperação exige terminal interativo.")
    try:
        answer = input_fn(
            "Apenas a instalação Python será revertida; banco de dados não será "
            "alterado. Digite REVERTER para confirmar: "
        )
    except (EOFError, KeyboardInterrupt) as exc:
        raise RecoveryError("Operação não autorizada.") from exc
    if answer.strip() != "REVERTER":
        raise RecoveryError("Operação não autorizada.")

    with maintenance_lock(home):
        return _rollback_locked(home)


def _rollback_locked(home: Path) -> dict:
    """Revalidate target links *after* gaining the exclusive lock."""
    _owned_private_directory(home)
    old = _version_slot(home, "current")
    previous = _version_slot(home, "previous")
    if previous == old:
        raise RecoveryError("Referências de versão inconsistentes.")
    if (home / ".current-recovery-next").exists() or (home / ".current-recovery-next").is_symlink():
        raise RecoveryError("Outra operação de recuperação está em andamento.")
    if (home / ".previous-recovery-next").exists() or (home / ".previous-recovery-next").is_symlink():
        raise RecoveryError("Outra operação de recuperação está em andamento.")

    # First prevent the automatic updater from immediately reapplying a
    # previously prepared release. No network activity is performed.
    _disable_updates(home)
    _safe_replace_link(home, "current", previous)
    _safe_replace_link(home, "previous", old)
    result = recovery_status(home)
    return {
        "schema": "nexus.recovery.v1",
        "result": "rolled_back",
        "current": result["current"],
        "previous": result["previous"],
        "auto_updates_enabled": result["auto_updates_enabled"],
        "database_modified": False,
        "process_restarted": False,
    }


def cli(argv=None) -> int:
    parser = argparse.ArgumentParser(
        prog="nexus-core-recover",
        description="Recuperação offline e controlada de instalação NEXUS CORE",
    )
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--status", action="store_true", help="consulta somente leitura")
    group.add_argument("--rollback", action="store_true", help="reverte somente a versão executável")
    args = parser.parse_args(argv)
    if os.geteuid() == 0:
        print("Não execute a recuperação como root.", file=sys.stderr)
        return 2
    try:
        output = rollback() if args.rollback else recovery_status()
    except (RecoveryError, OSError, RuntimeError):
        print("Instalação inválida ou operação não autorizada; nenhuma aprovação presumida.", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
