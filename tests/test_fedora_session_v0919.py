"""Fedora session start/stop must preserve preexisting system services."""
import os
from pathlib import Path
import subprocess


def test_fedora_session_start_stop_does_not_stop_preexisting_services(tmp_path):
    binaries = tmp_path / "bin"
    active = tmp_path / "active"
    runtime = tmp_path / "runtime"
    for directory in (binaries, active, runtime):
        directory.mkdir(mode=0o700)
    stopped = tmp_path / "stopped"
    commands = {
        "pg_lsclusters": "exit 1",
        "pg_isready": 'test -f "$TEST_ACTIVE/postgresql.service.active"',
        "curl": 'test -f "$TEST_ACTIVE/ollama.service.active"',
        "sudo": 'if [[ "$1" == "-n" ]]; then shift; fi\n"$@"',
        "systemctl": (
            'unit=""\n'
            'for arg in "$@"; do [[ "$arg" == *.service ]] && unit="$arg"; done\n'
            'case " $* " in\n'
            '  *" cat "*) exit 0;;\n'
            '  *" is-active "*) test -f "$TEST_ACTIVE/$unit.active";;\n'
            '  *" show "*) cat "$TEST_ACTIVE/$unit.id" 2>/dev/null || true;;\n'
            '  *" start "*) touch "$TEST_ACTIVE/$unit.active"; '
            'printf "%032d\\n" 1 > "$TEST_ACTIVE/$unit.id";;\n'
            '  *" stop "*) printf "%s\\n" "$unit" >> "$TEST_STOPPED"; '
            'rm -f "$TEST_ACTIVE/$unit.active";;\n'
            'esac\n'
        ),
    }
    for name, body in commands.items():
        script = binaries / name
        script.write_text("#!/usr/bin/env bash\n" + body + "\n", encoding="utf-8")
        script.chmod(0o755)
    environment = os.environ.copy()
    environment.update({
        "PATH": str(binaries) + os.pathsep + environment["PATH"],
        "XDG_RUNTIME_DIR": str(runtime),
        "TEST_ACTIVE": str(active),
        "TEST_STOPPED": str(stopped),
    })
    session = Path(__file__).resolve().parents[1] / "scripts/nexus_core_session.sh"

    def invoke(action):
        result = subprocess.run(
            ["bash", str(session), action], env=environment,
            text=True, capture_output=True, timeout=12,
        )
        assert result.returncode == 0, result.stderr
        return result.stdout

    assert "postgresql.service" in invoke("status")

    # Installed Fedora services belong to other apps: do not adopt or stop.
    for unit in ("postgresql.service", "ollama.service"):
        (active / (unit + ".active")).touch()
        (active / (unit + ".id")).write_text("1".zfill(32) + "\n")
    invoke("start")
    invoke("stop")
    assert all((active / (unit + ".active")).exists()
               for unit in ("postgresql.service", "ollama.service"))
    assert not stopped.exists()

    for unit in ("postgresql.service", "ollama.service"):
        (active / (unit + ".active")).unlink()
    invoke("start")
    state = runtime / "nexus-core" / "started-services"
    assert state.exists()
    assert "postgresql.service" in state.read_text()
    assert "ollama.service" in state.read_text()
    invoke("stop")
    assert set(stopped.read_text().splitlines()) == {
        "postgresql.service", "ollama.service",
    }
    assert not (active / "postgresql.service.active").exists()
    assert not (active / "ollama.service.active").exists()
    assert not state.exists()
