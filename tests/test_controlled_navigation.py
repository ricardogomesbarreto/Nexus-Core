"""v0.7.1: X11 navigation is one allowlisted key per human-approved call."""
from types import SimpleNamespace
import subprocess

import pytest

from nexus.automation import DesktopAutomationError, X11DesktopBackend
from nexus.core.application import NexusApplication
from nexus.desktop.window import DesktopWindow
from nexus.security import AuditLogger, RiskLevel, SecurityGate, SecurityRequest
from nexus.tools import DesktopNavigateTool, ToolExecutor, ToolRegistry


ALLOWED = {
    "next_field": "Tab",
    "previous_field": "ISO_Left_Tab",
    "page_up": "Prior",
    "page_down": "Next",
}


def x11(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":44")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)


@pytest.mark.parametrize("action,keysym", ALLOWED.items())
def test_navigation_sends_single_fixed_keysym(monkeypatch, action, keysym):
    x11(monkeypatch)
    calls = []

    def run(command, **kw):
        calls.append((command, kw))
        data = (
            b"Editor\n" if "getwindowname" in command else
            b"321\n" if "getwindowpid" in command else
            b"EditorClass\n" if "getwindowclassname" in command else b""
        )
        return subprocess.CompletedProcess(command, 0, stdout=data)

    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    result = X11DesktopBackend("/usr/bin/xdotool").navigate(
        window_id=12, window_title="Editor",
        window_pid=321, window_class="EditorClass", action=action,
    )
    assert result == action
    assert [c for c, _ in calls] == [
        ["/usr/bin/xdotool", "getwindowname", "12"],
        ["/usr/bin/xdotool", "getwindowpid", "12"],
        ["/usr/bin/xdotool", "getwindowclassname", "12"],
        ["/usr/bin/xdotool", "key", "--window", "12",
         "--clearmodifiers", "--", keysym],
    ]
    assert all(kw.get("shell") is None for _, kw in calls)
    assert all(kw["stdin"] == subprocess.DEVNULL for _, kw in calls)
    assert all(kw["timeout"] <= 5 for _, kw in calls)


@pytest.mark.parametrize("value", [
    None, 3, True, "", "Tab", "Return", "Enter", "Escape",
    "Ctrl+C", "ctrl+alt+Delete", "next_field page_down",
    "Next_Field", "a\n", "key", "--window",
])
def test_navigation_rejects_all_unlisted_input(value):
    with pytest.raises(DesktopAutomationError, match="Navegação inválida"):
        X11DesktopBackend.validate_navigation(value)


def test_renamed_window_blocks_navigation_before_keypress(monkeypatch):
    x11(monkeypatch)
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0, stdout=b"Other editor\n")

    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    with pytest.raises(DesktopAutomationError, match="mudou"):
        X11DesktopBackend("/usr/bin/xdotool").navigate(
            window_id=17, window_title="Editor",
            window_pid=321, window_class="EditorClass", action="page_down",
        )
    assert calls == [["/usr/bin/xdotool", "getwindowname", "17"]]


@pytest.mark.parametrize("wayland,display", [
    (True, ":9"), (False, ""), (False, "example.org:0"),
])
def test_unsupported_sessions_refuse_navigation(monkeypatch, wayland, display):
    monkeypatch.setenv("DISPLAY", display)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    if wayland:
        monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    else:
        monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.setattr("nexus.automation.x11.subprocess.run",
                        lambda *a, **kw: pytest.fail("Must not launch subprocess"))
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend("/usr/bin/xdotool").navigate(
            window_id=12, window_title="Editor",
            window_pid=321, window_class="EditorClass", action="next_field",
        )


@pytest.mark.parametrize("mode", ["failure", "timeout"])
def test_failed_navigation_never_claims_success(monkeypatch, mode):
    x11(monkeypatch)
    def run(cmd, **kw):
        if "getwindowname" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"Editor\n")
        if "getwindowpid" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"321\n")
        if "getwindowclassname" in cmd:
            return subprocess.CompletedProcess(cmd, 0, stdout=b"EditorClass\n")
        if mode == "timeout":
            raise subprocess.TimeoutExpired(cmd, 5, output=b"sensitive")
        return subprocess.CompletedProcess(cmd, 1)
    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    with pytest.raises(DesktopAutomationError) as caught:
        X11DesktopBackend("/usr/bin/xdotool").navigate(
            window_id=12, window_title="Editor",
            window_pid=321, window_class="EditorClass", action="previous_field",
        )
    assert "sensitive" not in str(caught.value)


