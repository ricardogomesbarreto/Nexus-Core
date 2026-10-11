"""v0.8.6: Linux flock maintenance coordination, no diagnostic side effects."""
import json
import os
from pathlib import Path
import subprocess

import pytest

from nexus.updates import launcher, manager, recovery
from nexus.updates.releases import ReleaseWheel, UpdateError
from scripts import install_linux


def managed(tmp_path):
    home = tmp_path / "managed"
    manager.set_autoupdate(True, home)
    return home


def installed(tmp_path):
    home = managed(tmp_path)
    versions = home / "versions"
    versions.mkdir(mode=0o700)
    current = versions / "v0.8.5"
    previous = versions / "v0.8.4"
    for dest in (current, previous):
        dest.mkdir(mode=0o700)
        (dest / "bin").mkdir(mode=0o700)
        binary = dest / "bin" / "python"
        binary.write_text("fake")
        binary.chmod(0o700)
    (home / "current").symlink_to(current)
    (home / "previous").symlink_to(previous)
    return home, current, previous


def fake_release():
    return ReleaseWheel(
        "0.8.6",
        "nexus_core-0.8.6-py3-none-any.whl",
        "https://github.com/ricardogomesbarreto/Nexus-Core/releases/download/v0.8.6/nexus_core-0.8.6-py3-none-any.whl",
        "0" * 64, 500,
    )


def test_kernel_lock_rejects_concurrent_same_user_maintenance(tmp_path):
    home = managed(tmp_path)
    with recovery.maintenance_lock(home):
        assert (home / ".maintenance.lock").stat().st_mode & 0o077 == 0
        with pytest.raises(recovery.RecoveryError, match="Outra manutenção"):
            with recovery.maintenance_lock(home):
                pytest.fail("Never permit two simultaneous changes")
    with recovery.maintenance_lock(home):
        pass  # kernel releases the lock even though the file persists


def test_lock_refuses_foreign_symlink(tmp_path):
    home = managed(tmp_path)
    outside = tmp_path / "private"
    outside.write_text("unchanged")
    (home / ".maintenance.lock").symlink_to(outside)
    with pytest.raises(recovery.RecoveryError):
        with recovery.maintenance_lock(home):
            pytest.fail("Do not follow an external lock symlink")
    assert outside.read_text() == "unchanged"


def test_lock_refuses_world_readable_or_wrong_file_type(tmp_path):
    home = managed(tmp_path)
    lock = home / ".maintenance.lock"
    lock.write_text("")
    lock.chmod(0o666)
    with pytest.raises(recovery.RecoveryError):
        with recovery.maintenance_lock(home):
            pytest.fail("World-readable lock should never be accepted")


def test_recovery_does_not_switch_while_updater_holds_lock(tmp_path):
    home, current, previous = installed(tmp_path)
    with recovery.maintenance_lock(home):
        with pytest.raises(recovery.RecoveryError, match="Outra manutenção"):
            recovery.rollback(home, tty=True, input_fn=lambda _: "REVERTER")
    assert (home / "current").resolve() == current
    assert (home / "previous").resolve() == previous
    assert manager.autoupdate_enabled(home) is True


def test_staging_does_not_write_while_recovery_holds_lock(tmp_path, monkeypatch):
    home, current, _ = installed(tmp_path)
    monkeypatch.setattr(manager, "latest_release", lambda _: fake_release())
    monkeypatch.setattr(manager, "download_verified",
                        lambda *a: pytest.fail("No download during lock"))
    with recovery.maintenance_lock(home):
        with pytest.raises(UpdateError, match="ocupada"):
            manager.stage_latest("0.8.5", home)
    assert not (home / "staged-release.json").exists()
    assert (home / "current").resolve() == current


def test_installer_cannot_enter_when_another_maintenance_is_active(tmp_path, monkeypatch):
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    home = manager._private_directory(manager.managed_home())
    monkeypatch.setattr(install_linux.venv, "create",
                        lambda *a, **kw: pytest.fail("No venv during maintenance"))
    with recovery.maintenance_lock(home):
        with pytest.raises(RuntimeError, match="manutenção"):
            install_linux.install_managed_python()
    assert not (home / "versions").exists()


def test_activation_refuses_second_maintainer_before_starting_pip(tmp_path, monkeypatch):
    home, current, _ = installed(tmp_path)
    monkeypatch.setattr(manager, "pending_release",
                        lambda _: pytest.fail("No marker read under lock"))
    with recovery.maintenance_lock(home):
        with pytest.raises(UpdateError, match="operação gerenciada"):
            manager.install_staged(home, current_version="0.8.5")
    assert (home / "current").resolve() == current


@pytest.mark.parametrize("argv", [
    ["--help"], ["-h"], ["--version"],
    ["--platform-check"], ["--desktop-check"], ["--vision-check"],
    ["--voice-check"], ["--ubuntu-doctor"], ["--ubuntu-preflight"],
    ["--devices-check"], ["--devices-preview-stdin"],
    ["--version", "--invalid-combination"],
])
def test_read_only_options_never_trigger_updates(argv):
    assert launcher.should_run_maintenance(argv) is False


def test_normal_desktop_launch_can_still_update():
    assert launcher.should_run_maintenance(["--desktop"]) is True
    assert launcher.should_run_maintenance([]) is True


def test_diagnostic_launcher_does_not_even_read_updater_preferences(tmp_path, monkeypatch):
    monkeypatch.setattr(launcher, "managed_home", lambda: tmp_path)
    monkeypatch.setattr(launcher, "autoupdate_enabled",
                        lambda h: pytest.fail("No maintenance for diagnosis"))
    monkeypatch.setattr(launcher, "current_python",
                        lambda h: Path("/usr/bin/python3"))
    monkeypatch.setattr(launcher.sys, "argv", ["nexus-core", "--platform-check"])
    monkeypatch.setattr(launcher.os, "execv",
                        lambda python, argv: (_ for _ in ()).throw(
                            RuntimeError(json.dumps(argv))
                        ))
    with pytest.raises(RuntimeError, match="--platform-check"):
        launcher.cli()


def test_explicit_disabling_prevents_followup_auto_update(tmp_path, monkeypatch):
    home, _, _ = installed(tmp_path)
    monkeypatch.setattr(manager, "latest_release", lambda _: fake_release())
    monkeypatch.setattr(manager, "download_verified",
                        lambda *a: pytest.fail("Must not download after disable"))
    manager.set_autoupdate(False, home)
    assert manager.stage_latest("0.8.5", home) is None
    assert manager.install_staged(home, current_version="0.8.5") is None
