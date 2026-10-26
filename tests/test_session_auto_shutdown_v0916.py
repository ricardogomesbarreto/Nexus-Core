"""Owned services are released on desktop exit, never borrowed instances."""

import os
from pathlib import Path
import subprocess

import pytest

from nexus.platforms import session_services as services


def _runtime(tmp_path, monkeypatch):
    runtime = tmp_path / "run"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    return runtime


def test_desktop_finally_cleans_up_even_when_startup_raises(monkeypatch):
    from nexus.desktop import window

    called = []
    monkeypatch.setattr(window, "_run_desktop_window", lambda: 2)
    monkeypatch.setattr(services, "stop_owned_services", lambda **kwargs: called.append("stop"))
    assert window.launch_desktop() == 2
    assert called == ["stop"]

    def fail():
        raise RuntimeError("display unavailable")
    monkeypatch.setattr(window, "_run_desktop_window", fail)
    with pytest.raises(RuntimeError, match="display unavailable"):
        window.launch_desktop()
    assert called == ["stop", "stop"]


def test_owned_services_stop_in_reverse_order_and_stale_ids_are_preserved(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path, monkeypatch)
    system = "postgresql@18-main.service"
    active = {system: "1" * 32, "ollama.service": "2" * 32,
              "postgresql@17-old.service": "4" * 32}
    calls = []

    def run(args, **kwargs):
        calls.append(args)
        unit = next((part for part in args if part.endswith(".service")), "")
        if "show" in args:
            return subprocess.CompletedProcess(args, 0, active.get(unit, "") + "\n")
        if "is-active" in args:
            return subprocess.CompletedProcess(args, 0 if unit in active else 3, "")
        if "stop" in args:
            active.pop(unit)
            return subprocess.CompletedProcess(args, 0, "")
        raise AssertionError(args)

    monkeypatch.setattr(services.subprocess, "run", run)
    assert services.record_started_service("system", system)
    assert services.record_started_service("system", "ollama.service")
    assert services.record_started_service("system", "postgresql@17-old.service")
    # The old cluster was restarted by another program; it must remain running.
    active["postgresql@17-old.service"] = "5" * 32
    assert services.stop_owned_services()
    assert [args[-1] for args in calls if "stop" in args] == ["ollama.service", system]
    assert "postgresql@17-old.service" in active
    assert not (runtime / "nexus-core" / "started-services").exists()
    assert services.stop_owned_services()


def test_failed_sudo_keeps_record_for_manual_stop(tmp_path, monkeypatch, capsys):
    runtime = _runtime(tmp_path, monkeypatch)
    path = runtime / "nexus-core" / "started-services"
    path.parent.mkdir(mode=0o700)
    path.write_text("system\tollama.service\t" + "a" * 32 + "\n")
    path.chmod(0o600)
    monkeypatch.setattr(services.shutil, "which", lambda _: None)

    def run(args, **kwargs):
        if "show" in args:
            return subprocess.CompletedProcess(args, 0, "a" * 32 + "\n")
        if "is-active" in args:
            return subprocess.CompletedProcess(args, 0, "")
        assert args == ["sudo", "-n", "systemctl", "stop", "ollama.service"]
        return subprocess.CompletedProcess(args, 1, "")

    monkeypatch.setattr(services.subprocess, "run", run)
    assert services.stop_owned_services() is False
    assert path.read_text().startswith("system\tollama.service\t")
    assert "stop no terminal" in capsys.readouterr().err


def test_graphical_authorization_stops_service_after_sudo_cache_expires(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path, monkeypatch)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    monkeypatch.setattr(services.shutil, "which", lambda command: f"/usr/bin/{command}")
    state = runtime / "nexus-core" / "started-services"
    state.parent.mkdir(mode=0o700)
    state.write_text("system\tollama.service\t" + "b" * 32 + "\n")
    state.chmod(0o600)
    commands = []

    def run(args, **kwargs):
        commands.append(args)
        if "show" in args:
            return subprocess.CompletedProcess(args, 0, "b" * 32 + "\n")
        if "is-active" in args:
            return subprocess.CompletedProcess(args, 0, "")
        return subprocess.CompletedProcess(args, 1 if args[0] == "sudo" else 0, "")

    monkeypatch.setattr(services.subprocess, "run", run)
    assert services.stop_owned_services()
    assert commands[-2:] == [["sudo", "-n", "systemctl", "stop", "ollama.service"],
                            ["/usr/bin/pkexec", "/usr/bin/systemctl", "stop", "ollama.service"]]
    assert not state.exists()


