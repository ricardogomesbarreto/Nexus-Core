"""Offline safeguards around the opt-in physical X11 acceptance script.

These tests do NOT certify any physical desktop, event injection or Tk widget.
"""
import subprocess
from types import SimpleNamespace

import pytest

from scripts import x11_manual_acceptance as acceptance


class Stream:
    def __init__(self, tty=True):
        self.tty = tty

    def isatty(self):
        return self.tty


def test_each_action_requires_explicit_terminal_confirmation():
    calls = []
    def permit(prompt):
        calls.append(prompt)
        return "AUTORIZO"
    assert acceptance._ask_consent(
        "DIGITAÇÃO", input_fn=permit, stream=Stream()
    ) is True
    assert acceptance._ask_consent(
        "UMA TECLA TAB", input_fn=permit, stream=Stream()
    ) is True
    assert len(calls) == 2
    assert calls[0] != calls[1]


@pytest.mark.parametrize("answer", ["", "sim", "autorizar", "AUTORIZO TUDO", " AUTORIZO NÃO"])
def test_non_exact_answers_are_denied(answer):
    assert acceptance._ask_consent(
        "DIGITAÇÃO", input_fn=lambda _: answer, stream=Stream()
    ) is False


def test_noninteractive_shell_never_gets_prompted():
    def must_not_ask(_):
        pytest.fail("Noninteractive script must refuse without prompting.")
    assert acceptance._ask_consent(
        "DIGITAÇÃO", input_fn=must_not_ask, stream=Stream(False)
    ) is False


def test_owned_disposable_window_is_selected_by_unique_title_and_pid(monkeypatch):
    calls = []
    class Backend:
        COMMAND_TIMEOUT = 5
        MAX_QUERY_BYTES = 4096
        def _command(self):
            return "/usr/bin/xdotool"
        def validate_id(self, ident):
            return ident
        def _identity(self, ident):
            assert ident == 123
            return "NEXUS-CORE-X11-HOMOLOG-abc", 445, "Tk"
    def run(command, **opts):
        calls.append((command, opts))
        return subprocess.CompletedProcess(command, 0, stdout=b"123\n")
    monkeypatch.setattr(acceptance.os, "getpid", lambda: 445)
    monkeypatch.setattr(acceptance.subprocess, "run", run)
    assert acceptance._test_window(
        Backend(), "NEXUS-CORE-X11-HOMOLOG-abc",
    ) == (123, "Tk")
    cmd, options = calls[0]
    assert cmd == [
        "/usr/bin/xdotool", "search", "--onlyvisible", "--pid", "445",
        "--name", "^NEXUS\\-CORE\\-X11\\-HOMOLOG\\-abc$",
    ]
    assert options["stdin"] == subprocess.DEVNULL
    assert options["stderr"] == subprocess.DEVNULL
    assert options.get("shell") is None
    assert options["timeout"] == 5


@pytest.mark.parametrize("response,pid,title", [
    (b"123\n456\n", 445, "NEXUS-CORE-X11-HOMOLOG-abc"),
    (b"123\n", 999, "NEXUS-CORE-X11-HOMOLOG-abc"),
    (b"123\n", 445, "Other"),
    (b"abc\n", 445, "NEXUS-CORE-X11-HOMOLOG-abc"),
])
def test_ambiguous_or_foreign_windows_fail_closed(monkeypatch, response, pid, title):
    class Backend:
        COMMAND_TIMEOUT = 5
        MAX_QUERY_BYTES = 4096
        def _command(self):
            return "/usr/bin/xdotool"
        def validate_id(self, ident):
            return ident
        def _identity(self, ident):
            return title, pid, "Tk"
    monkeypatch.setattr(acceptance.os, "getpid", lambda: 445)
    monkeypatch.setattr(acceptance.subprocess, "run", lambda cmd, **kw:
                        subprocess.CompletedProcess(cmd, 0, stdout=response))
    with pytest.raises(acceptance.AcceptanceError):
        acceptance._test_window(Backend(), "NEXUS-CORE-X11-HOMOLOG-abc")


def test_no_real_graphics_or_device_startup_when_x11_unavailable(monkeypatch, capsys):
    class NoX11:
        def _command(self):
            from nexus.automation import DesktopAutomationError
            raise DesktopAutomationError("Session not X11")
    monkeypatch.setattr(acceptance, "X11DesktopBackend", NoX11)
    assert acceptance.run() == 2
    assert "X11 local" in capsys.readouterr().out
