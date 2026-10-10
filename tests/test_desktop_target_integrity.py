"""v0.7.3: actions fail closed if X11 target identity changes after consent."""
import subprocess
from types import SimpleNamespace

import pytest

from nexus.automation import DesktopAutomationError, X11DesktopBackend
from nexus.security import AuditLogger, SecurityGate
from nexus.tools import DesktopNavigateTool, DesktopTypeTextTool, ToolExecutor, ToolRegistry


def local_x11(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":77")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)


def fake_xdotool(monkeypatch, *, title=b"Editor\n", pid=b"2233\n",
                 window_class=b"EditorApp\n", pid_status=0):
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        if "getactivewindow" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"42\n")
        if "getwindowname" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=title)
        if "getwindowpid" in cmd:
            return subprocess.CompletedProcess(cmd, pid_status, stdout=pid)
        if "getwindowclassname" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=window_class)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"")

    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    return calls


def test_inspection_returns_exact_identity_for_later_authorization(monkeypatch):
    local_x11(monkeypatch)
    calls = fake_xdotool(monkeypatch)
    result = X11DesktopBackend("/usr/bin/xdotool").active_window()
    assert result == (42, "Editor", 2233, "EditorApp")
    assert [x[1] for x in calls] == [
        "getactivewindow", "getwindowname", "getwindowpid",
        "getwindowclassname",
    ]


@pytest.mark.parametrize("changed", [
    {"title": b"Another\n"},
    {"pid": b"2234\n"},
    {"window_class": b"DifferentApp\n"},
    {"pid": b""},
    {"pid": b"not-a-pid\n"},
    {"pid_status": 1},
    {"window_class": b""},
])
@pytest.mark.parametrize("operation", ["type_text", "navigate"])
def test_changed_or_missing_identity_never_sends_keys(monkeypatch, changed, operation):
    local_x11(monkeypatch)
    calls = fake_xdotool(monkeypatch, **changed)
    backend = X11DesktopBackend("/usr/bin/xdotool")
    arguments = dict(
        window_id=42, window_title="Editor", window_pid=2233,
        window_class="EditorApp",
    )
    if operation == "type_text":
        arguments["text"] = "abc"
    else:
        arguments["action"] = "next_field"
    with pytest.raises(DesktopAutomationError):
        getattr(backend, operation)(**arguments)
    assert not any("key" in cmd or "type" in cmd for cmd in calls)


@pytest.mark.parametrize("pid", [0, -1, 2**31, True, "2233", None])
def test_invalid_pid_is_rejected(pid):
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend.validate_pid(pid)


@pytest.mark.parametrize("window_class", ["", "  ", "App\n", "\x00", "a" * 129, None])
def test_invalid_class_is_rejected(window_class):
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend.validate_class(window_class)


class Confirm:
    def __init__(self):
        self.requests = []

    def confirm(self, request):
        self.requests.append(request)
        return True


def test_legacy_action_without_pid_class_denied_before_confirmation(tmp_path):
    registry = ToolRegistry()
    registry.register(DesktopTypeTextTool(backend=SimpleNamespace()))
    registry.register(DesktopNavigateTool(backend=SimpleNamespace()))
    confirm = Confirm()
    gate = SecurityGate(audit_logger=AuditLogger(tmp_path / "desktop.log"))
    executor = ToolExecutor(registry, gate, confirmation_handler=confirm)
    for tool, extra in (
        ("desktop_type_text", {"text": "abc"}),
        ("desktop_navigate", {"action": "page_down"}),
    ):
        result = executor.execute(
            tool, window_id=42, window_title="Editor", **extra
        )
        assert not result.success
        assert result.error_code == "INVALID_INPUT"
    assert confirm.requests == []