class Backend:
    def __init__(self):
        self.actions = []
        self.deny = False

    def navigate(self, *, window_id, window_title, window_pid, window_class, action):
        if self.deny:
            raise DesktopAutomationError("Janela não está disponível.")
        self.actions.append((window_id, window_title, window_pid, window_class, action))
        return action


class Consent:
    def __init__(self, allowed):
        self.allowed = allowed
        self.requests = []

    def confirm(self, req):
        self.requests.append(req)
        return self.allowed


def executor(tmp_path, consent):
    registry = ToolRegistry()
    backend = Backend()
    registry.register(DesktopNavigateTool(backend))
    gate = SecurityGate(audit_logger=AuditLogger(tmp_path / "navigation.log"))
    return ToolExecutor(registry, gate, confirmation_handler=consent), backend


def test_registered_app_exposes_only_enumerated_navigation():
    app = NexusApplication(SimpleNamespace())
    c = {t["name"]: t for t in app.tool_registry.contracts()}
    assert app.tool_registry.exists("desktop_navigate")
    assert c["desktop_navigate"]["permission"] == "MEDIUM"
    assert c["desktop_navigate"]["inputs"]["required"] == [
        "window_id", "window_title", "window_pid", "window_class", "action",
    ]
    assert "keys" not in c["desktop_navigate"]["inputs"]["properties"]


def test_no_confirmation_means_no_navigation(tmp_path):
    for consent in (None, Consent(False), Consent("sim")):
        tool, backend = executor(tmp_path, consent)
        response = tool.execute(
            "desktop_navigate", window_id=12,
            window_title="Editor", window_pid=321, window_class="EditorClass", action="next_field",
        )
        assert not response.success
        assert backend.actions == []


def test_each_single_navigation_requires_a_separate_consent(tmp_path):
    consent = Consent(True)
    tool, backend = executor(tmp_path, consent)
    for action in ALLOWED:
        reply = tool.execute(
            "desktop_navigate", window_id=12,
            window_title="Editor", window_pid=321, window_class="EditorClass", action=action,
        )
        assert reply.success
        assert reply.data == {"window_id": 12, "action": action}
    assert len(consent.requests) == len(ALLOWED)
    assert [action[-1] for action in backend.actions] == list(ALLOWED)
    assert all(req.risk_level == RiskLevel.MEDIUM for req in consent.requests)


@pytest.mark.parametrize("bad", [
    "Tab", "Control_L+c", "Return", "next_field next_field", "",
])
def test_rejected_shortcuts_never_reach_confirmation_or_backend(tmp_path, bad):
    consent = Consent(True)
    tool, backend = executor(tmp_path, consent)
    reply = tool.execute(
        "desktop_navigate", window_id=12, window_title="Editor", window_pid=321, window_class="EditorClass", action=bad,
    )
    assert not reply.success
    assert reply.error_code in ("INVALID_RESOURCES", "INVALID_INPUT")
    assert consent.requests == []
    assert backend.actions == []


def test_backend_failures_return_denial_and_audit(tmp_path):
    consent = Consent(True)
    tool, backend = executor(tmp_path, consent)
    backend.deny = True
    result = tool.execute(
        "desktop_navigate", window_id=12, window_title="Editor",
        action="page_up",
    )
    assert not result.success
    assert result.error_code == "DESKTOP_DENIED"
    assert "OUTCOME=ERROR" in (tmp_path / "navigation.log").read_text()


def test_gui_confirmation_previews_exact_navigation():
    window = object.__new__(DesktopWindow)
    captured = []
    window.root = object()
    window.messagebox = SimpleNamespace(
        askyesno=lambda heading, message, **kw:
        captured.append((heading, message)) or True
    )
    request = SecurityRequest(
        action="desktop_navigate", description="Navegar uma tecla",
        risk_level=RiskLevel.MEDIUM, tool_name="desktop_navigate",
        data={"window_id": 12, "window_title": "Notas",
              "window_pid": 321, "window_class": "NotesClass",
              "action": "page_down"},
    )
    assert window._confirm(request) is True
    assert len(captured) == 1
    assert "Notas" in captured[0][1]
    assert "12" in captured[0][1]
    assert "page_down" in captured[0][1]
    assert "321" in captured[0][1]
    assert "NotesClass" in captured[0][1]


def test_injected_extra_key_is_rejected_by_contract(tmp_path):
    confirm = Consent(True)
    tool, backend = executor(tmp_path, confirm)
    response = tool.execute(
        "desktop_navigate", window_id=12, window_title="Editor",
        action="next_field", repeat=5,
    )
    assert not response.success
    assert response.error_code == "INVALID_INPUT"
    assert not confirm.requests
    assert not backend.actions
