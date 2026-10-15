"""v0.8.8: pinned standalone managed launcher and fail-closed version path."""
import json
import os
from pathlib import Path
import stat
import subprocess
import sys

import pytest

from nexus.updates import managed_entrypoint as entry
from nexus.updates import manager
from scripts import install_linux


def installed(tmp_path):
    home = tmp_path / "managed"
    versions = home / "versions"
    versions.mkdir(parents=True, mode=0o700)
    home.chmod(0o700)
    versions.chmod(0o700)
    current = versions / "v0.8.8"
    (current / "bin").mkdir(parents=True)
    current.chmod(0o700)
    python = current / "bin" / "python"
    python.write_text("#!/bin/sh\nexit 0\n")
    python.chmod(0o700)
    (home / "current").symlink_to(current)
    return home, current, python


def test_valid_runtime_is_owned_and_direct_version_slot(tmp_path):
    home, _, python = installed(tmp_path)
    assert entry.validate_current(home) == python


def test_launcher_records_pinned_home_before_exec_and_uses_isolated_python(
    tmp_path, monkeypatch
):
    home, _, python = installed(tmp_path)
    executed = []
    def fake_exec(path, args):
        executed.append((path, args))
    monkeypatch.delenv("NEXUS_DATABASE_PASSWORD", raising=False)
    monkeypatch.setenv("NEXUS_RUNNING_MANAGED", "0")
    monkeypatch.setenv("NEXUS_MANAGED_HOME", "not-in-use")
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "another-data-home"))
    entry.launch(["--version"], home=home, execv=fake_exec)
    assert executed == [(
        str(python),
        [str(python), "-I", "-m", "nexus.updates.launcher", "--version"],
    )]
    assert os.environ["NEXUS_MANAGED_HOME"] == str(home)
    assert os.environ["NEXUS_RUNNING_MANAGED"] == "1"
    assert manager.managed_home() == home


def test_managed_home_respects_xdg_for_unmanaged_process(tmp_path, monkeypatch):
    monkeypatch.delenv("NEXUS_RUNNING_MANAGED", raising=False)
    monkeypatch.setenv("NEXUS_MANAGED_HOME", str(tmp_path / "untrusted"))
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path / "other"))
    assert manager.managed_home() == tmp_path / "other/nexus-core/managed"


def test_invalid_environment_managed_home_is_rejected(tmp_path, monkeypatch):
    monkeypatch.setenv("NEXUS_RUNNING_MANAGED", "1")
    monkeypatch.setenv("NEXUS_MANAGED_HOME", "relative/path")
    with pytest.raises(manager.UpdateError):
        manager.managed_home()


@pytest.mark.parametrize("version", ["v0.8.8-extra", "anything", "v01.2.3"])
def test_launcher_denies_unrecognized_version_directory(tmp_path, version):
    home, current, python = installed(tmp_path)
    directory = current.parent / version
    current.rename(directory)
    (home / "current").unlink()
    (home / "current").symlink_to(directory)
    with pytest.raises(entry.LauncherError):
        entry.validate_current(home)


def test_launcher_rejects_external_current_symlink(tmp_path):
    home, _, _ = installed(tmp_path)
    other = tmp_path / "outside"
    (other / "bin").mkdir(parents=True)
    (other / "bin/python").write_text("outside")
    (home / "current").unlink()
    (home / "current").symlink_to(other)
    with pytest.raises(entry.LauncherError):
        entry.validate_current(home)


def test_launcher_rejects_private_python_symlink(tmp_path):
    home, _, python = installed(tmp_path)
    python.unlink()
    python.symlink_to("/bin/sh")
    with pytest.raises(entry.LauncherError):
        entry.validate_current(home)


def test_launcher_refuses_world_writable_executable(tmp_path):
    home, _, python = installed(tmp_path)
    python.chmod(0o777)
    with pytest.raises(entry.LauncherError):
        entry.validate_current(home)


def test_launcher_refuses_public_version_directory(tmp_path):
    home, current, _ = installed(tmp_path)
    current.chmod(0o755)
    with pytest.raises(entry.LauncherError):
        entry.validate_current(home)


def test_launcher_refuses_public_managed_home(tmp_path):
    home, _, _ = installed(tmp_path)
    home.chmod(0o755)
    with pytest.raises(entry.LauncherError):
        entry.validate_current(home)


def test_missing_runtime_denies_exec(tmp_path):
    home, _, python = installed(tmp_path)
    python.unlink()
    with pytest.raises(entry.LauncherError):
        entry.launch([], home=home, execv=lambda *args: pytest.fail("Must not exec"))


def test_unprovisioned_launcher_refuses_default(monkeypatch):
    monkeypatch.setattr(entry, "_INSTALL_HOME", None)
    with pytest.raises(entry.LauncherError, match="provisionado"):
        entry.launch(execv=lambda *args: pytest.fail("Must not exec"))


