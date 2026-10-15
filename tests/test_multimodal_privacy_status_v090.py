"""v0.9.0 — Honest status presentation without permission escalation."""
import os
from threading import Event
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.multimodal_status import MultimodalStatus


def snapshot(**overrides):
    fields = dict(
        listening_allowed=True, listening_requested=False,
        speech_enabled=True, speech_requested=False,
    )
    fields.update(overrides)
    return MultimodalStatus(**fields)


def test_software_state_never_claims_physical_hardware_verified():
    labels = snapshot().labels()
    assert labels == (
        "Escuta: aguardando", "Voz: habilitada", "Visão: sem captura",
    )
    assert not any("microfone testado" in text.lower() for text in labels)


@pytest.mark.parametrize("kwargs, expected", [
    ({"listening_allowed": False, "listening_requested": False}, "Escuta: pausada"),
    ({"listening_allowed": False, "listening_requested": True}, "Escuta: pausada"),
    ({"listening_requested": True}, "Escuta: solicitada"),
    ({"speech_enabled": False, "speech_requested": True}, "Voz: desativada"),
    ({"speech_requested": True}, "Voz: saída solicitada"),
])
def test_voice_status_is_explicit_and_bounded(kwargs, expected):
    labels = snapshot(**kwargs).labels()
    assert expected in labels


@pytest.mark.parametrize("source, expected", [
    ("camera", "Visão: processando câmera"),
    ("screen", "Visão: processando tela"),
    ("file", "Visão: processando imagem"),
    ("unknown", "Visão: processando visual"),
])
def test_visual_source_does_not_expose_user_provided_identifiers(source, expected):
    assert snapshot(vision_busy=True, vision_source=source).labels()[2] == expected


def test_visual_source_requires_busy_authorized_state_to_appear():
    state = snapshot(vision_source="camera", vision_busy=False)
    assert state.labels()[2] == "Visão: sem captura"


def test_cancellation_is_not_falsely_reported_as_capture_stopped():
    assert snapshot(
        vision_busy=True, vision_source="camera", cancellation_requested=True,
    ).labels()[2] == "Visão: cancelamento solicitado"


def test_closing_state_does_not_claim_hardware_is_inactive():
    assert snapshot(closing=True).labels() == (
        "Escuta: encerrando", "Voz: encerrando", "Visão: encerrando",
    )


class FakeAgent:
    def __init__(self):
        self.calls = []

    def run(self, prompt, is_cancelled=None, allow_tools=True):
        self.calls.append(prompt)
        return AgentOutcome(True, content="Resposta local")


class FakeApplication:
    def __init__(self):
        self.agent = FakeAgent()
        self.closed = False

    def shutdown(self):
        self.closed = True


class FakeRecognizer:
    def recognize_continuous(self, cancelled):
        while not cancelled():
            time.sleep(0.01)
        return ""

    def stop(self):
        pass


class FakeSpeaker:
    def speak(self, text, voice):
        pass

    def stop(self):
        pass


class BlockingVision:
    def __init__(self):
        self.entered = Event()
        self.release = Event()
        self.captures = 0

    def screen(self):
        self.captures += 1
        self.entered.set()
        self.release.wait(timeout=4)
        return b"ephemeral-private-image"

    def describe(self, image, *, question):
        return {"description": "Análise local de teste"}


def spin(root, predicate, timeout=5):
    deadline = time.monotonic() + timeout
    while not predicate() and time.monotonic() < deadline:
        root.update()
        time.sleep(0.01)
    assert predicate()


@pytest.fixture
def desktop():
    if not os.environ.get("DISPLAY"):
        pytest.skip("Requer display virtual Linux")
    import tkinter as tk

    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = FakeApplication()
    vision = BlockingVision()
    window = DesktopWindow(
        root, app, confirmation,
        speaker=FakeSpeaker(), recognizer=FakeRecognizer(), vision=vision,
    )
    yield root, window, app, vision
    vision.release.set()
    if not app.closed:
        window._close()
        spin(root, lambda: app.closed)
    confirmation.close()
    try:
        root.destroy()
    except tk.TclError:
        pass


def ui_labels(window):
    window._refresh_privacy_status()
    return tuple(label.cget("text") for label in window._privacy_labels)


