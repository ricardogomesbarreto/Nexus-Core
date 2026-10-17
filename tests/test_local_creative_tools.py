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


@pytest.mark.parametrize("spoken,kind", [
    ("Converta /home/usuario/Documentos/relatorio.docx em /home/usuario/Documentos/relatorio.pdf.", "document"),
    ("Converta /home/usuario/Imagens/foto.jpg em /home/usuario/Imagens/foto.webp", "image"),
    ("Extraia o texto de /home/usuario/Documentos/estudo.pdf em /home/usuario/Documentos/estudo.txt.", "pdf_text"),
])
def test_exact_conversion_phrase_avoids_ollama(spoken, kind):
    from nexus.agent.planner import _simple_creative_request
    action = _simple_creative_request(json.dumps({"historico": [], "mensagem_atual": spoken}))
    assert action is not None
    assert action[0] == "craft_convert_local"
    assert action[1]["kind"] == kind
    assert action[1]["source"].startswith("/home/usuario/")
    assert action[1]["output"].startswith("/home/usuario/")


def test_optional_cli_conversion_still_requests_consent_and_works_offline(tmp_path, monkeypatch):
    executor, home, confirmation = setup_tools(tmp_path)
    document = home / "relatorio.docx"
    destination = home / "relatorio.pdf"
    document.write_bytes(b"documento local")
    monkeypatch.setattr("nexus.tools.creative.shutil.which", lambda name: None)

    class ModelMustNotRun:
        def generate(self, request):
            pytest.fail("Conversão com caminhos explícitos não chama o Ollama")

    agent = AgentPlanner(ModelMustNotRun(), executor.registry, executor)
    question = f"Converta {document} em {destination}"
    result = agent.run(json.dumps({"historico": [], "mensagem_atual": question}))
    assert not result.success
    assert "wordcraft-cli" in (result.tool_result.error or "")
    assert not destination.exists()
    assert len(confirmation.calls) == 1


def test_previous_context_does_not_authorize_conversion(tmp_path):
    from nexus.agent.planner import _simple_creative_request
    prompt = json.dumps({
        "mensagem_atual": "Como funciona a conversão de documentos?",
        "historico": [
            {"usuario": "Converta /home/user/arquivo.docx em /home/user/arquivo.pdf"}
        ],
    })
    assert _simple_creative_request(prompt) is None


def test_conversion_rejects_symlink_output_without_reading_private_source(
    tmp_path, monkeypatch,
):
    """A CLI returning success must not trick the assistant into copying secrets."""
    from types import SimpleNamespace

    executor, home, _ = setup_tools(tmp_path)
    source = home / "source.docx"
    source.write_bytes(b"source document")
    sensitive = home / "do-not-copy.txt"
    sensitive.write_bytes(b"PRIVATE INFORMATION MUST NOT BE COPIED")
    dest = home / "result.pdf"

    def fake_run(args, **kwargs):
        Path(args[3]).symlink_to(sensitive)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        "nexus.tools.creative.shutil.which", lambda name: "/usr/bin/wordcraft-cli",
    )
    monkeypatch.setattr("nexus.tools.creative.subprocess.run", fake_run)
    result = executor.execute(
        "craft_convert_local", source=str(source), output=str(dest),
        kind="document",
    )
    assert not result.success
    assert not dest.exists()
    assert sensitive.read_bytes() == b"PRIVATE INFORMATION MUST NOT BE COPIED"
    assert "PRIVATE INFORMATION" not in (result.error or "")


@pytest.mark.parametrize("contents", [
    b"", b"not a pdf", b"<!doctype html><html></html>",
])
def test_conversion_rejects_empty_or_mislabelled_pdf(tmp_path, monkeypatch, contents):
    from types import SimpleNamespace

    executor, home, _ = setup_tools(tmp_path)
    source = home / "source.docx"
    source.write_bytes(b"docx source")
    dest = home / "result.pdf"

    def fake_run(args, **kwargs):
        Path(args[3]).write_bytes(contents)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr(
        "nexus.tools.creative.shutil.which", lambda name: "/usr/bin/wordcraft-cli",
    )
    monkeypatch.setattr("nexus.tools.creative.subprocess.run", fake_run)
    result = executor.execute(
        "craft_convert_local", source=str(source), output=str(dest),
        kind="document",
    )
    assert not result.success
    assert not dest.exists()


def test_photo_edit_rejects_decompression_bombs_with_safe_error(tmp_path, monkeypatch):
    from PIL import Image

    executor, home, _ = setup_tools(tmp_path)
    source = home / "oversized.png"
    out = home / "processed.png"
    stream = io.BytesIO()
    Image.new("RGB", (100, 100), "navy").save(stream, "PNG")
    source.write_bytes(stream.getvalue())
    monkeypatch.setattr(Image, "MAX_IMAGE_PIXELS", 16)
    outcome = executor.execute(
        "edit_image_local", source=str(source), output=str(out),
        operation="grayscale",
    )
    assert not outcome.success
    assert not out.exists()
    assert "DecompressionBombError" in (outcome.error or "")


@pytest.mark.parametrize("suffix,header", [
    (".pdf", b"%PDF-1.7\nexample"),
    (".png", bytes.fromhex("89504e470d0a1a0a")),
    (".jpg", bytes.fromhex("ffd8ff")),
    (".webp", b"RIFF\x00\x00\x00\x00WEBP"),
    (".docx", bytes.fromhex("504b0304")),
])
def test_converted_output_has_minimum_file_format_validation(suffix, header):
    from nexus.tools.creative import _validate_converted_output

    _validate_converted_output(header, suffix)
    with pytest.raises(ValueError):
        _validate_converted_output(b"wrong output bytes", suffix)