def test_untrusted_state_is_ignored(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path, monkeypatch)
    state = runtime / "nexus-core"
    state.mkdir(mode=0o700)
    target = tmp_path / "outside"
    target.write_text("system\tollama.service\t" + "a" * 32 + "\n")
    (state / "started-services").symlink_to(target)
    monkeypatch.setattr(services.subprocess, "run", lambda *a, **kw: pytest.fail("systemctl called"))
    assert services.stop_owned_services()
    assert not services.record_started_service("system", "ollama.service")
    assert target.exists()


def test_installer_does_not_claim_a_preexisting_postgres_unit(monkeypatch):
    from scripts import install_linux

    commands = []
    monkeypatch.setattr(install_linux, "installed", lambda _: True)
    monkeypatch.setattr(install_linux, "confirm", lambda _: True)

    def run(args, **kwargs):
        commands.append(args)
        if args[0] == "pg_isready":
            if not any(cmd[:3] == ["sudo", "systemctl", "start"] for cmd in commands):
                raise subprocess.CalledProcessError(2, args)
            return subprocess.CompletedProcess(args, 0)
        if args[0] == "pg_lsclusters":
            return subprocess.CompletedProcess(args, 0, "18 main 5432 online postgres\n")
        if args[:3] == ["systemctl", "is-active", "--quiet"]:
            return subprocess.CompletedProcess(args, 0)
        if args[:3] == ["sudo", "systemctl", "start"]:
            return subprocess.CompletedProcess(args, 0)
        raise AssertionError(args)

    monkeypatch.setattr(install_linux, "_run", run)
    monkeypatch.setattr(services, "record_started_service",
                        lambda *args: pytest.fail("preexisting service claimed"))
    assert install_linux.ensure_postgresql_running_for_install()


@pytest.mark.parametrize("launcher_exit", [0, 7])
def test_shell_desktop_stops_only_started_services_even_if_launcher_fails(tmp_path, launcher_exit):
    script = Path(__file__).resolve().parents[1] / "scripts" / "nexus_core_session.sh"
    bindir = tmp_path / "bin"
    bindir.mkdir()
    runtime = tmp_path / "run"
    runtime.mkdir(mode=0o700)
    home = tmp_path / "home"
    (home / ".local" / "bin").mkdir(parents=True)
    launcher = home / ".local" / "bin" / "nexus-core"
    launcher.write_text(f"#!/bin/sh\nexit {launcher_exit}\n")
    launcher.chmod(0o700)
    fake = {
        "pg_isready": "exit 0",
        "pg_lsclusters": 'printf "18 main 5432 online postgres\\n"',
        "curl": 'test -f "$FAKE_RUN/ollama.active"',
        "sudo": 'if [[ "${1:-}" == -n ]]; then shift; fi; "$@"',
        "systemctl": (
            'case " $* " in\n'
            '  *" cat "*) exit 0;;\n'
            '  *" is-active "*) test -f "$FAKE_RUN/ollama.active";;\n'
            '  *" show "*) printf "%032d\\n" 1;;\n'
            '  *" start "*) touch "$FAKE_RUN/ollama.active";;\n'
            '  *" stop "*) rm "$FAKE_RUN/ollama.active"; printf "stopped\\n" >> "$FAKE_RUN/stops";;\n'
            'esac\n'
        ),
    }
    for name, body in fake.items():
        path = bindir / name
        path.write_text("#!/usr/bin/env bash\n" + body + "\n")
        path.chmod(0o700)
    env = os.environ.copy()
    env.update({"PATH": f"{bindir}:{env['PATH']}", "FAKE_RUN": str(tmp_path),
                "XDG_RUNTIME_DIR": str(runtime), "HOME": str(home)})
    result = subprocess.run(["bash", str(script), "desktop"], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == launcher_exit, result.stderr
    assert (tmp_path / "stops").read_text().splitlines() == ["stopped"]
    assert not (tmp_path / "ollama.active").exists()