def test_native_tk_labels_are_visible_and_no_capture_on_initialization(desktop):
    root, window, app, vision = desktop
    assert ui_labels(window)[2] == "Visão: sem captura"
    assert "Ctrl+Shift+M" not in window.transcript.get("1.0", "end")
    assert root.bind("<Control-Shift-M>")
    assert vision.captures == 0
    assert app.agent.calls == []


def test_keyboard_microphone_toggle_reuses_existing_consent_boundary(desktop):
    root, window, app, vision = desktop
    assert window._voice_active is True
    assert window._shortcut_toggle_listening() == "break"
    assert window._voice_active is False
    assert ui_labels(window)[0] == "Escuta: pausada"
    assert window.mic_button.cget("text") == "Retomar escuta"
    assert vision.captures == 0
    assert app.agent.calls == []
    assert window._shortcut_toggle_listening() == "break"
    assert window._voice_active is True
    assert ui_labels(window)[0] in ("Escuta: aguardando", "Escuta: solicitada")


def test_rejected_vision_consent_never_sets_processing_or_captures(
    desktop, monkeypatch,
):
    from tkinter import simpledialog
    root, window, app, vision = desktop
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Explique")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: False)
    window._vision_screen()
    assert ui_labels(window)[2] == "Visão: sem captura"
    assert not window._busy
    assert vision.captures == 0


def test_authorized_vision_shows_progress_and_cancellation_truthfully(
    desktop, monkeypatch,
):
    from tkinter import simpledialog
    root, window, app, vision = desktop
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "O que aparece?")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._vision_screen()
    spin(root, lambda: vision.entered.is_set())
    assert ui_labels(window)[2] == "Visão: processando tela"
    window._cancel_current()
    assert ui_labels(window)[2] == "Visão: cancelamento solicitado"
    assert vision.captures == 1
    vision.release.set()
    spin(root, lambda: not window._busy)
    assert ui_labels(window)[2] == "Visão: sem captura"
    assert app.agent.calls == []


def test_on_demand_privacy_dialog_uses_current_state_without_devices(
    desktop, monkeypatch,
):
    root, window, app, vision = desktop
    dialogs = []
    monkeypatch.setattr(window.messagebox, "showinfo", lambda *a, **kw: dialogs.append((a, kw)))
    assert root.bind("<Control-Shift-I>")
    assert window._show_privacy_status() == "break"
    assert "Escuta: aguardando" in dialogs[-1][0][1] or "Escuta: solicitada" in dialogs[-1][0][1]
    assert "Visão: sem captura" in dialogs[-1][0][1]
    assert "não verificam hardware" in dialogs[-1][0][1]
    assert dialogs[-1][1]["parent"] is root

    window._shortcut_toggle_listening()
    window.speech_enabled.set(False)
    # No GUI poll is needed: the dialog must use the current state, not cached labels.
    assert window._show_privacy_status() == "break"
    assert "Escuta: pausada" in dialogs[-1][0][1]
    assert "Voz: desativada" in dialogs[-1][0][1]
    assert vision.captures == 0
    assert app.agent.calls == []


def test_on_demand_dialog_reports_only_authorized_visual_source(
    desktop, monkeypatch,
):
    from tkinter import simpledialog
    root, window, app, vision = desktop
    dialogs = []
    monkeypatch.setattr(window.messagebox, "showinfo", lambda *a, **kw: dialogs.append(a[1]))
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "Segredo do arquivo")
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._vision_screen()
    spin(root, lambda: vision.entered.is_set())
    window._show_privacy_status()
    assert "Visão: processando tela" in dialogs[-1]
    assert "Segredo do arquivo" not in dialogs[-1]
    window._cancel_current()
    window._show_privacy_status()
    assert "Visão: cancelamento solicitado" in dialogs[-1]
    assert vision.captures == 1
    assert app.agent.calls == []
    vision.release.set()
    spin(root, lambda: not window._busy)


def test_privacy_shortcut_does_not_reopen_dialog_during_shutdown(desktop, monkeypatch):
    root, window, app, vision = desktop
    monkeypatch.setattr(window.messagebox, "showinfo",
                        lambda *a, **kw: pytest.fail("Dialog after shutdown"))
    window._close()
    assert window._show_privacy_status() == "break"
    assert vision.captures == 0
