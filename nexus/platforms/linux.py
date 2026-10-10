"""NEXUS CORE v0.8.2: passive desktop-Linux platform inventory.

Only Ubuntu 24.04 LTS is the current *installer* validation target.
Unknown distributions are reported but no package-manager action is inferred.
This module does not open hardware, connect to networks or start services.
"""
from dataclasses import dataclass
import importlib.util
import os
from pathlib import Path
import platform
import re
import shutil
import sys


SUPPORTED_UBUNTU = "24.04"
REQUIRED_BINARIES = (
    "psql", "pg_isready", "espeak-ng", "arecord", "ffmpeg",
)
OPTIONAL_BINARIES = (
    "xdotool", "ollama", "docker",
)
UBUNTU_PACKAGES = (
    "python3-venv", "python3-tk", "postgresql", "postgresql-client",
    "xdotool", "espeak-ng", "alsa-utils", "ffmpeg",
)


@dataclass(frozen=True)
class LinuxProfile:
    system: str
    distro: str
    release: str
    session: str
    installer_supported: bool

    @property
    def target(self) -> str:
        if self.installer_supported:
            return "ubuntu_24_04_lts"
        if self.system != "Linux":
            return "non_linux"
        if self.distro == "ubuntu":
            return "ubuntu_not_yet_validated"
        return "linux_other_distro_future"


def parse_os_release(text: str) -> tuple[str, str]:
    """Parse only ID and VERSION_ID from /etc/os-release; never eval shell."""
    if type(text) is not str or len(text) > 64_000:
        return "unknown", "unknown"
    found = {}
    for line in text.splitlines():
        if line.startswith("#") or "=" not in line:
            continue
        key, raw = line.split("=", 1)
        if key not in ("ID", "VERSION_ID") or key in found:
            continue
        value = raw.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in "'\"":
            value = value[1:-1]
        if not re.fullmatch(r"[A-Za-z0-9_.+-]{1,40}", value, re.ASCII):
            continue
        found[key] = value
    return found.get("ID", "unknown").lower(), found.get("VERSION_ID", "unknown")


def linux_profile(
    *, os_release: str | None = None,
    system: str | None = None,
    environment: dict | None = None,
) -> LinuxProfile:
    system = platform.system() if system is None else system
    if os_release is None:
        try:
            os_release = Path("/etc/os-release").read_text(encoding="utf-8")
        except (OSError, UnicodeError):
            os_release = ""
    distro, release = parse_os_release(os_release)
    env = os.environ if environment is None else environment
    session = str(env.get("XDG_SESSION_TYPE", "")).lower()
    if session not in ("x11", "wayland"):
        session = "unknown"
    supported = (
        system == "Linux" and distro == "ubuntu"
        and release == SUPPORTED_UBUNTU
        and sys.version_info >= (3, 12)
    )
    return LinuxProfile(system, distro, release, session, supported)


def platform_capabilities(
    *, profile: LinuxProfile | None = None,
    locate=None,
    tkinter_available: bool | None = None,
) -> dict:
    """Read-only capability snapshot; status is not a hardware health check."""
    profile = linux_profile() if profile is None else profile
    locate = shutil.which if locate is None else locate
    if tkinter_available is None:
        try:
            tkinter_available = importlib.util.find_spec("tkinter") is not None
        except (ImportError, ValueError):
            tkinter_available = False
    needed = {binary: bool(locate(binary)) for binary in REQUIRED_BINARIES}
    optional = {binary: bool(locate(binary)) for binary in OPTIONAL_BINARIES}
    missing = [name for name, available in needed.items() if not available]
    if not tkinter_available:
        missing.append("python3-tk")
    return {
        "mode": "passive",
        "target": profile.target,
        "system": profile.system,
        "distro": profile.distro,
        "version_id": profile.release,
        "session": profile.session,
        "installer_supported": profile.installer_supported,
        "python_supported": sys.version_info >= (3, 12),
        "required": needed,
        "optional": optional,
        "tkinter_available": bool(tkinter_available),
        "missing_required": missing,
        "desktop_gui_ready_to_try": bool(tkinter_available and profile.system == "Linux"),
        "x11_automation_ready_to_try": bool(
            optional["xdotool"] and profile.session == "x11"
            and profile.system == "Linux"
        ),
        "postgresql_service_tested": False,
        "microphone_tested": False,
        "camera_tested": False,
        "ollama_model_tested": False,
        "changes_performed": False,
        "notes": (
            "Ubuntu 24.04 LTS é o alvo de instalação; outras distros somente "
            "diagnóstico nesta fase. A interface Tk pode funcionar em Wayland, "
            "mas automação de teclado por xdotool exige sessão X11 local."
        ),
    }
