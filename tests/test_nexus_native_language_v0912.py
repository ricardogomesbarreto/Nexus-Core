"""External engine names stay in technical integration, never Nexus UI text."""

import contextlib
import io
import json
import re
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from nexus.agent import AgentOutcome
from nexus.desktop.conversation import ChatSession
from nexus.desktop.tool_labels import action_label
from nexus.desktop.window import DesktopWindow
from nexus.security import RiskLevel, SecurityRequest, SensitiveResource
from nexus.tools import PdfCombineTool, ToolResult
from nexus.tools.craft_capabilities import inspect_local_features
from nexus.tools.static_analysis import _identify
from nexus.updates.launcher import should_run_maintenance
from scripts import validate_craft_cli


FORBIDDEN = ("photocraft", "wordcraft", "pdfcraft")


def assert_nexus_language(value):
    text = str(value).lower()
    assert all(name not in text for name in FORBIDDEN)
    assert re.search(r"\brea\b", text) is None


def test_feature_check_shows_capabilities_without_backend_names():
    report = inspect_local_features(probe=lambda: {"tools": [
        {"status": "available", "binary": "photocraft-cli"},
        {"status": "missing", "binary": "wordcraft-cli"},
        {"status": "degraded", "binary": "pdfcraft-cli"},
    ]})
    assert report["features"] == [
        {"category": "imagens", "status": "anunciada"},
        {"category": "documentos", "status": "ausente"},
        {"category": "pdf", "status": "degradada"},
    ]
    assert report["real_operation_tested"] is False
    assert_nexus_language(json.dumps(report))
    assert not should_run_maintenance(["--feature-check"])


def test_feature_check_cli_does_not_start_the_application():
    from nexus import main
    report = {"schema": "nexus.local-features.v1", "features": []}
    output = io.StringIO()
    with patch.object(main, "build_application", side_effect=AssertionError("startup")), \
         patch("nexus.tools.craft_capabilities.inspect_local_features", return_value=report), \
         contextlib.redirect_stdout(output):
        main.cli(["--feature-check"])
    assert json.loads(output.getvalue()) == report


def test_diagnostic_output_and_file_inspection_use_nexus_language(monkeypatch, capsys):
    monkeypatch.setattr(validate_craft_cli.shutil, "which", lambda _: None)
    assert validate_craft_cli.run() == 1
    assert "area=pdf estado=ausente" in capsys.readouterr().out
    assert_nexus_language(_identify(b"%PDF-1.7\n", ".pdf"))
    assert_nexus_language(_identify(b"data", ".asar"))


def test_chat_and_permission_are_nexus_branded(monkeypatch):
    output = ChatSession._describe(AgentOutcome(True, tool_result=ToolResult(
        True, "pdf_combine_local", data={"path": "/home/user/saida.pdf"})))
    assert output == "Arquivo criado no computador: /home/user/saida.pdf"
    assert_nexus_language(output)
    failure = ChatSession._describe(AgentOutcome(False, tool_result=ToolResult(
        False, "craft_convert_local", error="Operação recusada")))
    assert failure == "Converter arquivo: Operação recusada"
    assert_nexus_language(failure)
    assert_nexus_language(PdfCombineTool.description)

    details = []

    class Dialog:
        def __init__(self, root, description, **kwargs):
            details.append(description)
            details.append(kwargs["spoken_question"])

        def ask(self):
            return False

    monkeypatch.setattr("nexus.desktop.window.PermissionDialog", Dialog)
    window = DesktopWindow.__new__(DesktopWindow)
    window.root = object()
    window.recognizer = None
    window._voice_active = False
    window._listening = False
    window._listen_pending_generations = set()
    window._closing = False
    window._cancel_requested = False
    window._start_worker = lambda target: None
    window.speaker = None
    window.speech_enabled = SimpleNamespace(get=lambda: False)
    window.voice_choice = SimpleNamespace(get=lambda: "Feminina")
    request = SecurityRequest(
        action="pdf_combine_local", description=PdfCombineTool.description,
        risk_level=RiskLevel.MEDIUM, tool_name="pdf_combine_local",
        resources=(SensitiveResource("source_a", "/home/user/a.pdf"),
                   SensitiveResource("source_b", "/home/user/b.pdf"),
                   SensitiveResource("output", "/home/user/junto.pdf")),
    )
    assert window._confirm(request) is False
    assert "Função Nexus Core: Juntar dois PDFs" in details[0]
    assert "Primeiro PDF: /home/user/a.pdf" in details[0]
    assert "Segundo PDF: /home/user/b.pdf" in details[0]
    assert "Arquivo de saída: /home/user/junto.pdf" in details[0]
    assert_nexus_language(details)


def test_quick_guide_uses_only_nexus_capability_names():
    messages = []
    window = DesktopWindow.__new__(DesktopWindow)
    window.root = object()
    window.messagebox = SimpleNamespace(showinfo=lambda *a, **kw: messages.append(a))
    window._show_quick_guide()
    assert len(messages) == 1 and "Nexus Core" in messages[0][0]
    assert_nexus_language(messages[0][1])


def test_project_readme_uses_nexus_capability_language():
    readme = (Path(__file__).resolve().parents[1] / "README.md").read_text()
    assert_nexus_language(readme)
