"""A second desktop must not take down the services of an active window."""

import os
from pathlib import Path
import subprocess

from nexus.platforms import session_services as services


def _runtime(tmp_path, monkeypatch):
    runtime = tmp_path / "run"
    runtime.mkdir(mode=0o700)
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(runtime))
    return runtime


def test_second_desktop_does_not_run_or_clean_up_active_session(tmp_path, monkeypatch, capsys):
    from nexus.desktop import window

    runtime = _runtime(tmp_path, monkeypatch)
    state = runtime / "nexus-core" / "started-services"
    monkeypatch.setattr(window, "_run_desktop_window", lambda: 0)
    monkeypatch.setattr(services.subprocess, "run",
                        lambda *args, **kwargs: (_ for _ in ()).throw(AssertionError("stop called")))

    with services.desktop_session_lease() as held:
        assert held is True
        state.write_text("system\tollama.service\t" + "1" * 32 + "\n")
        state.chmod(0o600)
        assert window.launch_desktop() == 3
        assert services.stop_owned_services() is False
        assert state.exists()
        assert "janela" in capsys.readouterr().err
    # The lease is released even after a blocked second launch.
    with services.desktop_session_lease() as held:
        assert held is True


def test_shell_stop_does_not_interfere_with_active_desktop(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path, monkeypatch)
    script = Path(__file__).resolve().parents[1] / "scripts" / "nexus_core_session.sh"
    state = runtime / "nexus-core" / "started-services"
    with services.desktop_session_lease() as held:
        assert held is True
        state.write_text("system\tollama.service\t" + "1" * 32 + "\n")
        state.chmod(0o600)
        result = subprocess.run(["bash", str(script), "stop"], env=os.environ.copy(),
                                capture_output=True, text=True, timeout=10)
        assert result.returncode == 0, result.stderr
        assert "Outra janela do Nexus ativa" in result.stdout
        assert state.exists()


def test_unsafe_lease_file_blocks_new_window(tmp_path, monkeypatch):
    runtime = _runtime(tmp_path, monkeypatch)
    state_dir = runtime / "nexus-core"
    state_dir.mkdir(mode=0o700)
    outside = tmp_path / "other-file"
    outside.touch()
    (state_dir / "desktop.lock").symlink_to(outside)
    with services.desktop_session_lease() as held:
        assert held is False
    assert outside.exists()
