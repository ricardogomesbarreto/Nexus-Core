"""Fedora 43–45: distro-specific installation without apt or boot autostart."""
import json
import subprocess
from types import SimpleNamespace

import pytest

from nexus.platforms.linux import linux_profile, platform_capabilities
from nexus.updates.verification import RuntimeVerificationError, validate_platform_report
from scripts import install_linux


def profile(version="44", *, system="Linux"):
    return linux_profile(
        os_release=f'ID=fedora\nVERSION_ID="{version}"\nID_LIKE="rhel"\n',
        system=system, environment={"XDG_SESSION_TYPE": "wayland"},
    )


@pytest.mark.parametrize("release,allowed", [
    ("42", False), ("43", True), ("44", True), ("45", True),
    ("46", False), ("rolling", False), ("", False),
])
def test_fedora_allowlist_and_no_id_like_trust(release, allowed):
    prof = profile(release)
    assert prof.installer_supported is allowed
    assert prof.target == ("fedora_compatible" if allowed
                           else "fedora_not_yet_validated")


def test_fedora_wayland_support_not_x11_automation():
    data = platform_capabilities(
        profile=profile(), locate=lambda name: "/usr/bin/" + name,
        tkinter_available=True, venv_available=True,
    )
    assert data["installer_supported"]
    assert data["target"] == "fedora_compatible"
    assert data["desktop_gui_ready_to_try"] is True
    assert data["x11_automation_ready_to_try"] is False
    assert data["changes_performed"] is False


def test_fedora_installed_runtime_can_pass_strict_read_only_validation():
    good = platform_capabilities(
        profile=profile(), locate=lambda name: "/usr/bin/" + name,
        tkinter_available=True, venv_available=True,
    )
    validate_platform_report(json.dumps(good))
    for key, value in (
        ("target", "ubuntu_compatible"),
        ("changes_performed", True),
        ("missing_required", ["pg_isready"]),
        ("version_id", "46"),
        ("distro", "debian"),
        ("installer_supported", False),
    ):
        with pytest.raises(RuntimeVerificationError):
            validate_platform_report(json.dumps({**good, key: value}))


