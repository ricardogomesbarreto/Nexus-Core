"""Aula falada e busca local: testes Tk/Xvfb sem audio ou modelos reais."""
import os
import threading
import time

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")


def _widgets(parent, kind):
    found = []
    for child in parent.winfo_children():
        if isinstance(child, kind):
            found.append(child)
        found.extend(_widgets(child, kind))
    return found


def _until(root, predicate):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        root.update()
        if predicate():
            return
        time.sleep(0.01)
    pytest.fail("A interface nao concluiu a operacao offline")


def test_course_search_only_after_explicit_button(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import simpledialog, ttk

    import nexus.desktop.course_panel as ui
    from nexus.study.course_search import CourseSearchHit
    from nexus.study.offline_course import OfflineCourse, CourseLesson

    course = OfflineCourse(tmp_path, "Biologia",
                           (CourseLesson("Fotossintese", "aula.md"),))
    calls = []

    def search(course_arg, term, *, limit):
        calls.append((course_arg, term, limit))
        return [CourseSearchHit(0, "Fotossintese",
                                "A fotossintese converte energia luminosa.")]

    monkeypatch.setattr(ui, "search_course", search)
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "energia")
    root = tk.Tk()
    root.withdraw()
    try:
        panel = ui.open_course(root, course)
        actions = {w.cget("text"): w for w in _widgets(panel, ttk.Button)}
        assert calls == []
        assert sum(w.cget("text") == "Pesquisar no curso"
                   for w in _widgets(panel, ttk.Button)) == 1
        actions["Pesquisar no curso"].invoke()
        _until(root, lambda: "converte energia" in
               _widgets(panel, tk.Text)[0].get("1.0", "end"))
        assert calls == [(course, "energia", 8)]
    finally:
        root.destroy()


def test_course_voice_uses_selected_local_profile_pause_and_stop(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import ttk

    import nexus.desktop.course_panel as ui
    import nexus.voice.local as voice_module
    from nexus.study.offline_course import OfflineCourse, CourseLesson

    course = OfflineCourse(tmp_path, "Historia", (CourseLesson("Aula", "aula.md"),))
    started = threading.Event()
    released = threading.Event()
    called = []
    controllers = []

    class Speaker:
        VOICES = {"Feminina": "", "Masculina": ""}
        MAX_SPEECH = 2400

        def __init__(self):
            controllers.append(self)

        def speak(self, text, voice, **options):
            called.append((text, voice, options))
            started.set()
            released.wait(3)

        def pause(self):
            called.append("pause")
            return True

        def resume(self):
            called.append("resume")
            return True

        def stop(self):
            called.append("stop")
            released.set()

    monkeypatch.setattr(voice_module, "LocalSpeaker", Speaker)
    monkeypatch.setattr(ui, "read_lesson", lambda *args: "P" * 3000)
    root = tk.Tk()
    root.withdraw()
    try:
        panel = ui.open_course(root, course, voice="Masculina", speed=1.25, volume=75)
        actions = {w.cget("text"): w for w in _widgets(panel, ttk.Button)}
        assert controllers == []
        actions["Ouvir aula"].invoke()
        assert controllers == []
        actions["Ler aula"].invoke()
        actions["Ouvir aula"].invoke()
        _until(root, started.is_set)
        assert len(controllers) == 1
        text, selected_voice, opts = called[0]
        assert selected_voice == "Masculina"
        assert len(text) == 2400
        assert opts["speed"] == 1.25 and opts["volume"] == 75
        assert callable(opts["cancelled"])
        actions["Pausar/retomar áudio"].invoke()
        actions["Pausar/retomar áudio"].invoke()
        assert "pause" in called and "resume" in called
        actions["Parar áudio"].invoke()
        assert opts["cancelled"]()
        _until(root, lambda: "concluída ou interrompida" in
               " ".join(w.cget("text") for w in _widgets(panel, ttk.Label)))
        assert called[-1] == "stop"
    finally:
        released.set()
        root.destroy()


def test_closing_course_stops_ongoing_speech(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import ttk

    import nexus.desktop.course_panel as ui
    import nexus.voice.local as voice_module
    from nexus.study.offline_course import OfflineCourse, CourseLesson

    course = OfflineCourse(tmp_path, "Português", (CourseLesson("Aula", "aula.md"),))
    signal = threading.Event()
    stopped = threading.Event()

    class Speaker:
        VOICES = {"Feminina": "", "Masculina": ""}
        MAX_SPEECH = 2400
        def speak(self, text, voice, **kwargs):
            signal.set()
            stopped.wait(3)
        def stop(self):
            stopped.set()

    monkeypatch.setattr(voice_module, "LocalSpeaker", Speaker)
    monkeypatch.setattr(ui, "read_lesson", lambda *args: "Uma aula falada.")
    root = tk.Tk()
    root.withdraw()
    try:
        panel = ui.open_course(root, course)
        controls = {w.cget("text"): w for w in _widgets(panel, ttk.Button)}
        controls["Ler aula"].invoke()
        controls["Ouvir aula"].invoke()
        _until(root, signal.is_set)
        panel.tk.call(panel.protocol("WM_DELETE_WINDOW"))
        assert stopped.is_set()
        assert not panel.winfo_exists()
    finally:
        stopped.set()
        root.destroy()
