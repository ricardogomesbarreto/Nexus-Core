"""Advanced offline REA / Craft integrations, preserving per-action permissions."""
from __future__ import annotations

import io
import json
import os
from pathlib import Path
import struct
import zipfile
from types import SimpleNamespace

import pytest

from nexus.agent.planner import _simple_creative_request
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import EditImageTool, InspectArtifactTool, CraftConvertTool, ToolExecutor, ToolRegistry
from nexus.tools.creative import _validate_converted_output
from nexus.tools.static_analysis import _zip_summary
from nexus.tools.wasm_structure import MAX_SECTIONS, summarize_wasm


class Confirm:
    def __init__(self, response=True):
        self.response = response
        self.calls = 0

    def confirm(self, request):
        self.calls += 1
        return self.response


def executor(tmp_path, approved=True):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    reg = ToolRegistry()
    for tool in (EditImageTool(), InspectArtifactTool(), CraftConvertTool()):
        reg.register(tool)
    confirmation = Confirm(approved)
    return (ToolExecutor(reg, SecurityGate(path_security=policy,
                        audit_logger=AuditLogger(tmp_path / "audit.log")), confirmation),
            home, confirmation)


def wasm_section(number: int, payload: bytes = b"") -> bytes:
    assert len(payload) < 128
    return bytes((number, len(payload))) + payload


def test_wasm_sections_count_without_executing_code_or_reading_private_names():
    binary = b"\x00asm\x01\x00\x00\x00"
    binary += wasm_section(0, b"sensitive-name")
    binary += wasm_section(2, b"\x00")
    binary += wasm_section(7, b"\x00")
    binary += wasm_section(10, b"\x00")
    summary = summarize_wasm(binary, total_size=len(binary))
    assert "imports=1" in summary
    assert "exports=1" in summary
    assert "código=1" in summary
    assert "envelopes completos" in summary
    assert "sensitive-name" not in summary


def test_wasm_bounded_partial_and_malformed_fail_closed():
    head = b"\x00asm\x01\x00\x00\x00"
    partial = head + b"\x01\xff\x01"  # declared 255 bytes, not in prefix
    summary = summarize_wasm(partial, total_size=1000)
    assert "prefixo parcial" in summary
    with pytest.raises(ValueError):
        summarize_wasm(partial, total_size=len(partial))
    with pytest.raises(ValueError):
        summarize_wasm(head + b"\x01\xff\xff\xff\xff\x10", total_size=14)
    with pytest.raises(ValueError):
        summarize_wasm(head + wasm_section(1) * (MAX_SECTIONS + 1),
                       total_size=8 + 2 * (MAX_SECTIONS + 1))


def test_wasm_request_is_gated_and_never_executes_file(tmp_path, monkeypatch):
    ex, home, gate = executor(tmp_path, approved=False)
    sample = home / "module.wasm"
    sample.write_bytes(b"\x00asm\x01\x00\x00\x00" + wasm_section(7, b"\x00"))
    def denied(*args, **kwargs):
        pytest.fail("O analisador estático não pode iniciar subprocessos")
    monkeypatch.setattr("subprocess.run", denied)
    assert not ex.execute("inspect_artifact_local", source=str(sample)).success
    gate.response = True
    success = ex.execute("inspect_artifact_local", source=str(sample))
    assert success.success
    assert "exports=1" in success.data["summary"]
    assert gate.calls == 2
    assert sample.read_bytes().startswith(b"\x00asm")


def test_archive_classifications_and_metadata_are_index_only():
    for suffix, entries, expected in (
        (".docx", {"[Content_Types].xml": b"", "word/document.xml": b"confidential"}, "DOCX"),
        (".odt", {"mimetype": b"application/vnd.oasis.opendocument.text",
                  "content.xml": b"private"}, "ODT"),
        (".apk", {"AndroidManifest.xml": b"", "classes.dex": b"",
                  "lib/arm64-v8a/libexample.so": b"\x00"}, "APK"),
    ):
        buffer = io.BytesIO()
        with zipfile.ZipFile(buffer, "w") as z:
            for name, payload in entries.items():
                z.writestr(name, payload)
        buffer.seek(0)
        kind, summary = _zip_summary(buffer, suffix)
        assert kind == expected
        assert "private" not in summary
        assert "confidential" not in summary
        if kind == "APK":
            assert "ABIs conhecidas=arm64-v8a" in summary
            assert "bibliotecas nativas .so=1" in summary


