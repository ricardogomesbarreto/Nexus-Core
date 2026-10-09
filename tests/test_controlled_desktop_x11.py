"""X11 automation is one-shot, window-bound and never uses a shell."""
import os
import subprocess

import pytest

from nexus.automation import DesktopAutomationError, X11DesktopBackend, desktop_capabilities


@pytest.mark.parametrize("variables", [
    {},
    {"DISPLAY": ":1", "WAYLAND_DISPLAY": "wayland-0"},
    {"DISPLAY": ":1", "XDG_SESSION_TYPE": "wayland"},
])
def test_unsupported_graphics_session_fails_closed(monkeypatch, variables):
    for key in ("DISPLAY", "WAYLAND_DISPLAY", "XDG_SESSION_TYPE"):
        monkeypatch.delenv(key, raising=False)
    for key, value in variables.items():
        monkeypatch.setenv(key, value)
    monkeypatch.setattr("nexus.automation.x11.shutil.which",
                        lambda _: pytest.fail("Do not query X11 binary"))
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend().active_window()


def test_missing_xdotool_is_reported_without_display_access(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.setattr("nexus.automation.x11.shutil.which", lambda _: None)
    with pytest.raises(DesktopAutomationError, match="xdotool"):
        X11DesktopBackend().active_window()


class FakeProcess:
    def __init__(self, data=b"", rc=0):
        self.stdout = data
        self.returncode = rc


def test_active_window_queries_fixed_binary_without_shell(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    calls = []

    def run(cmd, **kw):
        calls.append((cmd, kw))
        return FakeProcess(b"120\n" if "getactivewindow" in cmd else b"Editor \xe2\x80\x94 Teste\n")

    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    backend = X11DesktopBackend("/usr/bin/xdotool")
    assert backend.active_window() == (120, "Editor — Teste")
    assert [cmd for cmd, _ in calls] == [
        ["/usr/bin/xdotool", "getactivewindow"],
        ["/usr/bin/xdotool", "getwindowname", "120"],
    ]
    assert all(kw.get("shell") is None for _, kw in calls)
    assert all(kw["stdin"] == subprocess.DEVNULL for _, kw in calls)
    assert all(kw["timeout"] == backend.COMMAND_TIMEOUT for _, kw in calls)


def test_typing_uses_one_explicit_window_without_enter_or_shell(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    calls = []

    def run(cmd, **kw):
        calls.append((cmd, kw))
        if "getactivewindow" in cmd:
            return FakeProcess(b"88\n")
        if "getwindowname" in cmd:
            return FakeProcess("Notas\n".encode("utf-8"))
        return FakeProcess()

    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    backend = X11DesktopBackend("/usr/bin/xdotool")
    assert backend.type_text(window_id=88, window_title="Notas",
                             text="Olá, minha anotação.") == 20
    assert calls[-1][0] == [
        "/usr/bin/xdotool", "type", "--window", "88", "--clearmodifiers",
        "--delay", "2", "--", "Olá, minha anotação.",
    ]
    assert calls[-1][1].get("shell") is None
    assert calls[-1][1]["timeout"] == backend.TYPE_TIMEOUT


@pytest.mark.parametrize("window_id,title", [
    (12, "Janela antiga"), (13, "Janela atual"),
])
def test_focus_or_title_changed_prevents_typing(monkeypatch, window_id, title):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    calls = []

    def run(cmd, **kw):
        calls.append(cmd)
        return FakeProcess(b"12\n" if "getactivewindow" in cmd else b"Janela atual\n")

    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    with pytest.raises(DesktopAutomationError, match="mudou"):
        X11DesktopBackend("/usr/bin/xdotool").type_text(
            window_id=window_id, window_title=title, text="teste"
        )
    assert not any("type" in cmd for cmd in calls)


@pytest.mark.parametrize("data", [
    "", " \t", "abc\nxyz", "abc\rxyz", "abc\txyz", "\x00",
    "x" * 301, "abc\x1b", "ok\u202eegnahc",
])
def test_forbidden_characters_or_long_text_are_rejected(data):
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend.validate_text(data)


@pytest.mark.parametrize("identifier", [-1, 0, True, "12", 2**32, 4.5, None])
def test_invalid_window_ids_are_rejected(identifier):
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend.validate_id(identifier)


@pytest.mark.parametrize("title", ["", " ", "Editor\n", "x" * 201, "teste\x00"])
def test_invalid_window_title_is_rejected(title):
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend.validate_title(title)


@pytest.mark.parametrize("data", [b"abc\n", b"9999999999999\n", b"n/a\n"])
def test_untrusted_window_identifiers_fail_closed(monkeypatch, data):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.setattr("nexus.automation.x11.subprocess.run",
                        lambda cmd, **kw: FakeProcess(data))
    with pytest.raises(DesktopAutomationError):
        X11DesktopBackend("/usr/bin/xdotool").active_window()


def test_subprocess_timeouts_are_sanitized(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    def timeout(cmd, **kw):
        raise subprocess.TimeoutExpired(cmd=cmd, timeout=1, output=b"secret")

    monkeypatch.setattr("nexus.automation.x11.subprocess.run", timeout)
    with pytest.raises(DesktopAutomationError) as error:
        X11DesktopBackend("/usr/bin/xdotool").active_window()
    assert "secret" not in str(error.value)


def test_failed_typing_does_not_claim_success(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    def run(cmd, **kw):
        if "getactivewindow" in cmd:
            return FakeProcess(b"15\n")
        if "getwindowname" in cmd:
            return FakeProcess(b"Notes\n")
        return FakeProcess(rc=1)
    monkeypatch.setattr("nexus.automation.x11.subprocess.run", run)
    with pytest.raises(DesktopAutomationError, match="parcialmente"):
        X11DesktopBackend("/usr/bin/xdotool").type_text(
            window_id=15, window_title="Notes", text="value"
        )


def test_capability_check_does_not_open_X11(monkeypatch):
    monkeypatch.setenv("DISPLAY", ":1")
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    monkeypatch.delenv("XDG_SESSION_TYPE", raising=False)
    monkeypatch.setattr("nexus.automation.x11.shutil.which", lambda _: None)
    monkeypatch.setattr("nexus.automation.x11.subprocess.run",
                        lambda *a, **kw: pytest.fail("Probe must not access desktop"))
    result = desktop_capabilities()
    assert result["session_x11"] is True
    assert result["xdotool"] is False
    assert result["wayland_supported"] is False
    assert result["camera_access"] is False
