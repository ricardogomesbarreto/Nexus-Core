"""Linux user installation / official stable update machinery for Nexus Core."""
from .manager import (
    UpdateError, autoupdate_enabled, current_python, install_staged,
    managed_home, pending_release, set_autoupdate, stage_latest,
)
from .releases import ReleaseWheel, latest_release, parse_release
from .watcher import AutoUpdateWatcher

__all__ = [
    "AutoUpdateWatcher", "ReleaseWheel", "UpdateError", "autoupdate_enabled",
    "current_python", "install_staged", "latest_release", "managed_home",
    "parse_release", "pending_release", "set_autoupdate", "stage_latest",
]
