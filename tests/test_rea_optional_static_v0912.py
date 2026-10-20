"""REA optional static adapter: access controls and no implicit installation."""

import json
from pathlib import Path

import pytest

from nexus.agent.planner import _simple_creative_request
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import ReaStaticTool, ToolExecutor, ToolRegistry


class Consent:
    def __init__(self, allow=True):
        self.allow = allow
        self.calls = []
    def confirm(self, request):
        self.calls.append(request)
        return self.allow


def setup(tmp_path, approved=True):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    tool = ReaStaticTool()
    registry = ToolRegistry()
    registry.register(tool)
    consent = Consent(approved)
    exec = ToolExecutor(
        registry,
        SecurityGate(path_security=policy,
                     audit_logger=AuditLogger(tmp_path / "audit.log")),
        consent,
    )
    return exec, home, consent


def test_explicit_phrase_uses_only_current_turn_and_not_model():
    prompt = json.dumps({
        "historico": [{"usuario": "Inspecione Rust /home/u/outro.elf"}],
        "mensagem_atual": "Analise o binário Rust /home/u/programa.elf",
    })
    assert _simple_creative_request(prompt) == (
        "rea_static_local",
        {"mode": "rust", "source": "/home/u/programa.elf"},
    )
    neutral = json.dumps({
        "historico": [{"usuario": "Inspecione Rust /home/u/outro.elf"}],
        "mensagem_atual": "Olá",
    })
    assert _simple_creative_request(neutral) is None


def test_declining_consent_never_launches_rea(tmp_path, monkeypatch):
    executor, home, consent = setup(tmp_path, approved=False)
    sample = home / "program.elf"
    sample.write_bytes(b"\x7fELFtest")
    monkeypatch.setattr(
        "nexus.tools.rea_static.shutil.which",
        lambda _: pytest.fail("REA must not be looked up before approval"),
    )
    result = executor.execute(
        "rea_static_local", source=str(sample), mode="rust",
    )
    assert result.success is False
    assert len(consent.calls) == 1


def test_missing_rea_returns_clear_message_and_no_download(tmp_path, monkeypatch):
    executor, home, consent = setup(tmp_path)
    sample = home / "program.elf"
    sample.write_bytes(b"\x7fELFtest")
    monkeypatch.setattr("nexus.tools.rea_static.shutil.which", lambda _: None)
    result = executor.execute("rea_static_local", source=str(sample), mode="rust")
    assert result.success is False
    assert "não instalado" in result.error
    assert len(consent.calls) == 1


def test_optional_rea_is_allowlisted_and_discards_sensitive_results(tmp_path, monkeypatch):
    executor, home, consent = setup(tmp_path)
    sample = home / "program.elf"
    sample.write_bytes(b"\x7fELFTEST REA")
    received = []
    monkeypatch.setattr(
        "nexus.tools.rea_static.shutil.which", lambda _: "/usr/bin/rea",
    )

    def fake_cli(args, destination, directory, timeout=45):
        received.append((args, directory, timeout))
        assert args[0:2] == ["/usr/bin/rea", "inspect-rust-binary"]
        assert args[-1] == "--json"
        assert Path(args[2]).read_bytes() == sample.read_bytes()
        Path(destination).write_text(
            json.dumps({"architecture": "x86_64", "secrets": "PRIVATE_INFO"}),
            encoding="utf-8",
        )

    monkeypatch.setattr("nexus.tools.rea_static._bounded_stdout", fake_cli)
    result = executor.execute("rea_static_local", source=str(sample), mode="rust")
    assert result.success is True
    assert result.data["mode"] == "rust"
    assert "architecture" in result.data["summary"]
    assert "PRIVATE_INFO" not in json.dumps(result.data)
    assert not Path(received[0][0][2]).exists()
    assert len(consent.calls) == 1


def test_symlink_target_blocked_after_approval(tmp_path, monkeypatch):
    executor, home, consent = setup(tmp_path)
    target = home / "program.elf"
    target.write_bytes(b"\x7fELFtest")
    link = home / "link.elf"
    link.symlink_to(target)
    monkeypatch.setattr(
        "nexus.tools.rea_static.shutil.which", lambda _: "/usr/bin/rea",
    )
    monkeypatch.setattr(
        "nexus.tools.rea_static._bounded_stdout",
        lambda *args, **kwargs: pytest.fail("Should not invoke CLI on symlink"),
    )
    result = executor.execute("rea_static_local", source=str(link), mode="rust")
    assert not result.success


@pytest.mark.parametrize("kind,path", [
    ("rust", "a.js"), ("go", "a.dll"), ("electron", "a.exe"),
    ("shell", "a.bin"), ("native", "a.dll"),
])
def test_disallow_unlisted_modes_and_extensions(tmp_path, monkeypatch, kind, path):
    executor, home, _ = setup(tmp_path)
    target = home / path
    target.write_bytes(b"sample")
    monkeypatch.setattr(
        "nexus.tools.rea_static.shutil.which", lambda _: "/usr/bin/rea",
    )
    monkeypatch.setattr(
        "nexus.tools.rea_static._bounded_stdout",
        lambda *args, **kwargs: pytest.fail("Cannot invoke unsafe mode"),
    )
    assert not executor.execute(
        "rea_static_local", source=str(target), mode=kind,
    ).success


def test_invalid_or_oversized_rea_output_is_rejected(tmp_path, monkeypatch):
    executor, home, _ = setup(tmp_path)
    source = home / "dll.dll"
    source.write_bytes(b"MZtest")
    monkeypatch.setattr("nexus.tools.rea_static.shutil.which", lambda _: "/usr/bin/rea")

    def fake_cli(args, path, directory, timeout=45):
        Path(path).write_text("not-json", encoding="utf-8")

    monkeypatch.setattr("nexus.tools.rea_static._bounded_stdout", fake_cli)
    assert not executor.execute(
        "rea_static_local", source=str(source), mode="dotnet",
    ).success