def test_archive_reports_symlinks_without_following_them():
    data = io.BytesIO()
    with zipfile.ZipFile(data, "w") as z:
        link = zipfile.ZipInfo("link.txt")
        link.create_system = 3
        link.external_attr = (0o120777 << 16)
        z.writestr(link, "/home/user/.ssh/id_rsa")
    data.seek(0)
    _, summary = _zip_summary(data, ".zip")
    assert "links simbólicos declarados=1" in summary
    assert ".ssh" not in summary


@pytest.mark.parametrize("operation,phrase", [
    ("autocontrast", "autocontraste"),
    ("sepia", "sépia"),
    ("flip_horizontal", "espelhamento horizontal"),
    ("flip_vertical", "espelhamento vertical"),
    ("brighten", "clareamento"),
    ("contrast", "contraste"),
])
def test_new_photo_effects_match_current_chat_and_protect_original(
    tmp_path, operation, phrase,
):
    from PIL import Image
    ex, home, confirm = executor(tmp_path)
    original = home / "sample.png"
    image = Image.new("RGB", (12, 9), (40, 88, 130))
    image.putpixel((0, 0), (200, 25, 25))
    image.save(original)
    before = original.read_bytes()
    destination = home / (operation + ".png")
    msg = f"Edite a foto {original} em {phrase} e salve em {destination}"
    action = _simple_creative_request(json.dumps({
        "mensagem_atual": msg, "historico": [],
    }))
    assert action is not None and action[0] == "edit_image_local"
    assert action[1]["operation"] == operation
    result = ex.execute(action[0], **action[1])
    assert result.success
    assert confirm.calls == 1
    with Image.open(destination) as out:
        assert out.size == image.size and out.format == "PNG"
    assert original.read_bytes() == before
    assert os.stat(destination).st_mode & 0o777 == 0o600


def test_history_alone_never_authorizes_new_image_filter(tmp_path):
    path = tmp_path / "foo.png"
    result = _simple_creative_request(json.dumps({
        "mensagem_atual": "Explique sépia",
        "historico": [{"usuario": f"Edite a foto {path} em sépia e salve em {tmp_path / 'out.png'}"}],
    }))
    assert result is None


@pytest.mark.parametrize("source,output,kind", [
    ("photo.tiff", "photo.tif", "image"),
    ("paper.docx", "paper.odt", "document"),
    ("paper.rtf", "paper.pdf", "document"),
    ("paper.odt", "paper.rtf", "document"),
])
def test_new_craft_formats_recognized_in_text_chat(source, output, kind):
    phrase = f"Converta /home/usuario/Documentos/{source} em /home/usuario/Documentos/{output}"
    action = _simple_creative_request(json.dumps({"mensagem_atual": phrase, "historico": []}))
    assert action is not None
    assert action[0] == "craft_convert_local" and action[1]["kind"] == kind


@pytest.mark.parametrize("ext,data", [
    (".tif", b"II\x2a\x00" + b"x" * 16),
    (".tiff", b"MM\x00\x2a" + b"x" * 16),
    (".rtf", b"{\\rtf1\\ansi Sample}"),
    (".odt", b"PK\x03\x04" + b"X" * 20),
])
def test_new_conversion_outputs_require_expected_file_headers(ext, data):
    _validate_converted_output(data, ext)
    with pytest.raises(ValueError):
        _validate_converted_output(b"wrong bytes", ext)


