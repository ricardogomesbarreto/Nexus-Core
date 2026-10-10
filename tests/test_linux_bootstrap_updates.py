"""v0.8.1 staged updates, atomic activation and offline fallback."""
import hashlib
import os
from pathlib import Path
import subprocess

import pytest

from nexus.updates import manager
from nexus.updates import launcher, watcher
from nexus.updates.releases import ReleaseWheel, UpdateError


WHEEL = b"stand-in wheel contents"
VER = "0.8.2"
NAME = f"nexus_core-{VER}-py3-none-any.whl"
SHA = hashlib.sha256(WHEEL).hexdigest()
URL = f"https://github.com/ricardogomesbarreto/Nexus-Core/releases/download/v{VER}/{NAME}"
RELEASE = ReleaseWheel(VER, NAME, URL, SHA, len(WHEEL))


def setup_home(tmp_path, monkeypatch):
    home = tmp_path / "managed"
    manager.set_autoupdate(True, home)
    monkeypatch.setattr(manager, "latest_release", lambda version: RELEASE)
    def download(release, directory):
        path = directory / release.filename
        path.write_bytes(WHEEL)
        return path
    monkeypatch.setattr(manager, "download_verified", download)
    return home


def test_disabled_means_no_network_and_no_update(tmp_path, monkeypatch):
    home = tmp_path / "managed"
    monkeypatch.setattr(manager, "latest_release", lambda _: pytest.fail("no network permitted"))
    assert manager.autoupdate_enabled(home) is False
    assert manager.stage_latest("0.8.1", home) is None
    assert manager.install_staged(home, current_version="0.8.1") is None


