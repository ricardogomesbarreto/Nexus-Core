"""v0.8.5: secure recovery works without the previously installed Nexus."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from nexus.updates import recovery
from scripts import install_linux


def make_install(tmp_path, with_previous=True):
    home = tmp_path / "managed"
    versions = home / "versions"
    versions.mkdir(parents=True)
    home.chmod(0o700)
    versions.chmod(0o700)
    current = versions / "v0.8.5"
    previous = versions / "v0.8.4"
    for folder in (current, previous):
        (folder / "bin").mkdir(parents=True)
        folder.chmod(0o700)
        executable = folder / "bin/python"
        executable.write_text("#!/bin/sh\nexit 0\n")
        executable.chmod(0o700)
    (home / "current").symlink_to(current)
    if with_previous:
        (home / "previous").symlink_to(previous)
    (home / "auto-update.enabled").write_text("1\n")
    (home / "auto-update.enabled").chmod(0o600)
    return home, current, previous


def test_status_is_private_without_operational_changes(tmp_path):
    home, current, previous = make_install(tmp_path)
    report = recovery.recovery_status(home)
    assert report == {
        "schema": "nexus.recovery.v1",
        "mode": "offline_read_only",
        "current": "v0.8.5",
        "previous": "v0.8.4",
        "rollback_available": True,
        "auto_updates_enabled": True,
        "database_modified": False,
        "process_restarted": False,
    }
    assert (home / "current").resolve() == current


def test_first_install_without_previous_does_not_allow_reversal(tmp_path):
    home, current, _ = make_install(tmp_path, with_previous=False)
    assert recovery.recovery_status(home)["rollback_available"] is False
    with pytest.raises(recovery.RecoveryError):
        recovery.rollback(home, tty=True, input_fn=lambda _: "REVERTER")
    assert (home / "current").resolve() == current


@pytest.mark.parametrize("response", ["", "sim", "Reverter", "AUTORIZO", "REVERTER TUDO"])
def test_confirmation_must_be_exact(tmp_path, response):
    home, current, _ = make_install(tmp_path)
    with pytest.raises(recovery.RecoveryError, match="não autorizada"):
        recovery.rollback(home, tty=True, input_fn=lambda _: response)
    assert (home / "current").resolve() == current
    assert (home / "auto-update.enabled").read_text() == "1\n"


def test_no_interactive_tty_no_switch(tmp_path):
    home, current, _ = make_install(tmp_path)
    with pytest.raises(recovery.RecoveryError, match="interativo"):
        recovery.rollback(
            home, tty=False,
            input_fn=lambda _: pytest.fail("No prompt without terminal"),
        )
    assert (home / "current").resolve() == current


def test_successful_rollback_is_offline_and_disables_reupdate(tmp_path, monkeypatch):
    home, current, previous = make_install(tmp_path)
    monkeypatch.setattr(recovery.subprocess if hasattr(recovery, "subprocess") else recovery, "unused", None, raising=False)
    result = recovery.rollback(home, tty=True, input_fn=lambda _: "REVERTER")
    assert result["current"] == "v0.8.4"
    assert result["previous"] == "v0.8.5"
    assert result["auto_updates_enabled"] is False
    assert result["database_modified"] is False
    assert (home / "current").resolve() == previous
    assert (home / "previous").resolve() == current
    assert (home / "auto-update.enabled").read_text() == "0\n"
    assert home.joinpath("auto-update.enabled").stat().st_mode & 0o077 == 0
    assert not list(home.glob(".*-recovery-next"))
    assert not list(home.glob(".recovery-option-*"))


def test_symlink_escape_never_selected_for_recovery(tmp_path):
    home, current, _ = make_install(tmp_path)
    external = tmp_path / "outside"
    (external / "bin").mkdir(parents=True)
    (external / "bin/python").write_text("evil")
    (home / "previous").unlink()
    (home / "previous").symlink_to(external)
    assert recovery.recovery_status(home)["rollback_available"] is False
    with pytest.raises(recovery.RecoveryError):
        recovery.rollback(home, tty=True, input_fn=lambda _: "REVERTER")
    assert (home / "current").resolve() == current


def test_untrusted_current_is_denied_before_consent(tmp_path):
    home, current, _ = make_install(tmp_path)
    (current / "bin/python").chmod(0o600)
    with pytest.raises(recovery.RecoveryError):
        recovery.rollback(home, tty=True, input_fn=lambda _: pytest.fail("No prompt"))
    assert (home / "auto-update.enabled").read_text() == "1\n"


def test_permission_unsafe_home_cannot_be_switched(tmp_path):
    home, _, _ = make_install(tmp_path)
    home.chmod(0o777)
    with pytest.raises(recovery.RecoveryError):
        recovery.recovery_status(home)
    with pytest.raises(recovery.RecoveryError):
        recovery.rollback(home, tty=True, input_fn=lambda _: "REVERTER")


def test_dangerous_preferences_symlink_is_rejected(tmp_path):
    home, current, _ = make_install(tmp_path)
    victim = tmp_path / "keep"
    victim.write_text("keep")
    (home / "auto-update.enabled").unlink()
    (home / "auto-update.enabled").symlink_to(victim)
    with pytest.raises(recovery.RecoveryError, match="insegura"):
        recovery.rollback(home, tty=True, input_fn=lambda _: "REVERTER")
    assert victim.read_text() == "keep"
    assert (home / "current").resolve() == current


def test_recover_launcher_is_self_contained_and_works_without_checkout(tmp_path, monkeypatch):
    home, current, _ = make_install(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    script = install_linux.write_recovery_launcher(home)
    assert script.name == "nexus-core-recover"
    assert script.stat().st_mode & stat.S_IXUSR
    assert "_INSTALL_HOME = " in script.read_text()
    completed = subprocess.run(
        [sys.executable, str(script), "--status"],
        cwd=tmp_path, env={"HOME": str(tmp_path), "PATH": os.environ.get("PATH", "")},
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=10,
        check=True,
    )
    assert json.loads(completed.stdout)["current"] == current.name
    assert "Traceback" not in completed.stderr


def test_unknown_recovery_binary_is_never_replaced(tmp_path, monkeypatch):
    home, _, _ = make_install(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    other = tmp_path / ".local/bin/nexus-core-recover"
    other.parent.mkdir(parents=True)
    other.write_text("untrusted")
    with pytest.raises(RuntimeError, match="desconhecido"):
        install_linux.write_recovery_launcher(home)
    assert other.read_text() == "untrusted"


def test_recovery_script_refuses_root_and_noninteractive_rollback(tmp_path, monkeypatch, capsys):
    home, _, _ = make_install(tmp_path)
    monkeypatch.setattr(recovery, "home_directory", lambda: home)
    monkeypatch.setattr(recovery.os, "geteuid", lambda: 0)
    assert recovery.cli(["--status"]) == 2
    assert "root" in capsys.readouterr().err


def test_no_database_or_application_imports_in_standalone_script():
    text = (install_linux.ROOT / "nexus/updates/recovery.py").read_text(encoding="utf-8")
    assert "from nexus" not in text
    assert "import psycopg" not in text
    assert "import requests" not in text
    assert "subprocess.run" not in text
    assert "os.execv" not in text
