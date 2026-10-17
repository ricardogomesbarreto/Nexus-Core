"""Original ZIP Craft CLI info/render integration, offline and authorization gates."""
import io
import json
import os
from pathlib import Path
import struct
from types import SimpleNamespace

import pytest

from nexus.agent import AgentPlanner
from nexus.agent.planner import _simple_creative_request
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import ToolExecutor, ToolRegistry, CraftInspectTool, PdfRenderTool
from nexus.tools.craft_inspect import _safe_summary
from nexus.tools.pdf_render import _validate_png


class Confirmation:
    def __init__(self, approve=True):
        self.approve = approve
        self.calls = 0

    def confirm(self, req):
        self.calls += 1
        return self.approve


def setup(tmp_path, approve=True):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    registry = ToolRegistry()
    registry.register(CraftInspectTool())
    registry.register(PdfRenderTool())
    confirmation = Confirmation(approve)
    executor = ToolExecutor(
        registry, SecurityGate(path_security=policy,
                               audit_logger=AuditLogger(tmp_path / "audit.log")),
        confirmation,
    )
    return executor, home, confirmation


@pytest.mark.parametrize("kind,values,expected", [
    ("pdf", {"pages": 3, "javascript": True, "attachments": 1,
             "title": "SECRET", "file": "/home/secret/file.pdf"}, "pages=3"),
    ("image", {"width": 12, "height": 24, "layers": [{"name": "SECRET"}],
               "file": "/home/secret/image.png"}, "width=12"),
    ("document", {"pages": 5, "words": 77, "author": "SECRET"}, "words=77"),
])
def test_info_safe_scalar_projection_never_includes_private_strings(kind, values, expected):
    summary = _safe_summary(kind, json.dumps(values).encode())
    assert expected in summary
    assert "SECRET" not in summary
    assert "/home/secret" not in summary
    assert "foram omitidos" in summary


@pytest.mark.parametrize("payload", [
    b"", b"bad json", b"[]", b'{"title":"SECRET"}',
    b'{"pages":-1}', b'{"pages":999999999}', b'{"pages":"3"}',
    b'{"pages":true}' * 100000,
])
def test_info_invalid_or_untrusted_output_fails_closed(payload):
    with pytest.raises(ValueError):
        _safe_summary("pdf", payload)


@pytest.mark.parametrize("kind,suffix,exe,key,value", [
    ("pdf", ".pdf", "pdfcraft-cli", "pages", 2),
    ("image", ".png", "photocraft-cli", "width", 500),
    ("document", ".docx", "wordcraft-cli", "words", 120),
])
def test_real_cli_arguments_and_gate_are_fixed(tmp_path, monkeypatch, kind, suffix, exe, key, value):
    executor, home, confirm = setup(tmp_path, approve=False)
    source = home / ("sample" + suffix)
    original = (b"%PDF-1.4\nsample" if suffix == ".pdf" else
                b"PK\x03\x04sample" if suffix == ".docx" else b"\x89PNG\r\n\x1a\nsample")
    source.write_bytes(original)
    calls = []

    def fake_run(argv, **kw):
        calls.append((argv, kw))
        assert argv[0] == "/usr/bin/" + exe
        assert argv[1] == "info"
        assert Path(argv[2]).is_file()
        assert Path(argv[2]).parent != source.parent
        assert kw["stdin"] == __import__("subprocess").DEVNULL
        assert kw["timeout"] == 45
        kw["stdout"].write(json.dumps({key: value, "title": "SECRET"}).encode())
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.craft_inspect.shutil.which", lambda cmd: "/usr/bin/" + cmd)
    monkeypatch.setattr("nexus.tools.craft_inspect.subprocess.run", fake_run)
    denied = executor.execute("craft_inspect_local", source=str(source), kind=kind)
    assert not denied.success and not calls
    confirm.approve = True
    result = executor.execute("craft_inspect_local", source=str(source), kind=kind)
    assert result.success and f"{key}={value}" in result.data["summary"]
    assert "SECRET" not in result.data["summary"]
    assert source.read_bytes() == original
    assert len(calls) == 1
    assert confirm.calls == 2