def test_opt_in_stage_is_private_and_verifiable(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    assert manager.stage_latest("0.8.1", home) == RELEASE
    assert manager.pending_release(home) == RELEASE
    assert (home / "downloads" / NAME).read_bytes() == WHEEL
    assert (home / "auto-update.enabled").stat().st_mode & 0o077 == 0
    assert (home / "staged-release.json").stat().st_mode & 0o077 == 0
    assert manager.stage_latest("0.8.1", home) == RELEASE
    assert len(list((home / "downloads").glob("*.whl"))) == 1


def test_tampered_or_symlinked_pending_files_fail_closed(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    manager.stage_latest("0.8.1", home)
    (home / "downloads" / NAME).write_bytes(b"tampered")
    assert manager.pending_release(home) is None
    (home / "staged-release.json").unlink()
    (home / "staged-release.json").symlink_to(tmp_path / "missing")
    assert manager.pending_release(home) is None


def test_user_can_disable_updates_without_changing_runtime(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    manager.set_autoupdate(False, home)
    assert not manager.autoupdate_enabled(home)
    monkeypatch.setattr(manager, "latest_release", lambda _: pytest.fail("should not connect"))
    assert manager.stage_latest("0.8.1", home) is None


def prepare_running_venv(home):
    versions = home / "versions"
    old = versions / "v0.8.1"
    (old / "bin").mkdir(parents=True)
    (old / "bin/python").write_text("old")
    (home / "current").symlink_to(old)
    return old


def fake_venv_create(target, **kw):
    (target / "bin").mkdir(parents=True)
    (target / "bin/python").write_text("new")


def test_new_version_is_installed_separately_and_switched_atomically(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    manager.stage_latest("0.8.1", home)
    old = prepare_running_venv(home)
    monkeypatch.setattr(manager.venv, "create", fake_venv_create)
    seen = []
    def run(cmd, **kw):
        seen.append(cmd)
        if "nexus.main" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"Nexus Core 0.8.2\n")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"")
    monkeypatch.setattr(manager.subprocess, "run", run)
    assert manager.install_staged(home, current_version="0.8.1") == VER
    assert (home / "current").resolve() == home / "versions" / "v0.8.2"
    assert (home / "previous").resolve() == old
    assert manager.pending_release(home) is None
    assert any("pip" in cmd for cmd in seen)
    assert any("nexus.main" in cmd for cmd in seen)


def test_failed_upgrade_keeps_old_installed(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    manager.stage_latest("0.8.1", home)
    old = prepare_running_venv(home)
    monkeypatch.setattr(manager.venv, "create", fake_venv_create)
    def fail(cmd, **kw):
        raise subprocess.CalledProcessError(1, cmd)
    monkeypatch.setattr(manager.subprocess, "run", fail)
    with pytest.raises(UpdateError, match="preservada"):
        manager.install_staged(home, current_version="0.8.1")
    assert (home / "current").resolve() == old
    assert not (home / "versions" / "v0.8.2").exists()


def test_false_package_version_blocks_atomic_switch(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    manager.stage_latest("0.8.1", home)
    old = prepare_running_venv(home)
    monkeypatch.setattr(manager.venv, "create", fake_venv_create)
    monkeypatch.setattr(manager.subprocess, "run",
                        lambda cmd, **kw: subprocess.CompletedProcess(
                            cmd, 0, stdout=b"Nexus Core 0.8.1\n"
                        ))
    with pytest.raises(UpdateError):
        manager.install_staged(home, current_version="0.8.1")
    assert (home / "current").resolve() == old


def test_foreign_current_symlink_is_rejected(tmp_path):
    home = tmp_path / "managed"
    home.mkdir()
    (home / "versions").mkdir()
    evil = tmp_path / "foreign"
    evil.mkdir()
    (home / "current").symlink_to(evil)
    with pytest.raises(UpdateError):
        manager.current_python(home)


def test_updater_worker_cannot_run_without_managed_launcher(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    monkeypatch.delenv("NEXUS_RUNNING_MANAGED", raising=False)
    monkeypatch.setattr(watcher, "managed_home", lambda: home)
    monkeypatch.setattr(watcher, "autoupdate_enabled", lambda h=None: True)
    worker = watcher.AutoUpdateWatcher("0.8.1")
    assert worker.start() is False
    assert worker._worker is None


def test_background_update_only_stages_and_never_installs(tmp_path, monkeypatch):
    home = setup_home(tmp_path, monkeypatch)
    monkeypatch.setattr(watcher, "managed_home", lambda: home)
    monkeypatch.setattr(watcher, "autoupdate_enabled", lambda h=None: True)
    monkeypatch.setattr(watcher, "stage_latest", lambda *args:
                        RELEASE)
    worker = watcher.AutoUpdateWatcher("0.8.1")
    assert worker.check_once() is True
    assert worker._worker is None


def test_managed_launcher_offline_uses_existing_python(tmp_path, monkeypatch):
    home = tmp_path / "managed"
    monkeypatch.setattr(launcher, "managed_home", lambda: home)
    monkeypatch.setattr(launcher, "autoupdate_enabled", lambda h: False)
    monkeypatch.setattr(launcher, "current_python", lambda h: Path("/bin/python3"))
    def execv(python, args):
        assert str(python) == "/bin/python3"
        assert args[-2:] == ["--version", "--desktop-check"]
        raise RuntimeError("exec checked")
    monkeypatch.setattr(launcher.os, "execv", execv)
    monkeypatch.setattr(launcher.sys, "argv", ["nexus-core", "--version", "--desktop-check"])
    with pytest.raises(RuntimeError, match="exec checked"):
        launcher.cli()


def test_untrusted_existing_system_launcher_is_never_overwritten(tmp_path, monkeypatch):
    from scripts import install_linux
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    destination = tmp_path / ".local/bin/nexus-core"
    destination.parent.mkdir(parents=True)
    destination.write_text("#!/bin/sh\necho unsafe\n")
    with pytest.raises(RuntimeError, match="outro executável"):
        install_linux.write_launcher(tmp_path / "managed")


def test_installer_never_prompts_in_unattended_mode(monkeypatch):
    from scripts import install_linux
    class Closed:
        def isatty(self):
            return False
    monkeypatch.setattr(install_linux.sys, "stdin", Closed())
    assert install_linux.confirm("Install with sudo?") is False
