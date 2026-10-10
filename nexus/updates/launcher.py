"""Pre-launch maintenance for the explicitly user-managed Linux installation.

Runs BEFORE loading the GUI/voice/database. Unavailable internet is harmless.
No sudo, no remote scripts, no installation into system Python.
"""
import os
import sys

from nexus.config.settings import settings
from .manager import (
    UpdateError, autoupdate_enabled, current_python,
    install_staged, managed_home, stage_latest,
)


def cli() -> None:
    home = managed_home()
    if autoupdate_enabled(home):
        running_version = settings.version
        try:
            # If offline, a previously verified staging area can still apply.
            installed = install_staged(home, current_version=running_version)
            if installed is not None:
                running_version = installed
        except (UpdateError, OSError) as exc:
            print("Nexus Core: atualização adiada; instalação anterior preservada.", file=sys.stderr)
        try:
            stage_latest(running_version, home)
            # The freshly staged release applies at the next launch, not now.
        except (UpdateError, OSError):
            pass
    try:
        python = current_python(home)
    except (UpdateError, OSError):
        print("Nexus Core: instalação gerenciada indisponível.", file=sys.stderr)
        raise SystemExit(2)
    # execv replaces this launcher; the running assistant is never hot patched.
    os.execv(str(python), [str(python), "-m", "nexus.main", *sys.argv[1:]])


if __name__ == "__main__":
    cli()
