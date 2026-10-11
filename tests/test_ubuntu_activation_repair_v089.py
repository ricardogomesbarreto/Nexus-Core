"""v0.8.9 — Safe offline repair of interrupted Ubuntu activation."""
import json
import os
from pathlib import Path

import pytest

from nexus.updates import manager, recovery, managed_entrypoint
from scripts import install_linux


def setup_home(tmp_path, *, prior=True):
    home = tmp_path / "managed"
    versions = home / "versions"
    versions.mkdir(parents=True)
    home.chmod(0o700)
    versions.chmod(0o700)
    folders = {}
    for name in ("v0.8.6", "v0.8.7", "v0.8.9"):
        folder = versions / name
        (folder / "bin").mkdir(parents=True)
        folder.chmod(0o700)
        exe = folder / "bin/python"
        exe.write_text("#!/bin/sh\nexit 0\n")
        exe.chmod(0o700)
        folders[name] = folder
    (home / "current").symlink_to(folders["v0.8.7"])
    if prior:
        (home / "previous").symlink_to(folders["v0.8.6"])
    (home / "auto-update.enabled").write_text("1\n")
    (home / "auto-update.enabled").chmod(0o600)
    return home, folders


def interrupt_before_current(tmp_path, monkeypatch, *, prior=True):
    home, dirs = setup_home(tmp_path, prior=prior)
    original = manager.os.replace

    def fail_current(src, dst):
        if Path(dst) == home / "current":
            raise OSError("simulated process crash")
        return original(src, dst)

    monkeypatch.setattr(manager.os, "replace", fail_current)
    with pytest.raises(OSError, match="simulated"):
        manager._switch_current(home, dirs["v0.8.9"])
    monkeypatch.setattr(manager.os, "replace", original)
    return home, dirs


def test_completed_activation_has_no_orphan_journal(tmp_path):
    home, dirs = setup_home(tmp_path)
    manager._switch_current(home, dirs["v0.8.9"])
    assert (home / "current").resolve() == dirs["v0.8.9"]
    assert (home / "previous").resolve() == dirs["v0.8.7"]
    assert recovery.activation_status(home)["status"] == "clear"
    assert not (home / ".activation-intent.json").exists()


def test_current_switch_failure_records_valid_private_intent(tmp_path, monkeypatch):
    home, dirs = interrupt_before_current(tmp_path, monkeypatch)
    intent = home / ".activation-intent.json"
    document = json.loads(intent.read_text())
    assert document == {
        "schema": "nexus.activation-intent.v1",
        "from": "v0.8.7",
        "to": "v0.8.9",
        "previous_before": "v0.8.6",
    }
    assert intent.stat().st_mode & 0o077 == 0
    assert (home / "current").resolve() == dirs["v0.8.7"]
    assert (home / "previous").resolve() == dirs["v0.8.7"]
    assert recovery.activation_status(home)["status"] == "interrupted"


def test_offline_repair_restores_previous_when_switch_did_not_complete(
    tmp_path, monkeypatch
):
    home, dirs = interrupt_before_current(tmp_path, monkeypatch)
    result = recovery.repair_activation(
        home, tty=True, input_fn=lambda _: "REPARAR"
    )
    assert result["result"] == "reconciled"
    assert result["current"] == "v0.8.7"
    assert result["previous"] == "v0.8.6"
    assert result["auto_updates_enabled"] is False
    assert result["database_modified"] is False
    assert (home / "current").resolve() == dirs["v0.8.7"]
    assert (home / "previous").resolve() == dirs["v0.8.6"]
    assert (home / "auto-update.enabled").read_text() == "0\n"
    assert recovery.activation_status(home)["status"] == "clear"


def test_repair_without_earlier_previous_unlinks_partial_link(
    tmp_path, monkeypatch
):
    home, dirs = interrupt_before_current(tmp_path, monkeypatch, prior=False)
    assert (home / "previous").is_symlink()
    result = recovery.repair_activation(
        home, tty=True, input_fn=lambda _: "REPARAR"
    )
    assert result["previous"] is None
    assert not (home / "previous").exists()
    assert (home / "current").resolve() == dirs["v0.8.7"]


def test_activation_after_current_switch_but_before_journal_cleanup(
    tmp_path, monkeypatch,
):
    home, dirs = setup_home(tmp_path)
    marker = home / ".activation-intent.json"
    old_unlink = Path.unlink

    def fail_cleanup(self, *args, **kwargs):
        if self == marker:
            raise OSError("simulated power loss after current switch")
        return old_unlink(self, *args, **kwargs)

    monkeypatch.setattr(Path, "unlink", fail_cleanup)
    with pytest.raises(OSError, match="simulated power"):
        manager._switch_current(home, dirs["v0.8.9"])
    monkeypatch.setattr(Path, "unlink", old_unlink)
    assert (home / "current").resolve() == dirs["v0.8.9"]
    assert (home / "previous").resolve() == dirs["v0.8.7"]
    result = recovery.repair_activation(
        home, tty=True, input_fn=lambda _: "REPARAR"
    )
    assert result["current"] == "v0.8.9"
    assert result["previous"] == "v0.8.7"
    assert recovery.activation_status(home)["status"] == "clear"


