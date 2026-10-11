"""NEXUS CORE v0.8.7 — pre-activation checks may never boot the app."""
import json
import subprocess
from pathlib import Path

import pytest

from nexus.updates import manager, verification
from nexus.updates.releases import ReleaseWheel, UpdateError


GOOD = {
    "mode": "passive",
    "target": "ubuntu_24_04_lts",
    "system": "Linux",
    "installer_supported": True,
    "python_supported": True,
    "changes_performed": False,
    "missing_required": [],
}


@pytest.mark.parametrize("changes", [
    {"mode": "active"},
    {"target": "linux_other_distro_future"},
    {"target": "ubuntu_not_yet_validated"},
    {"system": "Darwin"},
    {"installer_supported": False},
    {"python_supported": False},
    {"changes_performed": True},
    {"missing_required": ["postgresql"]},
    {"missing_required": ["python3-tk"]},
])
def test_fails_closed_on_unvalidated_linux_platform(changes):
    data = dict(GOOD, **changes)
    with pytest.raises(verification.RuntimeVerificationError):
        verification.validate_platform_report(json.dumps(data))


@pytest.mark.parametrize("content", [
    "not json", "{}", "[]", "null", "", "{" + "x" * 13000,
])
def test_malformed_platform_report_does_not_pass(content):
    with pytest.raises(verification.RuntimeVerificationError):
        verification.validate_platform_report(content)


def test_read_only_ubuntu_report_passes_without_side_effects():
    verification.validate_platform_report(json.dumps(GOOD))
    verification.validate_platform_report(json.dumps(GOOD).encode("utf-8"))


def test_expected_version_exact_match_only():
    verification.validate_version_output(b"Nexus Core 0.8.7\n", "0.8.7")
    for payload in ["Nexus Core 0.8.6", "Nexus Core 0.8.7 extra", ""]:
        with pytest.raises(verification.RuntimeVerificationError):
            verification.validate_version_output(payload, "0.8.7")


def test_isolated_runtime_order_and_no_app_boot():
    calls = []
    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        output = b""
        if "--version" in argv:
            output = b"Nexus Core 0.8.7\n"
        elif "--platform-check" in argv:
            output = json.dumps(GOOD).encode()
        return subprocess.CompletedProcess(argv, 0, stdout=output)
    verification.verify_installed_runtime(
        Path("/tmp/isolated/bin/python"), "0.8.7", run=fake_run
    )
    assert len(calls) == 3
    assert [args[-1] for args, _ in calls] == [
        "check", "--version", "--platform-check",
    ]
    for args, kw in calls:
        assert args[:3] == ["/tmp/isolated/bin/python", "-I", "-m"]
        assert kw["stdin"] == subprocess.DEVNULL
        assert kw["stderr"] == subprocess.DEVNULL
        assert kw["stdout"] == subprocess.PIPE
        assert kw["check"] is True
        assert kw["timeout"] <= 30
        assert "--desktop" not in args


@pytest.mark.parametrize("step", ["check", "--version", "--platform-check"])
def test_subprocess_failure_prevents_activation(step):
    def fake_run(argv, **kw):
        if argv[-1] == step:
            raise subprocess.CalledProcessError(1, argv)
        output = b"Nexus Core 0.8.7\n" if "--version" in argv else json.dumps(GOOD).encode()
        return subprocess.CompletedProcess(argv, 0, stdout=output)
    with pytest.raises(verification.RuntimeVerificationError):
        verification.verify_installed_runtime(Path("/tmp/env/bin/python"), "0.8.7", run=fake_run)


def test_nonzero_result_even_without_check_exception_is_rejected():
    def fake_run(argv, **kw):
        return subprocess.CompletedProcess(argv, 3, stdout=b"")
    with pytest.raises(verification.RuntimeVerificationError):
        verification.verify_installed_runtime(Path("/tmp/env/bin/python"), "0.8.7", run=fake_run)


def test_update_invalid_platform_keeps_previous_current_and_cleans_new(tmp_path, monkeypatch):
    home = tmp_path / "managed"
    manager.set_autoupdate(True, home)
    versions = home / "versions"
    old = versions / "v0.8.6"
    (old / "bin").mkdir(parents=True)
    (old / "bin/python").write_text("existing")
    (home / "current").symlink_to(old)

    release = ReleaseWheel(
        "0.8.7", "nexus_core-0.8.7-py3-none-any.whl",
        "https://github.com/ricardogomesbarreto/Nexus-Core/releases/download/v0.8.7/nexus_core-0.8.7-py3-none-any.whl",
        "0" * 64, 1024,
    )
    monkeypatch.setattr(manager, "pending_release", lambda _: release)
    monkeypatch.setattr(manager, "_verify_wheel", lambda *args: True)
    def fake_venv(target, **kwargs):
        (target / "bin").mkdir(parents=True)
        (target / "bin/python").write_text("candidate")
    monkeypatch.setattr(manager.venv, "create", fake_venv)
    invoked = []
    def fake_run(cmd, **kw):
        invoked.append(cmd[-1])
        if "--platform-check" in cmd:
            report = dict(GOOD, target="linux_other_distro_future")
            return subprocess.CompletedProcess(cmd, 0, stdout=json.dumps(report).encode())
        if "--version" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"Nexus Core 0.8.7\n")
        return subprocess.CompletedProcess(cmd, 0, stdout=b"")
    monkeypatch.setattr(manager.subprocess, "run", fake_run)

    with pytest.raises(UpdateError, match="preservada"):
        manager.install_staged(home, current_version="0.8.6")
    assert invoked[0].endswith("nexus_core-0.8.7-py3-none-any.whl[voice,vision]")
    assert invoked[1:] == ["check", "--version", "--platform-check"]
    assert (home / "current").resolve() == old
    assert not (versions / "v0.8.7").exists()
    assert manager.autoupdate_enabled(home) is True


def test_new_installer_validation_rejects_missing_ubuntu_dependency(tmp_path, monkeypatch):
    from scripts import install_linux
    from nexus.config.settings import settings
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    def fake_venv(path, **kwargs):
        (path / "bin").mkdir(parents=True)
        (path / "bin/python").write_text("stub")
    monkeypatch.setattr(install_linux.venv, "create", fake_venv)
    def fake_run(cmd, **kwargs):
        if "--platform-check" in cmd:
            return subprocess.CompletedProcess(
                cmd, 0, stdout=json.dumps(dict(GOOD, missing_required=["pg_isready"]))
            )
        if "--version" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout="Nexus Core " + settings.version)
        return subprocess.CompletedProcess(cmd, 0, stdout=None)
    monkeypatch.setattr(install_linux, "_run", fake_run)
    with pytest.raises(verification.RuntimeVerificationError):
        install_linux.install_managed_python()
    assert not (manager.managed_home() / "current").is_symlink()
