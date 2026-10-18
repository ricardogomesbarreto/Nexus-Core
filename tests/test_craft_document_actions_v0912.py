"""Typed local document actions based on the two original Craft CLI contracts."""

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from nexus.agent.planner import _simple_creative_request
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import CraftConvertTool, PdfExtractTool, ToolExecutor, ToolRegistry
from nexus.tools.pdf_extract import _page_selection, _validate_pdf_copy
from scripts.validate_craft_cli import _write_pdf


class Confirmation:
    def __init__(self, approve=True):
        self.approve = approve
        self.calls = []

    def confirm(self, request):
        self.calls.append(request)
        return self.approve


def setup(tmp_path, approve=True):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    registry = ToolRegistry()
    registry.register(CraftConvertTool())
    registry.register(PdfExtractTool())
    confirmation = Confirmation(approve)
    executor = ToolExecutor(registry, SecurityGate(path_security=policy,
                            audit_logger=AuditLogger(tmp_path / "audit.log")), confirmation)
    return executor, home, confirmation


@pytest.mark.parametrize("bad", ["", "0", "01", "1,1", "2-1", "1-5000", "5001", "--out", "1, 2", "1-20,21", "1-3,3-4"])
def test_pages_fail_closed(bad):
    with pytest.raises(ValueError):
        _page_selection(bad)


def test_page_selection_and_pdf_floor(tmp_path):
    assert _page_selection("1,3-5") == ("1,3-5", 4)
    pdf = tmp_path / "valid.pdf"
    _write_pdf(pdf)
    _validate_pdf_copy(pdf.read_bytes())
    for bad in (b"%PDF-1.7\nnot a pdf", pdf.read_bytes()[:-10], b"<html>error</html>"):
        with pytest.raises(ValueError):
            _validate_pdf_copy(bad)


def test_extract_uses_exact_pages_and_new_file_after_consent(tmp_path, monkeypatch):
    executor, home, approval = setup(tmp_path, approve=False)
    source = home / "relatorio.pdf"
    _write_pdf(source)
    original = source.read_bytes()
    output = home / "selecionadas.pdf"
    calls = []

    def fake_run(argv, **kwargs):
        calls.append((argv, kwargs))
        assert argv[0:2] == ["/usr/bin/pdfcraft-cli", "extract"]
        assert argv[3:5] == ["--pages", "1"]
        assert argv[5] == "--out"
        assert Path(argv[2]).read_bytes() == original
        _write_pdf(Path(argv[6]))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.pdf_extract.shutil.which", lambda _: "/usr/bin/pdfcraft-cli")
    monkeypatch.setattr("nexus.tools.pdf_extract.subprocess.run", fake_run)
    args = {"source": str(source), "output": str(output), "pages": "1"}
    assert not executor.execute("pdf_extract_pages_local", **args).success
    assert not calls
    approval.approve = True
    result = executor.execute("pdf_extract_pages_local", **args)
    assert result.success and result.data == {"path": str(output), "page_count": 1}
    assert len(calls) == 1 and source.read_bytes() == original
    assert output.stat().st_mode & 0o777 == 0o600
    assert not executor.execute("pdf_extract_pages_local", **args).success
    assert len(approval.calls) == 3


def test_extract_rejects_symlink_output_and_malformed_cli_result(tmp_path, monkeypatch):
    executor, home, _ = setup(tmp_path)
    source = home / "relatorio.pdf"
    _write_pdf(source)
    outside = home / "segredo.pdf"
    _write_pdf(outside)

    def fake_run(argv, **kwargs):
        Path(argv[6]).symlink_to(outside)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.pdf_extract.shutil.which", lambda _: "/usr/bin/pdfcraft-cli")
    monkeypatch.setattr("nexus.tools.pdf_extract.subprocess.run", fake_run)
    output = home / "nao-gerar.pdf"
    result = executor.execute("pdf_extract_pages_local", source=str(source),
                              output=str(output), pages="1")
    assert not result.success and not output.exists()
    assert outside.read_bytes() == source.read_bytes()


def test_wordcraft_text_uses_bounded_stdout_and_preserves_original(tmp_path, monkeypatch):
    executor, home, approval = setup(tmp_path)
    source = home / "rascunho.docx"
    source.write_bytes("documento sintético".encode())
    output = home / "texto.txt"
    script = tmp_path / "wordcraft-cli"
    script.write_text("#!/usr/bin/env python3\n"
                      "import sys, pathlib\n"
                      "assert len(sys.argv) == 3 and sys.argv[1] == 'text'\n"
                      "assert pathlib.Path(sys.argv[2]).is_file()\n"
                      "print('Conteúdo extraído localmente')\n")
    script.chmod(0o700)
    monkeypatch.setattr("nexus.tools.creative.shutil.which", lambda _: str(script))
    result = executor.execute("craft_convert_local", source=str(source),
                              output=str(output), kind="document_text")
    assert result.success and output.read_text().strip() == "Conteúdo extraído localmente"
    assert source.read_bytes() == "documento sintético".encode()
    assert output.stat().st_mode & 0o777 == 0o600 and len(approval.calls) == 1


def test_wordcraft_excessive_output_is_rejected_before_commit(tmp_path, monkeypatch):
    executor, home, _ = setup(tmp_path)
    source = home / "rascunho.docx"
    source.write_bytes(b"doc")
    script = tmp_path / "wordcraft-cli"
    script.write_text("#!/usr/bin/env python3\nprint('X' * 65536)\n")
    script.chmod(0o700)
    monkeypatch.setattr("nexus.tools.creative.shutil.which", lambda _: str(script))
    monkeypatch.setattr("nexus.tools.creative._MAX_OUTPUT", 1024)
    output = home / "texto.txt"
    assert not executor.execute("craft_convert_local", source=str(source),
                                output=str(output), kind="document_text").success
    assert not output.exists()


@pytest.mark.parametrize("utterance,name,extra", [
    ("Extraia o texto do documento /home/usuario/relatorio.docx em /home/usuario/texto.txt",
     "craft_convert_local", {"kind": "document_text"}),
    ("Extraia as páginas 1,3-5 do PDF /home/usuario/a.pdf em /home/usuario/parte.pdf",
     "pdf_extract_pages_local", {"pages": "1,3-5"}),
])
def test_only_current_explicit_turn_routes(utterance, name, extra):
    action = _simple_creative_request(json.dumps({"mensagem_atual": utterance, "historico": []}))
    assert action is not None and action[0] == name
    assert all(action[1][key] == val for key, val in extra.items())
    assert _simple_creative_request(json.dumps({"mensagem_atual": "Oi", "historico": [utterance]})) is None