def test_craft_optional_binary_missing_reports_error_without_creating_output(tmp_path, monkeypatch):
    ex, home, confirm = executor(tmp_path)
    source = home / "documento.rtf"
    source.write_bytes(b"{\\rtf1\\ansi User sample}")
    destination = home / "documento.odt"
    monkeypatch.setattr("nexus.tools.creative.shutil.which", lambda name: None)
    result = ex.execute("craft_convert_local", source=str(source),
                        output=str(destination), kind="document")
    assert not result.success
    assert "Mecanismo local para este formato não instalado" in (result.error or "")
    assert not destination.exists()
    assert confirm.calls == 1


def test_craft_document_conversion_passes_fixed_args_and_staged_output(tmp_path, monkeypatch):
    ex, home, _ = executor(tmp_path)
    input_path = home / "report.rtf"
    input_path.write_bytes(b"{\\rtf1\\ansi Sample}")
    output_path = home / "report.odt"
    calls = []
    def fake_run(args, **kw):
        calls.append(args)
        Path(args[3]).write_bytes(b"PK\x03\x04" + b"X" * 40)
        return SimpleNamespace(returncode=0)
    monkeypatch.setattr("nexus.tools.creative.shutil.which", lambda name: "/trusted/wordcraft-cli")
    monkeypatch.setattr("nexus.tools.creative.subprocess.run", fake_run)
    ok = ex.execute("craft_convert_local", source=str(input_path),
                    output=str(output_path), kind="document")
    assert ok.success
    assert calls[0][1] == "convert"
    assert Path(calls[0][2]).suffix == ".rtf"
    assert Path(calls[0][3]).suffix == ".odt"
    assert output_path.read_bytes().startswith(b"PK\x03\x04")
    assert not ex.execute("craft_convert_local", source=str(input_path),
                          output=str(output_path), kind="document").success


@pytest.mark.parametrize("name,data,kind", [
    ("picture.tif", b"II\x2a\x00" + b"\x00" * 16, "TIFF"),
    ("picture.tiff", b"MM\x00\x2a" + b"\x00" * 16, "TIFF"),
    ("picture.webp", b"RIFF\x04\x00\x00\x00WEBP", "WEBP"),
    ("animation.gif", b"GIF89a\x01\x00\x01\x00", "GIF"),
])
def test_static_image_signatures_are_structural_without_loading_images(name, data, kind):
    from nexus.tools.static_analysis import _identify
    reported_kind, summary = _identify(data, Path(name).suffix)
    assert reported_kind == kind
    assert "não analisado" in summary or "não analisados" in summary



@pytest.mark.parametrize("field,invalid", [
    ("entries", 3001), ("zip64", 65535), ("directory", 8 * 1024 * 1024 + 1),
])
def test_zip_preflight_denies_unbounded_indices_before_zipfile_parse(
    monkeypatch, field, invalid,
):
    import nexus.tools.static_analysis as static
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as z:
        z.writestr("small.txt", b"x")
    content = bytearray(buffer.getvalue())
    end = content.rfind(b"PK\x05\x06")
    assert end >= 0
    if field == "entries":
        struct.pack_into("<H", content, end + 8, invalid)
        struct.pack_into("<H", content, end + 10, invalid)
    elif field == "zip64":
        struct.pack_into("<H", content, end + 8, invalid)
        struct.pack_into("<H", content, end + 10, invalid)
    else:
        struct.pack_into("<I", content, end + 12, invalid)
    def forbidden(*a, **kw):
        pytest.fail("Central directory must be rejected before ZipFile allocation")
    monkeypatch.setattr(static.zipfile, "ZipFile", forbidden)
    with pytest.raises(ValueError):
        static._zip_summary(io.BytesIO(content), ".zip")


def test_zip_preflight_accepts_empty_and_normal_archives():
    from nexus.tools.static_analysis import _check_zip_directory_bounds
    for payloads in ([], [("a.txt", b"one"), ("b.txt", b"two")]):
        stream = io.BytesIO()
        with zipfile.ZipFile(stream, "w", compression=zipfile.ZIP_STORED) as z:
            for name, body in payloads:
                z.writestr(name, body)
        stream.seek(0)
        _check_zip_directory_bounds(stream)
        stream.seek(0)
        kind, summary = _zip_summary(stream, ".zip")
        assert kind == "ZIP"
        assert f"{len(payloads)} entradas" in summary
