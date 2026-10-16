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
