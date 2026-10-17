"""Regression: installing the user Ollama service must never enable boot/login.

This is a user requirement on low-RAM Ubuntu notebooks. The installer starts
a static unit only for this session. System-wide services are not changed.
"""
from pathlib import Path

import pytest

from scripts import install_linux


def test_local_ollama_installer_starts_static_user_unit_without_enable(tmp_path, monkeypatch):
    calls = []
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    monkeypatch.setattr(
        install_linux, "_run",
        lambda cmd, **kw: calls.append((cmd, kw)),
    )
    binary = tmp_path / "runtime" / "ollama"
    binary.parent.mkdir()
    binary.write_bytes(b"local-test")

    install_linux._user_ollama_service(binary)

    unit = tmp_path / ".config" / "systemd" / "user" / "nexus-core-ollama.service"
    assert unit.exists()
    text = unit.read_text(encoding="utf-8")
    assert "ExecStart=" in text and "127.0.0.1:11434" in text
    assert "[Install]" not in text
    assert "WantedBy=" not in text
    assert unit.stat().st_mode & 0o077 == 0
    assert [call[0] for call in calls] == [
        ["systemctl", "--user", "daemon-reload"],
        ["systemctl", "--user", "start", "nexus-core-ollama.service"],
    ]
    assert not any("enable" in call[0] or "--now" in call[0] for call in calls)


def test_local_ollama_installer_never_replaces_existing_unit(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    folder = tmp_path / ".config" / "systemd" / "user"
    folder.mkdir(parents=True)
    unit = folder / "nexus-core-ollama.service"
    unit.write_text("existing-customized-unit")
    monkeypatch.setattr(
        install_linux, "_run",
        lambda *args, **kw: pytest.fail("Installer should not mutate existing user service"),
    )
    with pytest.raises(RuntimeError):
        install_linux._user_ollama_service(Path("/usr/bin/ollama"))
    assert unit.read_text() == "existing-customized-unit"


def test_local_ollama_installer_rejects_symlinked_unit_folder(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    linked = tmp_path / ".config" / "systemd" / "user"
    linked.parent.mkdir(parents=True)
    external = tmp_path / "external"
    external.mkdir()
    linked.symlink_to(external, target_is_directory=True)
    monkeypatch.setattr(
        install_linux, "_run",
        lambda *args, **kw: pytest.fail("A symlink cannot trigger system commands"),
    )
    with pytest.raises(RuntimeError, match="insegura"):
        install_linux._user_ollama_service(Path("/usr/bin/ollama"))
    assert list(external.iterdir()) == []