def test_password_is_only_loaded_from_private_bounded_regular_file(tmp_path):
    secret = tmp_path / "db_credentials.json"
    secret.write_text(json.dumps({"database_password": "dummy-testing-password"}))
    secret.chmod(0o600)
    assert entry.load_local_password(secret) == "dummy-testing-password"
    secret.chmod(0o644)
    assert entry.load_local_password(secret) is None
    secret.unlink()
    secret.symlink_to(tmp_path / "missing")
    assert entry.load_local_password(secret) is None
    secret.unlink()
    secret.write_text("x" * 5000)
    secret.chmod(0o600)
    assert entry.load_local_password(secret) is None


def test_launcher_loads_dedicated_postgresql_identity_from_private_file(
    tmp_path, monkeypatch,
):
    monkeypatch.setattr(entry.os, "geteuid", lambda: 1000)
    home, _, _ = installed(tmp_path)
    secret = tmp_path / "credentials.json"
    secret.write_text(json.dumps({
        "database_name": "nexus_core", "database_user": "nexus_core",
        "database_password": "private-test-password",
    }))
    secret.chmod(0o600)
    for key in ("NEXUS_DATABASE_PASSWORD", "NEXUS_DATABASE_NAME", "NEXUS_DATABASE_USER",
                "NEXUS_RUNNING_MANAGED", "NEXUS_MANAGED_HOME"):
        monkeypatch.setenv(key, "temporary-test-value")
        monkeypatch.delenv(key, raising=False)
    entry.launch([], home=home, credentials=secret, execv=lambda *args: None)
    assert os.environ["NEXUS_DATABASE_NAME"] == "nexus_core"
    assert os.environ["NEXUS_DATABASE_USER"] == "nexus_core"
    assert os.environ["NEXUS_DATABASE_PASSWORD"] == "private-test-password"


def test_launcher_rejects_public_or_malformed_database_identity(tmp_path):
    secret = tmp_path / "credentials.json"
    secret.write_text(json.dumps({
        "database_name": "nexus_core\nUNTRUSTED", "database_user": "nexus_core",
        "database_password": "private-test-password",
    }))
    secret.chmod(0o600)
    assert entry.load_local_database_config(secret) is None
    secret.write_text(json.dumps({"database_password": "private-test-password"}))
    secret.chmod(0o644)
    assert entry.load_local_database_config(secret) is None


def test_launch_keeps_user_supplied_password_untouched(tmp_path, monkeypatch):
    home, _, _ = installed(tmp_path)
    secret = tmp_path / "db_credentials.json"
    secret.write_text(json.dumps({"database_password": "local-password"}))
    secret.chmod(0o600)
    monkeypatch.setenv("NEXUS_DATABASE_PASSWORD", "already-configured")
    monkeypatch.setenv("NEXUS_RUNNING_MANAGED", "0")
    monkeypatch.setenv("NEXUS_MANAGED_HOME", "not-in-use")
    entry.launch([], home=home, credentials=secret, execv=lambda *a: None)
    assert os.environ["NEXUS_DATABASE_PASSWORD"] == "already-configured"


def test_installed_launcher_has_no_checkout_dependencies_and_honors_pinned_home(
    tmp_path, monkeypatch
):
    home, _, python = installed(tmp_path)
    # Test with an isolated plain executable impersonating the runtime only.
    python.write_text(
        '#!/bin/sh\nprintf "%s\\n" "$NEXUS_MANAGED_HOME" "$NEXUS_RUNNING_MANAGED" "$@"\n'
    )
    python.chmod(0o700)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    script = install_linux.write_launcher(home)
    content = script.read_text(encoding="utf-8")
    assert content.count("# NEXUS-CORE-MANAGED-LAUNCHER") >= 1
    assert content.startswith("#!/usr/bin/env python3")
    assert script.stat().st_mode & 0o077 == 0
    other = tmp_path / "other-xdg"
    result = subprocess.run(
        [sys.executable, str(script), "--platform-check"],
        cwd=tmp_path, env={
            "HOME": str(tmp_path), "PATH": os.environ.get("PATH", ""),
            "XDG_DATA_HOME": str(other),
        },
        capture_output=True, text=True, timeout=10, check=True,
    )
    data = result.stdout.splitlines()
    assert data == [
        str(home), "1", "-I", "-m", "nexus.updates.launcher", "--platform-check",
    ]
    assert not other.exists()


def test_installer_rejects_preexisting_unknown_launcher(tmp_path, monkeypatch):
    home, _, _ = installed(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    launcher = tmp_path / ".local/bin/nexus-core"
    launcher.parent.mkdir(parents=True)
    launcher.write_text("#!/bin/sh\necho other\n")
    with pytest.raises(RuntimeError, match="outro executável"):
        install_linux.write_launcher(home)
    assert "echo other" in launcher.read_text()


def test_installer_rejects_bin_directory_symlink(tmp_path, monkeypatch):
    home, _, _ = installed(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    other = tmp_path / "outside"
    other.mkdir()
    (tmp_path / ".local").mkdir()
    (tmp_path / ".local/bin").symlink_to(other)
    with pytest.raises(RuntimeError, match="link simbólico"):
        install_linux.write_launcher(home)
