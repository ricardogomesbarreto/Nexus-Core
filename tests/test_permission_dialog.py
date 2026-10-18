"""Consent accepts exact decisions; uncertain speech never authorizes."""

import os
from queue import Empty, Queue
from threading import Event, Thread

import pytest

from nexus.desktop.permission_dialog import PermissionDialog, permission_answer


@pytest.mark.parametrize("utterance,spoken,expected", [
    ("AUTORIZAR", False, True),
    ("Negar", False, False),
    ("cancelar", False, False),
    ("Nexus, autorizo esta ação", True, True),
    ("nexus nao autorizo esta acao", True, False),
    ("Nexus, nego esta ação", True, False),
    ("sim", True, None),
    ("autorizar", True, None),
    ("não autorizo esta ação", True, None),
    ("Nexus, autorizo esta ação e execute outra", True, None),
    ("autorizo", False, None),
])
def test_only_explicit_exact_consent_is_accepted(utterance, spoken, expected):
    assert permission_answer(utterance, spoken=spoken) is expected


class Recognizer:
    def __init__(self):
        self.phrases = Queue()
        self.started = Event()

    def recognize_continuous(self, cancelled):
        self.started.set()
        while not cancelled():
            try:
                return self.phrases.get(timeout=0.01)
            except Empty:
                pass
        return ""

    def stop(self):
        pass


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
@pytest.mark.parametrize("typed,expected", [("AUTORIZAR", True), ("NEGAR", False), ("sim", False)])
def test_modal_typed_decision(typed, expected):
    import tkinter as tk
    root = tk.Tk()
    recognizer = Recognizer()
    workers = []

    def start_worker(target):
        worker = Thread(target=target, daemon=True)
        workers.append(worker)
        worker.start()

    try:
        dialog = PermissionDialog(root, "Ferramenta: create_directory\nRecurso: /home/user/Teste",
                                  recognizer=recognizer, listen=False,
                                  ready_to_listen=lambda: True,
                                  start_worker=start_worker, cancelled=lambda: False)

        def decide():
            dialog.entry.insert(0, typed)
            dialog._typed_answer()
            if typed == "sim":
                assert dialog.window.winfo_exists()  # Ambiguous text stays unapproved.
                dialog._finish(False)

        root.after(150, decide)
        assert dialog.ask() is expected
        assert not recognizer.started.is_set()
    finally:
        root.destroy()


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_modal_spoken_consent_and_cancellation():
    import tkinter as tk
    root = tk.Tk()
    recognizer = Recognizer()
    cancelled = Event()
    workers = []

    def start_worker(target):
        worker = Thread(target=target, daemon=True)
        workers.append(worker)
        worker.start()

    try:
        for phrase, expected in (("sim", False), ("Nexus, autorizo esta ação", True)):
            dialog = PermissionDialog(root, "Ação: criar pasta\nPasta: /home/user/Teste",
                                      recognizer=recognizer, listen=True,
                                      ready_to_listen=lambda: True,
                                      start_worker=start_worker,
                                      cancelled=cancelled.is_set)
            recognizer.phrases.put(phrase)
            if not expected:
                root.after(350, cancelled.set)
            assert dialog.ask() is expected
            cancelled.clear()
    finally:
        root.destroy()
        for worker in workers:
            worker.join(timeout=1)


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_question_is_spoken_before_microphone_can_accept_consent():
    import tkinter as tk

    class Speaker:
        def __init__(self):
            self.started = Event()
            self.release = Event()
            self.calls = []

        def speak(self, text, voice):
            self.calls.append((text, voice))
            self.started.set()
            self.release.wait(timeout=3)

        def stop(self):
            self.release.set()

    root = tk.Tk()
    recognizer = Recognizer()
    speaker = Speaker()
    workers = []

    def start_worker(target):
        worker = Thread(target=target, daemon=True)
        workers.append(worker)
        worker.start()

    try:
        dialog = PermissionDialog(
            root, "Ação: criar pasta\nAlvo: /home/user/Teste",
            recognizer=recognizer, listen=True, ready_to_listen=lambda: True,
            start_worker=start_worker, cancelled=lambda: False,
            speaker=speaker, voice="Masculina",
            spoken_question="Nexus Core pede autorização para criar uma pasta.",
        )

        def verify_order():
            if not speaker.started.is_set():
                root.after(20, verify_order)
                return
            assert not recognizer.started.is_set()
            assert dialog.window.winfo_exists()
            assert dialog.description.winfo_ismapped()
            assert "Ação: criar pasta" in dialog.description.get("1.0", "end")
            recognizer.phrases.put("Nexus, autorizo esta ação")
            speaker.release.set()

        root.after(100, verify_order)
        root.after(4000, lambda: dialog._finish(False))
        assert dialog.ask() is True
        assert speaker.calls == [("Nexus Core pede autorização para criar uma pasta.", "Masculina")]
        assert recognizer.started.is_set()
    finally:
        speaker.release.set()
        root.destroy()
        for worker in workers:
            worker.join(timeout=1)
