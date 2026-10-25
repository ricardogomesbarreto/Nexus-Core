"""Stop only service instances that Nexus recorded when it started them.

The desktop uses this on exit, including the direct managed launcher path.
The session shell script uses the same private record for terminal sessions.
"""

import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import tempfile


_IDENTITY = re.compile(r"[0-9a-fA-F]{32}\Z")
_POSTGRES_UNIT = re.compile(r"postgresql@[0-9]+-[A-Za-z0-9_-]+\.service\Z")
_USER_OLLAMA = "nexus-core-ollama.service"
_SYSTEM_OLLAMA = "ollama.service"


def _record_path(*, create: bool = False) -> Path | None:
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    if not runtime:
        return None
    base = Path(runtime)
    try:
        status = base.lstat()
        if not base.is_dir() or base.is_symlink() or status.st_uid != os.getuid():
            return None
        directory = base / "nexus-core"
        if create and not directory.exists():
            directory.mkdir(mode=0o700)
        status = directory.lstat()
        if (not directory.is_dir() or directory.is_symlink()
                or status.st_uid != os.getuid() or status.st_mode & 0o777 != 0o700):
            return None
        path = directory / "started-services"
        if path.is_symlink():
            return None
        if path.exists():
            status = path.lstat()
            if (not path.is_file() or status.st_uid != os.getuid()
                    or status.st_mode & 0o777 != 0o600):
                return None
        return path
    except OSError:
        return None


def _allowed(scope: str, unit: str) -> bool:
    return ((scope == "user" and unit == _USER_OLLAMA)
            or (scope == "system" and (unit == _SYSTEM_OLLAMA
                                       or unit == "postgresql.service"
                                       or _POSTGRES_UNIT.fullmatch(unit) is not None)))


def _systemctl(scope: str, *args: str) -> subprocess.CompletedProcess:
    command = ["systemctl"] if scope == "system" else ["systemctl", "--user"]
    return subprocess.run([*command, *args], stdin=subprocess.DEVNULL,
                          stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                          text=True, timeout=15, check=False)


def _invocation(scope: str, unit: str) -> str:
    result = _systemctl(scope, "show", unit, "--property=InvocationID", "--value")
    value = result.stdout.strip() if result.returncode == 0 else ""
    return value if _IDENTITY.fullmatch(value) else ""


def record_started_service(scope: str, unit: str) -> bool:
    """Called only after a successful start of a previously inactive service."""
    if not _allowed(scope, unit):
        return False
    path = _record_path(create=True)
    if path is None:
        return False
    try:
        identity = _invocation(scope, unit)
        if not identity:
            return False
        flags = os.O_WRONLY | os.O_APPEND | os.O_CREAT | getattr(os, "O_NOFOLLOW", 0)
        descriptor = os.open(path, flags, 0o600)
        with os.fdopen(descriptor, "a", encoding="ascii") as stream:
            status = os.fstat(stream.fileno())
            if status.st_uid != os.getuid() or status.st_mode & 0o777 != 0o600:
                return False
            stream.write(f"{scope}\t{unit}\t{identity}\n")
        return True
    except (OSError, subprocess.TimeoutExpired):
        return False


def stop_owned_services() -> bool:
    """Noninteractive shutdown; retain failed entries for manual retry.

    Never stop an already running third-party service or a restarted instance.
    A missing sudo credential is reported promptly rather than hanging the GUI.
    """
    path = _record_path()
    if path is None or not path.exists():
        return True
    try:
        lines = path.read_text(encoding="ascii").splitlines()
    except (OSError, UnicodeError):
        print("[NEXUS] Registro privado de serviços ilegível; parada manual necessária.",
              file=sys.stderr)
        return False
    failed: list[str] = []
    # Stop the model first, then the database; retain original record order.
    for line in reversed(lines):
        parts = line.split("\t")
        if len(parts) != 3:
            continue
        scope, unit, identity = parts
        if not _allowed(scope, unit) or not _IDENTITY.fullmatch(identity):
            continue
        try:
            if _systemctl(scope, "is-active", "--quiet", unit).returncode != 0:
                continue
            if _invocation(scope, unit) != identity:
                continue
            command = (["sudo", "-n", "systemctl", "stop", unit]
                       if scope == "system" else ["systemctl", "--user", "stop", unit])
            result = subprocess.run(command, stdin=subprocess.DEVNULL,
                                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                                    timeout=25, check=False)
            # A graphical session can request system authentication if sudo's
            # cached credential has expired. No generic shell is invoked.
            if (result.returncode != 0 and scope == "system"
                    and (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY"))
                    and shutil.which("pkexec") and shutil.which("systemctl")):
                result = subprocess.run([shutil.which("pkexec"),
                                         shutil.which("systemctl"), "stop", unit],
                                        stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                        stderr=subprocess.DEVNULL, timeout=45, check=False)
            if result.returncode != 0:
                failed.append(line)
                print(f"[NEXUS] Não foi possível parar {unit} automaticamente; "
                      "use bash scripts/nexus_core_session.sh stop no terminal.", file=sys.stderr)
            else:
                print(f"[NEXUS] Serviço iniciado pelo Nexus encerrado: {unit}")
        except (OSError, subprocess.TimeoutExpired):
            failed.append(line)
            print(f"[NEXUS] Falha ao encerrar {unit}; tente a parada manual.", file=sys.stderr)
    try:
        if failed:
            descriptor, filename = tempfile.mkstemp(prefix=".remaining-", dir=path.parent)
            try:
                with os.fdopen(descriptor, "w", encoding="ascii") as stream:
                    os.fchmod(stream.fileno(), 0o600)
                    stream.write("\n".join(reversed(failed)) + "\n")
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(filename, path)
            finally:
                Path(filename).unlink(missing_ok=True)
        else:
            path.unlink(missing_ok=True)
    except OSError:
        print("[NEXUS] Falha ao atualizar registro de serviços; confira status manualmente.",
              file=sys.stderr)
        return False
    return not failed
