"""Desktop tools must be mediated and fail closed without explicit consent."""
import json
from types import SimpleNamespace

import pytest

from nexus.core.application import NexusApplication
from nexus.security import AuditLogger, SecurityGate
from nexus.tools import (
    DesktopTypeTextTool, DesktopWindowInfoTool,
    ToolExecutor, ToolRegistry,
)
from nexus.automation import DesktopAutomationError


class Backend:
    def __init__(self):
        self.calls = []
        self.title = "Notas"
        self.window_id = 155
        self.denied = False

    def active_window(self):
        self.calls.append(("inspect",))
        if self.denied:
            raise DesktopAutomationError("Display X11 indisponível.")
        return self.window_id, self.title

    def type_text(self, *, window_id, window_title, text):
        self.calls.append(("type", window_id, window_title, text))
        if self.denied:
            raise DesktopAutomationError("Falha X11.")
        return len(text)


class Consent:
    def __init__(self, approve, callback=None):
        self.approve = approve
        self.callback = callback
        self.requests = []

    def confirm(self, request):
        self.requests.append(request)
        if self.callback is not None:
            self.callback()
        return self.approve


def setup_tools(tmp_path, *, consent=None, backend=None):
    backend = backend or Backend()
    registry = ToolRegistry()
    registry.register(DesktopWindowInfoTool(backend))
    registry.register(DesktopTypeTextTool(backend))
    gate = SecurityGate(audit_logger=AuditLogger(tmp_path / "desktop-audit.log"))
    executor = ToolExecutor(registry, gate, confirmation_handler=consent)
    return executor, backend


def test_app_registers_both_desktop_actions():
    # No database or service startup needed to enumerate built-in tools.
    app = NexusApplication(SimpleNamespace())
    assert app.tool_registry.exists("desktop_window_info")
    assert app.tool_registry.exists("desktop_type_text")
    contracts = {x["name"]: x for x in app.tool_registry.contracts()}
    assert contracts["desktop_type_text"]["permission"] == "MEDIUM"
    assert contracts["desktop_window_info"]["permission"] == "LOW"
    assert contracts["desktop_type_text"]["inputs"]["required"] == [
        "window_id", "window_title", "text",
    ]


def test_read_only_window_inspection_returns_bounded_metadata(tmp_path):
    executor, backend = setup_tools(tmp_path)
    response = executor.execute("desktop_window_info")
    assert response.success is True
    assert response.data == {"window_id": 155, "window_title": "Notas"}
    assert backend.calls == [("inspect",)]


def test_typing_requires_fresh_approval_per_operation(tmp_path):
    confirm = Consent(True)
    executor, backend = setup_tools(tmp_path, consent=confirm)
    for _ in range(2):
        result = executor.execute("desktop_type_text",
                                  window_id=155, window_title="Notas",
                                  text="Olá")
        assert result.success is True
        assert result.data == {"window_id": 155, "sent_characters": 3}
    assert len(confirm.requests) == 2
    assert len([call for call in backend.calls if call[0] == "type"]) == 2
    assert all(req.risk_level.name == "MEDIUM" for req in confirm.requests)


@pytest.mark.parametrize("consent", [None, Consent(False), Consent("sim")])
def test_missing_false_or_nonboolean_confirmation_blocks_typing(tmp_path, consent):
    executor, backend = setup_tools(tmp_path, consent=consent)
    response = executor.execute("desktop_type_text",
                                window_id=155, window_title="Notas", text="Abc")
    assert not response.success
    assert not backend.calls
    assert response.error_code in ("CONFIRMATION_REQUIRED", "CONFIRMATION_REJECTED")


@pytest.mark.parametrize("arguments", [
    {"window_id": 0, "window_title": "Notas", "text": "ok"},
    {"window_id": 155, "window_title": "Notas", "text": "ls\n"},
    {"window_id": 155, "window_title": "Notas", "text": "x" * 301},
    {"window_id": 155, "window_title": "Notas\n", "text": "ok"},
    {"window_id": 155, "window_title": "Notas", "text": ""},
    {"window_id": 155, "window_title": "Notas", "text": "ok", "extra": 1},
])
def test_invalid_model_tool_calls_are_denied_before_consent(tmp_path, arguments):
    consent = Consent(True)
    executor, backend = setup_tools(tmp_path, consent=consent)
    result = executor.execute("desktop_type_text", **arguments)
    assert not result.success
    assert not backend.calls
    assert not consent.requests
    assert result.error_code in ("INVALID_INPUT", "INVALID_RESOURCES")


def test_invalid_window_after_confirmation_fails_without_claiming_typing(tmp_path):
    backend = Backend()
    def change():
        backend.denied = True
    consent = Consent(True, callback=change)
    executor, backend = setup_tools(tmp_path, consent=consent, backend=backend)
    result = executor.execute("desktop_type_text",
                              window_id=155, window_title="Notas", text="xyz")
    assert not result.success
    assert result.error_code == "DESKTOP_DENIED"
    assert "OUTCOME=ERROR" in (tmp_path / "desktop-audit.log").read_text()


def test_tool_execution_never_leaks_text_into_result(tmp_path):
    executor, backend = setup_tools(tmp_path, consent=Consent(True))
    result = executor.execute("desktop_type_text", window_id=155,
                              window_title="Notas", text="not my password")
    assert result.success
    assert "not my password" not in json.dumps(result.as_dict())


def test_sensitive_desktop_call_does_not_use_unsafe_low_risk_bypass(tmp_path):
    executor, backend = setup_tools(tmp_path)
    safe = executor.execute("desktop_window_info")
    dangerous = executor.execute("desktop_type_text",
                                 window_id=155, window_title="Notas", text="A")
    assert safe.success
    assert not dangerous.success
    assert not any(c[0] == "type" for c in backend.calls)
