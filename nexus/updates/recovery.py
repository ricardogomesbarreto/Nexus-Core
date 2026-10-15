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


def _activation_intent(home: Path) -> dict | None:
    """Read a bounded, private, strict journal without following symlinks."""
    marker = home / ".activation-intent.json"
    if not marker.is_symlink() and not marker.exists():
        return None
    if marker.is_symlink() or not marker.is_file():
        raise RecoveryError("Registro de ativação inválido.")
    mode = marker.stat()
    if (mode.st_uid != os.getuid() or mode.st_nlink != 1
            or mode.st_mode & 0o077 or mode.st_size > 2048):
        raise RecoveryError("Registro de ativação inseguro.")
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
    except (OSError, ValueError, UnicodeError) as exc:
        raise RecoveryError("Registro de ativação ilegível.") from exc
    if type(data) is not dict or set(data) != {
        "schema", "from", "to", "previous_before",
    } or data["schema"] != "nexus.activation-intent.v1":
        raise RecoveryError("Formato do registro de ativação inválido.")
    if (type(data["from"]) is not str or VERSION.fullmatch(data["from"]) is None
            or type(data["to"]) is not str or VERSION.fullmatch(data["to"]) is None
            or data["from"] == data["to"]
            or (data["previous_before"] is not None
                and (type(data["previous_before"]) is not str
                     or VERSION.fullmatch(data["previous_before"]) is None))):
        raise RecoveryError("Referências de versão inválidas.")
    return data


def activation_status(home: Path | None = None) -> dict:
    """Report whether a local activation is pending; never alter files."""
    home = home_directory() if home is None else Path(home)
    _owned_private_directory(home)
    try:
        data = _activation_intent(home)
        state = "interrupted" if data is not None else "clear"
    except RecoveryError:
        state = "invalid_record"
    return {
        "schema": "nexus.activation-repair.v1",
        "status": state,
        "repair_requires_confirmation": state != "clear",
        "database_modified": False,
        "external_network_used": False,
        "automatic_repair_performed": False,
    }


def _verified_version(home: Path, name: str) -> Path:
    """Validate only owned direct version folders with a viable runtime."""
    versions = home / "versions"
    _owned_private_directory(versions)
    if VERSION.fullmatch(name) is None:
        raise RecoveryError("Versão inválida para reparo.")
    folder = versions / name
    if folder.is_symlink() or not folder.is_dir():
        raise RecoveryError("Versão referenciada não está instalada.")
    meta = folder.stat()
    if meta.st_uid != os.getuid() or meta.st_mode & 0o022:
        raise RecoveryError("Versão referenciada insegura.")
    executable = folder / "bin/python"
    if executable.is_symlink() or not executable.is_file():
        raise RecoveryError("Python da versão inválido.")
    meta = executable.stat()
    if meta.st_uid != os.getuid() or not meta.st_mode & stat.S_IXUSR:
        raise RecoveryError("Python da versão inseguro.")
    return folder


def _repair_activation_locked(home: Path) -> dict:
    """Safely reconcile previous with current under the exclusive lock."""
    _owned_private_directory(home)
    record = _activation_intent(home)
    if record is None:
        raise RecoveryError("Nenhuma ativação interrompida para reparar.")
    before = _verified_version(home, record["from"])
    previous_before = (
        _verified_version(home, record["previous_before"])
        if record["previous_before"] is not None else None
    )
    current = _version_slot(home, "current")
    if current.name not in (record["from"], record["to"]):
        raise RecoveryError("Versão atual diverge do registro.")
    if current.name == record["to"]:
        _verified_version(home, record["to"])
    # An unknown previous reference must never be overwritten silently.
    previous_link = home / "previous"
    if previous_link.is_symlink():
        old_previous = _version_slot(home, "previous")
        allowed = {record["from"], record["previous_before"]}
        if old_previous.name not in allowed:
            raise RecoveryError("Versão anterior inesperada; revisão manual.")
    elif previous_link.exists():
        raise RecoveryError("Referência anterior inválida.")
    for name in ("previous", "current"):
        temp = home / ("." + name + "-recovery-next")
        if temp.exists() or temp.is_symlink():
            raise RecoveryError("Outra recuperação encontra-se em andamento.")
    # Preserve operator intent: the repair does not switch current. If current
    # is already new, finish the previous pointer. If still old, undo the
    # partial previous pointer update and keep the old runtime selected.
    desired_previous = before if current.name == record["to"] else previous_before
    if desired_previous is None:
        previous_link.unlink(missing_ok=True)
    elif not previous_link.is_symlink() or previous_link.resolve(strict=True) != desired_previous:
        _safe_replace_link(home, "previous", desired_previous)
    (home / ".activation-intent.json").unlink()
    return {
        "schema": "nexus.activation-repair.v1",
        "result": "reconciled",
        "current": current.name,
        "previous": desired_previous.name if desired_previous else None,
        "auto_updates_enabled": False,
        "database_modified": False,
        "external_network_used": False,
        "process_restarted": False,
    }


def repair_activation(home: Path | None = None, *, input_fn=input, tty=None) -> dict:
    """Require a human's terminal consent before any repair or preference edit."""
    home = home_directory() if home is None else Path(home)
    status = activation_status(home)
    if status["status"] != "interrupted":
        raise RecoveryError("Nenhum registro reparável disponível.")
    if tty is None:
        tty = sys.stdin.isatty()
    if not tty:
        raise RecoveryError("Reparo requer terminal interativo.")
    try:
        answer = input_fn(
            "Reparar somente os links do programa, sem restaurar banco de "
            "dados? Digite REPARAR para autorizar: "
        )
    except (EOFError, KeyboardInterrupt) as exc:
        raise RecoveryError("Reparo não autorizado.") from exc
    if answer.strip() != "REPARAR":
        raise RecoveryError("Reparo não autorizado.")
    with maintenance_lock(home):
        # Prevent applying a staged release immediately after repair.
        # The installer/updater and repair all share the same flock.
        _disable_updates(home)
        return _repair_activation_locked(home)


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
    group.add_argument("--activation-status", action="store_true", help="consulta registro de ativação sem alterar nada")
    group.add_argument("--rollback", action="store_true", help="reverte somente a versão executável")
    group.add_argument("--repair-activation", action="store_true", help="repara uma ativação interrompida com confirmação")
    args = parser.parse_args(argv)
    if os.geteuid() == 0:
        print("Não execute a recuperação como root.", file=sys.stderr)
        return 2
    try:
        if args.repair_activation:
            output = repair_activation()
        elif args.activation_status:
            output = activation_status()
        elif args.rollback:
            output = rollback()
        else:
            output = recovery_status()
    except (RecoveryError, OSError, RuntimeError):
        print("Instalação inválida ou operação não autorizada; nenhuma aprovação presumida.", file=sys.stderr)
        return 2
    print(json.dumps(output, ensure_ascii=False, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(cli())
