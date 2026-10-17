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
        "systemctl": "exit 0",
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