def _fake_png(width=6, height=8):
    return b"\x89PNG\r\n\x1a\n" + struct.pack(">I", 13) + b"IHDR" + struct.pack(
        ">IIBBBBB", width, height, 8, 2, 0, 0, 0
    ) + b"\x00\x00\x00\x00"


def test_pdf_render_is_private_new_file_and_original_untouched(tmp_path, monkeypatch):
    executor, home, confirmation = setup(tmp_path)
    source = home / "paper.pdf"
    source.write_bytes(b"%PDF-1.7\nsynthetic sample")
    dest = home / "preview.png"
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        assert argv[0:2] == ["/usr/bin/pdfcraft-cli", "render"]
        assert argv[3:7] == ["--page", "2", "--dpi", "96"]
        assert argv[7] == "--out"
        Path(argv[8]).write_bytes(_fake_png())
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.pdf_render.shutil.which", lambda name: "/usr/bin/pdfcraft-cli")
    monkeypatch.setattr("nexus.tools.pdf_render.subprocess.run", fake_run)
    action = executor.execute("pdf_render_local", source=str(source),
                              output=str(dest), page=2)
    assert action.success and action.data["page"] == 2
    assert dest.read_bytes().startswith(b"\x89PNG")
    assert dest.stat().st_mode & 0o777 == 0o600
    assert source.read_bytes() == b"%PDF-1.7\nsynthetic sample"
    assert confirmation.calls == 1 and len(calls) == 1
    assert not executor.execute("pdf_render_local", source=str(source),
                                output=str(dest), page=2).success


@pytest.mark.parametrize("bad", [
    b"", b"\x89PNG\r\n\x1a\n", _fake_png(0, 8),
    _fake_png(5000, 5000), b"<html>not a PNG</html>",
])
def test_pdf_render_rejects_invalid_or_massive_pixels(bad):
    with pytest.raises(ValueError):
        _validate_png(bad)


def test_pdf_render_symlink_output_from_cli_is_never_read(tmp_path, monkeypatch):
    executor, home, _ = setup(tmp_path)
    pdf = home / "paper.pdf"
    pdf.write_bytes(b"%PDF-1.7\n")
    secret = home / "secret.png"
    secret.write_bytes(_fake_png())

    def malicious(argv, **kwargs):
        Path(argv[8]).symlink_to(secret)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.pdf_render.shutil.which", lambda name: "/usr/bin/pdfcraft-cli")
    monkeypatch.setattr("nexus.tools.pdf_render.subprocess.run", malicious)
    dest = home / "copy.png"
    assert not executor.execute("pdf_render_local", source=str(pdf),
                                output=str(dest), page=1).success
    assert not dest.exists()


@pytest.mark.parametrize("utterance,name", [
    ("Consulte os metadados do arquivo /home/usuario/a.pdf", "craft_inspect_local"),
    ("Mostre os metadados da imagem /home/usuario/a.png", "craft_inspect_local"),
    ("Renderize a página 3 do PDF /home/usuario/a.pdf em /home/usuario/3.png", "pdf_render_local"),
])
def test_current_turn_natural_language_routing(utterance, name):
    action = _simple_creative_request(json.dumps({"mensagem_atual": utterance, "historico": []}))
    assert action is not None and action[0] == name
    if name == "pdf_render_local":
        assert action[1]["page"] == 3


def test_history_never_grants_metadata_or_render_permission():
    prompt = json.dumps({
        "mensagem_atual": "O que são metadados?",
        "historico": [{"usuario": "Consulte os metadados do arquivo /home/u/private.pdf"},
                     {"usuario": "Renderize a página 3 do PDF /home/u/a.pdf em /home/u/3.png"}],
    })
    assert _simple_creative_request(prompt) is None


def test_local_chat_uses_gate_without_ollama(tmp_path, monkeypatch):
    executor, home, confirmation = setup(tmp_path, approve=False)
    doc = home / "file.pdf"
    doc.write_bytes(b"%PDF-1.7\n")
    class NoModel:
        def generate(self, request):
            pytest.fail("Parser de metadados não deve carregar o Ollama")
    agent = AgentPlanner(NoModel(), executor.registry, executor)
    prompt = json.dumps({"mensagem_atual": f"Consulte os metadados do arquivo {doc}",
                         "historico": []})
    outcome = agent.run(prompt)
    assert not outcome.success
    assert confirmation.calls == 1