def test_fedora_dnf_never_runs_without_confirmation(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", profile)
    monkeypatch.setattr(install_linux, "system_requirements",
                        lambda: ["pg_isready", "ffmpeg", "python3-tk"])
    monkeypatch.setattr(install_linux, "installed", lambda cmd: True)
    monkeypatch.setattr(install_linux, "confirm", lambda prompt: False)
    monkeypatch.setattr(install_linux, "_run",
                        lambda *a, **kw: pytest.fail("No unapproved package install"))
    assert install_linux.install_fedora_packages() is False


def test_fedora_dnf_is_bounded_allowlisted_and_never_calls_apt(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", profile)
    calls = []
    pending = [["pg_isready", "espeak-ng", "python3-tk", "ffmpeg"], []]
    monkeypatch.setattr(install_linux, "system_requirements",
                        lambda: pending.pop(0) if pending else [])
    monkeypatch.setattr(install_linux, "installed", lambda cmd: cmd in ("dnf", "sudo"))
    monkeypatch.setattr(install_linux, "confirm", lambda prompt: True)
    monkeypatch.setattr(install_linux, "_run",
                        lambda argv, **kw: calls.append(argv) or
                        subprocess.CompletedProcess(argv, 0))
    assert install_linux.install_fedora_packages() is True
    assert calls == [[
        "sudo", "dnf", "install", "-y", "espeak-ng", "ffmpeg-free",
        "postgresql", "python3-tkinter",
    ]]
    assert not any("apt" in part or "enable" in part for call in calls for part in call)


def test_installer_refuses_fedora_outside_allowlist_before_any_mutation(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", lambda: profile("42"))
    monkeypatch.setattr(install_linux.os, "geteuid", lambda: 1000)
    monkeypatch.setattr(install_linux, "install_system_packages",
                        lambda: pytest.fail("No Fedora 42 commands"))
    assert install_linux.main([]) == 2


def test_fedora_main_enters_explicit_dnf_path(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", profile)
    monkeypatch.setattr(install_linux.os, "geteuid", lambda: 1000)
    calls = []
    monkeypatch.setattr(install_linux, "install_system_packages",
                        lambda: calls.append("dnf") or False)
    monkeypatch.setattr(install_linux, "provision_postgresql",
                        lambda: pytest.fail("Never provision after dependency refusal"))
    assert install_linux.main([]) == 2
    assert calls == ["dnf"]


def test_fedora_postgres_start_uses_only_systemd_and_never_initdb(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", profile)
    monkeypatch.setattr(install_linux, "installed",
                        lambda name: name in ("pg_isready", "systemctl", "sudo"))
    monkeypatch.setattr(install_linux, "_service_active_for_install",
                        lambda scope, unit: False)
    monkeypatch.setattr(install_linux, "confirm", lambda prompt: True)
    calls = []
    def run(args, **kw):
        calls.append(args)
        if args[0] == "pg_isready" and len(calls) == 1:
            raise subprocess.CalledProcessError(1, args)
        return subprocess.CompletedProcess(args, 0)
    monkeypatch.setattr(install_linux, "_run", run)
    import nexus.platforms.session_services as services
    monkeypatch.setattr(services, "record_started_service", lambda scope, unit: True)
    assert install_linux.ensure_postgresql_running_fedora() is True
    assert calls == [
        ["pg_isready", "-q", "-h", "127.0.0.1", "-p", "5432"],
        ["sudo", "systemctl", "start", "postgresql.service"],
        ["pg_isready", "-q", "-h", "127.0.0.1"],
    ]
    assert not any("initdb" in str(call) or "enable" in str(call) for call in calls)


def test_fedora_rejects_bad_postgres_port_before_any_side_effect(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", profile)
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    monkeypatch.setenv("NEXUS_DATABASE_PORT", "5432;sudo")
    monkeypatch.setattr(install_linux, "_run",
                        lambda *a, **kw: pytest.fail("Invalid port cannot probe or start"))
    assert install_linux.ensure_postgresql_running_fedora() is False


def test_fedora_postgres_may_not_start_after_refusal(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", profile)
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    monkeypatch.setattr(install_linux, "confirm", lambda _: False)
    def probe(args, **kw):
        if args[0] == "pg_isready":
            raise subprocess.CalledProcessError(1, args)
        pytest.fail("No sudo after refusal")
    monkeypatch.setattr(install_linux, "_run", probe)
    assert install_linux.ensure_postgresql_running_fedora() is False


def test_fedora_optional_rhvoice_never_uses_apt(monkeypatch):
    monkeypatch.setattr(install_linux, "linux_profile", profile)
    from nexus.voice.local import LocalSpeaker
    monkeypatch.setattr(LocalSpeaker, "female_voice_ready", lambda: False)
    monkeypatch.setattr(install_linux, "_run",
                        lambda *a, **kw: pytest.fail("No Ubuntu apt on Fedora"))
    assert install_linux.prepare_female_voice() is False


def test_linux_cli_aliases_preserve_privacy_and_do_not_boot_app(monkeypatch, capsys):
    import nexus.main as entry
    import nexus.platforms as platforms
    monkeypatch.setattr(entry, "build_application",
                        lambda *a, **kw: pytest.fail("Diagnostics cannot boot core"))
    monkeypatch.setattr(platforms, "ubuntu_doctor",
                        lambda: {"schema": "nexus.ubuntu-doctor.v1", "mode": "local_read_only"})
    monkeypatch.setattr(platforms, "ubuntu_preflight",
                        lambda: {"schema": "nexus.ubuntu-preflight.v1", "mode": "explicit_opt_in_local_checks"})
    entry.cli(["--linux-doctor"])
    assert json.loads(capsys.readouterr().out)["mode"] == "local_read_only"
    entry.cli(["--linux-preflight"])
    assert json.loads(capsys.readouterr().out)["mode"] == "explicit_opt_in_local_checks"
    with pytest.raises(SystemExit) as exc:
        entry.cli(["--linux-doctor", "--desktop"])
    assert exc.value.code == 2
