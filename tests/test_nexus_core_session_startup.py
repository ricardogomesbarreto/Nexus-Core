"""Session startup waits for a local Ollama service to accept connections."""

import os
from pathlib import Path
import subprocess

import pytest


@pytest.mark.parametrize("ready_after,expected_code", [(3, 0), (100, 1)])
def test_ollama_service_gets_bounded_readiness_wait(tmp_path, ready_after, expected_code):
    binary = tmp_path / "bin"
    binary.mkdir()
    commands = {
        "pg_isready": "exit 0",
        "systemctl": (
            'if [[ "$*" == *"is-active"* ]]; then exit 1; fi\n'
            'if [[ "$*" == *"show"* ]]; then printf "%032d\\n" 1; fi\n'
            'exit 0'
        ),
        "sudo": '"$@"',
        "sleep": 'printf "wait\\n" >> "$NEXUS_FAKE_SLEEPS"',
        "curl": (
            'count=$(cat "$NEXUS_FAKE_CALLS" 2>/dev/null || printf 0)\n'
            'count=$((count+1))\n'
            'printf "%s" "$count" > "$NEXUS_FAKE_CALLS"\n'
            'printf "private transport detail\\n" >&2\n'
            'test "$count" -ge "$NEXUS_FAKE_READY_AFTER"'
        ),
    }
    for name, body in commands.items():
        path = binary / name
        path.write_text("#!/usr/bin/env bash\n" + body + "\n")
        path.chmod(0o755)
    env = os.environ.copy()
    env.update({
        "PATH": f"{binary}:{env['PATH']}",
        "NEXUS_FAKE_CALLS": str(tmp_path / "calls"),
        "NEXUS_FAKE_SLEEPS": str(tmp_path / "sleeps"),
        "NEXUS_FAKE_READY_AFTER": str(ready_after),
        "XDG_RUNTIME_DIR": str(tmp_path),
    })
    script = Path(__file__).resolve().parents[1] / "scripts" / "nexus_core_session.sh"
    result = subprocess.run(["bash", str(script), "start"], env=env,
                            capture_output=True, text=True, timeout=10)
    assert result.returncode == expected_code
    assert "[SERVIÇO] Iniciando Ollama local" in result.stdout
    assert "private transport detail" not in result.stderr
    if expected_code == 0:
        assert "[SERVIÇO] Ollama local: pronto." in result.stdout
        assert (tmp_path / "calls").read_text() == "3"
    else:
        assert "após 30 segundos" in result.stderr
        assert (tmp_path / "calls").read_text() == "31"


def test_stop_preserves_preexisting_services_and_only_stops_own_instances(tmp_path):
    binary = tmp_path / "bin"
    binary.mkdir()
    active = tmp_path / "active"
    active.mkdir()
    runtime = tmp_path / "runtime"
    runtime.mkdir(mode=0o700)
    commands = {
        "pg_lsclusters": 'printf "18 main 5432 online postgres\\n"',
        "pg_isready": 'test -f "$NEXUS_FAKE_ACTIVE/postgresql@18-main.service.active"',
        "curl": 'test -f "$NEXUS_FAKE_ACTIVE/ollama.service.active"',
        "sudo": '"$@"',
        "systemctl": (
            'unit=""\n'
            'for argument in "$@"; do [[ "$argument" == *.service ]] && unit="$argument"; done\n'
            'case " $* " in\n'
            '  *" cat "*) exit 0;;\n'
            '  *" is-active "*) test -f "$NEXUS_FAKE_ACTIVE/$unit.active";;\n'
            '  *" show "*) cat "$NEXUS_FAKE_ACTIVE/$unit.id" 2>/dev/null || true;;\n'
            '  *" start "*) touch "$NEXUS_FAKE_ACTIVE/$unit.active"; '
            'printf "%032d\\n" 1 > "$NEXUS_FAKE_ACTIVE/$unit.id";;\n'
            '  *" stop "*) printf "%s\\n" "$unit" >> "$NEXUS_FAKE_STOPS"; '
            'rm -f "$NEXUS_FAKE_ACTIVE/$unit.active";;\n'
            'esac\n'
        ),
    }
    for name, body in commands.items():
        path = binary / name
        path.write_text("#!/usr/bin/env bash\n" + body + "\n")
        path.chmod(0o755)
    env = os.environ.copy()
    env.update({"PATH": f"{binary}:{env['PATH']}", "XDG_RUNTIME_DIR": str(runtime),
                "NEXUS_FAKE_ACTIVE": str(active), "NEXUS_FAKE_STOPS": str(tmp_path / "stops")})
    script = Path(__file__).resolve().parents[1] / "scripts" / "nexus_core_session.sh"

    def run(action):
        result = subprocess.run(["bash", str(script), action], env=env,
                                capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr

    # A ready service belongs to another application; Nexus must never stop it.
    for unit in ("postgresql@18-main.service", "ollama.service"):
        (active / f"{unit}.active").touch()
        (active / f"{unit}.id").write_text("1".zfill(32) + "\n")
    run("start")
    run("stop")
    assert not (tmp_path / "stops").exists()
    assert all((active / f"{unit}.active").exists()
               for unit in ("postgresql@18-main.service", "ollama.service"))

    for unit in ("postgresql@18-main.service", "ollama.service"):
        (active / f"{unit}.active").unlink()
    run("start")
    state = runtime / "nexus-core" / "started-services"
    assert state.stat().st_mode & 0o777 == 0o600
    # Another actor restarted Ollama; its new InvocationID is not ours.
    (active / "ollama.service.id").write_text("2".zfill(32) + "\n")
    run("stop")
    assert (tmp_path / "stops").read_text().splitlines() == ["postgresql@18-main.service"]
    assert (active / "ollama.service.active").exists()
    run("stop")
    assert (tmp_path / "stops").read_text().splitlines() == ["postgresql@18-main.service"]

    # Without private session state, starting an unavailable service is refused.
    (active / "ollama.service.active").unlink()
    without_runtime = {key: value for key, value in env.items() if key != "XDG_RUNTIME_DIR"}
    denied = subprocess.run(["bash", str(script), "start"], env=without_runtime,
                            capture_output=True, text=True, timeout=10)
    assert denied.returncode != 0
    assert "XDG_RUNTIME_DIR privado indisponível" in denied.stderr
    assert not (active / "ollama.service.active").exists()