@pytest.mark.parametrize("response", ["", "sim", "REVERTER", "reparar", "REPARAR TUDO"])
def test_repair_requires_exact_confirmation(tmp_path, monkeypatch, response):
    home, dirs = interrupt_before_current(tmp_path, monkeypatch)
    with pytest.raises(recovery.RecoveryError, match="autorizado"):
        recovery.repair_activation(
            home, tty=True, input_fn=lambda _: response
        )
    assert (home / ".activation-intent.json").exists()
    assert (home / "auto-update.enabled").read_text() == "1\n"
    assert (home / "current").resolve() == dirs["v0.8.7"]


def test_repair_without_tty_is_non_mutating(tmp_path, monkeypatch):
    home, _ = interrupt_before_current(tmp_path, monkeypatch)
    with pytest.raises(recovery.RecoveryError, match="interativo"):
        recovery.repair_activation(
            home, tty=False,
            input_fn=lambda _: pytest.fail("Never ask without TTY"),
        )
    assert (home / "auto-update.enabled").read_text() == "1\n"
    assert (home / ".activation-intent.json").is_file()


def test_launcher_and_update_refuse_incomplete_activation(tmp_path, monkeypatch):
    home, _ = interrupt_before_current(tmp_path, monkeypatch)
    with pytest.raises(managed_entrypoint.LauncherError, match="interrompida"):
        managed_entrypoint.validate_current(home)
    with pytest.raises(manager.UpdateError, match="reparo"):
        manager._checked_current(home)
    with pytest.raises(manager.UpdateError):
        manager._switch_current(home, home / "versions" / "v0.8.9")


@pytest.mark.parametrize("tamper", [
    {"from": "../escape"},
    {"to": "/tmp/external"},
    {"previous_before": "v0.8.7;bad"},
    {"schema": "unrecognized"},
    {"from": "v0.8.9"},
])
def test_forged_activation_journal_denied(tmp_path, monkeypatch, tamper):
    home, dirs = interrupt_before_current(tmp_path, monkeypatch)
    marker = home / ".activation-intent.json"
    payload = json.loads(marker.read_text())
    payload.update(tamper)
    marker.write_text(json.dumps(payload))
    assert recovery.activation_status(home)["status"] == "invalid_record"
    with pytest.raises(recovery.RecoveryError):
        recovery.repair_activation(home, tty=True, input_fn=lambda _: "REPARAR")
    assert (home / "auto-update.enabled").read_text() == "1\n"
    assert (home / "current").resolve() == dirs["v0.8.7"]


def test_symlinked_or_world_readable_journal_is_not_accepted(tmp_path):
    home, _ = setup_home(tmp_path)
    marker = home / ".activation-intent.json"
    external = tmp_path / "external"
    external.write_text("{}")
    marker.symlink_to(external)
    assert recovery.activation_status(home)["status"] == "invalid_record"
    assert external.read_text() == "{}"
    marker.unlink()
    marker.write_text(json.dumps({
        "schema": "nexus.activation-intent.v1",
        "from": "v0.8.7", "to": "v0.8.9", "previous_before": None,
    }))
    marker.chmod(0o644)
    assert recovery.activation_status(home)["status"] == "invalid_record"


def test_repair_refuses_unknown_prior_pointer(tmp_path, monkeypatch):
    home, dirs = interrupt_before_current(tmp_path, monkeypatch)
    (home / "previous").unlink()
    (home / "previous").symlink_to(dirs["v0.8.9"])
    with pytest.raises(recovery.RecoveryError, match="inesperada"):
        recovery.repair_activation(home, tty=True, input_fn=lambda _: "REPARAR")
    assert (home / "current").resolve() == dirs["v0.8.7"]
    assert (home / ".activation-intent.json").exists()


def test_activation_status_never_runs_io_over_network_or_modifies_data(tmp_path):
    home, _ = setup_home(tmp_path)
    report = recovery.activation_status(home)
    assert report == {
        "schema": "nexus.activation-repair.v1",
        "status": "clear",
        "repair_requires_confirmation": False,
        "database_modified": False,
        "external_network_used": False,
        "automatic_repair_performed": False,
    }


def test_repair_uses_same_exclusive_maintenance_lock(tmp_path, monkeypatch):
    home, _ = interrupt_before_current(tmp_path, monkeypatch)
    with recovery.maintenance_lock(home):
        with pytest.raises(recovery.RecoveryError, match="Outra manutenção"):
            recovery.repair_activation(home, tty=True, input_fn=lambda _: "REPARAR")
    assert (home / "auto-update.enabled").read_text() == "1\n"


def test_standalone_recovery_status_command_remains_import_free(
    tmp_path, monkeypatch,
):
    home, _ = setup_home(tmp_path)
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    script = install_linux.write_recovery_launcher(home)
    result = os.popen("true").close()  # no bearing on tested command
    assert result is None
    data = script.read_text(encoding="utf-8")
    assert "_INSTALL_HOME = " in data
    assert "from nexus" not in data
    assert "--repair-activation" in data
