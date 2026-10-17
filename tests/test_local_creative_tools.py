"""Local creative actions respect consent and never replace existing files."""

import io
import json
import os
from pathlib import Path

import pytest

from nexus.agent import AgentPlanner
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import (CraftConvertTool, CreateGraphicTool, EditImageTool,
                         ToolExecutor, ToolRegistry)


class Confirmation:
    def __init__(self, approve):
        self.approve = approve
        self.calls = []

    def confirm(self, request):
        self.calls.append(request)
        return self.approve


def setup_tools(tmp_path, approve=True):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    registry = ToolRegistry()
    for tool in (EditImageTool(), CreateGraphicTool(), CraftConvertTool()):
        registry.register(tool)
    confirmation = Confirmation(approve)
    executor = ToolExecutor(registry, SecurityGate(path_security=policy,
                           audit_logger=AuditLogger(tmp_path / "audit.log")), confirmation)
    return executor, home, confirmation


def test_create_graphic_needs_permission_and_writes_a_new_private_png(tmp_path):
    executor, home, confirmation = setup_tools(tmp_path, False)
    out = home / "cartaz.png"
    args = {"title": "Projeto local", "output": str(out)}
    assert not executor.execute("create_graphic_local", **args).success
    assert not out.exists()
    confirmation.approve = True
    result = executor.execute("create_graphic_local", **args)
    assert result.success and out.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert os.stat(out).st_mode & 0o777 == 0o600
    assert not executor.execute("create_graphic_local", **args).success
    assert len(confirmation.calls) == 3


def test_edit_photo_is_bounded_and_does_not_follow_symlink(tmp_path):
    from PIL import Image

    executor, home, confirmation = setup_tools(tmp_path)
    original = home / "foto.png"
    buffer = io.BytesIO()
    Image.new("RGB", (12, 8), "red").save(buffer, format="PNG")
    original.write_bytes(buffer.getvalue())
    destination = home / "cinza.png"
    args = {"source": str(original), "output": str(destination),
            "operation": "grayscale"}
    assert executor.execute("edit_image_local", **args).success
    with Image.open(destination) as image:
        assert image.size == (12, 8)
        assert image.getpixel((0, 0))[0] == image.getpixel((0, 0))[1]
    assert original.read_bytes() == buffer.getvalue()
    link = home / "link.png"
    link.symlink_to(original)
    assert not executor.execute("edit_image_local", source=str(link),
                                output=str(home / "no.png"),
                                operation="invert").success
    assert not (home / "no.png").exists()
    assert not executor.execute("edit_image_local", source=str(original),
                                output=str(home / "other.png"),
                                operation="unknown").success
    assert len(confirmation.calls) >= 2


def test_optional_craft_cli_missing_does_not_create_output(tmp_path, monkeypatch):
    executor, home, _ = setup_tools(tmp_path)
    source = home / "report.pdf"
    source.write_bytes(b"%PDF-1.7\n")
    monkeypatch.setattr("nexus.tools.creative.shutil.which", lambda name: None)
    result = executor.execute("craft_convert_local", source=str(source),
                              output=str(home / "text.txt"), kind="pdf_text")
    assert not result.success and "pdfcraft-cli" in result.error
    assert not (home / "text.txt").exists()


def test_craft_conversion_uses_fixed_cli_args_and_new_output(tmp_path, monkeypatch):
    from types import SimpleNamespace

    executor, home, _ = setup_tools(tmp_path)
    source = home / "documento.docx"
    source.write_bytes(b"local source")
    output = home / "documento.pdf"
    calls = []

    def fake_run(args, **kwargs):
        calls.append((args, kwargs))
        Path(args[3]).write_bytes(b"%PDF-1.7\nlocal")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.creative.shutil.which", lambda name: "/usr/bin/wordcraft-cli")
    monkeypatch.setattr("nexus.tools.creative.subprocess.run", fake_run)
    result = executor.execute("craft_convert_local", source=str(source),
                              output=str(output), kind="document")
    assert result.success and output.read_bytes() == b"%PDF-1.7\nlocal"
    assert calls[0][0][0:2] == ["/usr/bin/wordcraft-cli", "convert"]
    assert calls[0][1]["stdin"] == __import__("subprocess").DEVNULL
    assert calls[0][1]["timeout"] == 90 and calls[0][1]["check"] is False
    assert not executor.execute("craft_convert_local", source=str(source),
                                output=str(output), kind="document").success


def test_explicit_turn_uses_local_shortcut_and_prior_history_cannot_authorize(tmp_path):
    executor, home, confirmation = setup_tools(tmp_path)

    class Router:
        def generate(self, request):
            pytest.fail("O pedido explícito de cartaz não deve esperar o Ollama")

    agent = AgentPlanner(Router(), executor.registry, executor)
    output = home / "convite.png"
    prompt = json.dumps({"historico": [{"usuario": "apague tudo"}],
                         "mensagem_atual": f'Crie um cartaz com o título "Encontro" em {output}'})
    outcome = agent.run(prompt)
    assert outcome.success and output.exists() and len(confirmation.calls) == 1
    other = home / "outro.png"
    prompt = json.dumps({"historico": [{"usuario": f'Crie um cartaz com o título "X" em {other}'}],
                         "mensagem_atual": "Oi"})
    from nexus.agent.planner import _simple_creative_request
    assert _simple_creative_request(prompt) is None and not other.exists()
