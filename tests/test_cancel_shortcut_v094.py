"""v0.9.4: keyboard cancellation follows the existing button semantics."""
import time
from threading import Event

from nexus.agent import AgentOutcome

from test_multimodal_privacy_status_v090 import desktop, spin, ui_labels


def test_cancel_shortcut_is_inert_when_idle(desktop):
    root, window, app, vision = desktop
    assert root.bind("<Control-Shift-X>")
    window.input.insert("1.0", "Texto ainda não enviado")

    assert window._shortcut_cancel_current() == "break"
    assert window.input.get("1.0", "end-1c") == "Texto ainda não enviado"
    assert not window._cancel_requested
    assert app.agent.calls == []
    assert vision.captures == 0


def test_shortcut_cancels_pending_chat_once(desktop, monkeypatch):
    root, window, app, vision = desktop
    started = Event()

    class WaitingAgent:
        def run(self, prompt, is_cancelled=None):
            started.set()
            while not is_cancelled():
                time.sleep(0.01)
            return AgentOutcome(False, error_code="CANCELLED")

    app.agent = window.session.agent = WaitingAgent()
    window.speech_enabled.set(False)
    cancels = []
    original_cancel = window.confirmation.cancel_pending

    def cancel_pending():
        cancels.append(True)
        return original_cancel()

    monkeypatch.setattr(window.confirmation, "cancel_pending", cancel_pending)
    window.input.insert("1.0", "Pergunta que aguarda resposta")
    window._send()
    spin(root, started.is_set)

    assert window._shortcut_cancel_current() == "break"
    assert window._shortcut_cancel_current() == "break"
    assert cancels == [True]
    assert window.cancel_button.instate(("disabled",))
    spin(root, lambda: not window._busy)
    assert "Solicitação cancelada." in window.transcript.get("1.0", "end")
    assert vision.captures == 0


def test_shortcut_marks_authorized_visual_work_as_cancellation_requested(
    desktop, monkeypatch,
):
    from tkinter import simpledialog

    root, window, app, vision = desktop
    monkeypatch.setattr(simpledialog, "askstring", lambda *args, **kw: "O que aparece?")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *args, **kw: True)
    window._vision_screen()
    spin(root, vision.entered.is_set)

    assert window._shortcut_cancel_current() == "break"
    assert ui_labels(window)[2] == "Visão: cancelamento solicitado"
    assert vision.captures == 1
    vision.release.set()
    spin(root, lambda: not window._busy)
    assert "Análise visual cancelada." in window.transcript.get("1.0", "end")
    assert ui_labels(window)[2] == "Visão: sem captura"
    assert app.agent.calls == []
