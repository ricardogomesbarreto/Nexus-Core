"""Tk/Xvfb acceptance for optional v0.9.19 controls; no real audio or DB."""
import os
import time
from types import SimpleNamespace

import pytest


pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")


def widgets(parent, kind):
    found = []
    for child in parent.winfo_children():
        if isinstance(child, kind):
            found.append(child)
        found.extend(widgets(child, kind))
    return found


def until(root, predicate):
    deadline = time.monotonic() + 5
    while time.monotonic() < deadline:
        root.update()
        if predicate():
            return
        time.sleep(.01)
    pytest.fail("Painel não concluiu operação de teste")


def test_study_offline_exercises_speech_and_opt_in_progress(monkeypatch):
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    from nexus.desktop import study_panel
    from nexus.offline_study import generate_cloze_questions
    import nexus.voice.local as local_voice

    snippet = "A fotossíntese transforma energia luminosa em energia química."
    hit = SimpleNamespace(document_id=5, chunk_id=12, name="aula.md", text=snippet)
    written = []
    spoken = []

    class FakeStore:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def due(self): return []
        def record_session(self, chunk, correct, total):
            written.append((chunk, correct, total))
            return 5
        def recent_sessions(self): return written[:]

    class FakeSpeaker:
        VOICES = {"Feminina": "", "Masculina": ""}
        MAX_SPEECH = 2400
        def speak(self, text, voice, *, cancelled=None):
            spoken.append((text, voice))
        def stop(self):
            spoken.append(("stop", ""))

    monkeypatch.setattr(study_panel, "PostgreSQLStudyCards", FakeStore)
    monkeypatch.setattr(local_voice, "LocalSpeaker", FakeSpeaker)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw: True)
    monkeypatch.setattr(simpledialog, "askstring",
                        lambda *a, **kw: generate_cloze_questions(snippet)[0].expected_answer)

    root = tk.Tk()
    root.withdraw()
    try:
        panel = study_panel.open_study(root, hit, voice="Masculina")
        until(root, lambda: any("cartões disponíveis" in w.cget("text")
                                for w in widgets(panel, ttk.Label)))
        actions = {w.cget("text"): w for w in widgets(panel, ttk.Button)}
        actions["Gerar exercícios do trecho"].invoke()
        actions["Responder exercício"].invoke()
        actions["Salvar progresso"].invoke()
        until(root, lambda: written == [(12, 1, 1)])
        actions["Ler trecho em voz alta"].invoke()
        until(root, lambda: spoken and spoken[0] == (snippet, "Masculina"))
        actions["Parar leitura"].invoke()
    finally:
        root.destroy()


def test_offline_catalog_button_does_not_use_database_for_catalog(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import filedialog, ttk
    from nexus.desktop import library_panel
    import nexus.knowledge.offline_catalog as catalog

    class FakeLibrary:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def list_documents(self, limit=20): return []

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", FakeLibrary)
    monkeypatch.setattr(filedialog, "askdirectory", lambda **kw: str(tmp_path))
    monkeypatch.setattr(catalog, "list_offline_materials",
                        lambda path: [catalog.OfflineMaterial("wiki.zim", "ZIM local", 12)])
    root = tk.Tk()
    root.withdraw()
    try:
        panel = library_panel.open_library(root, SimpleNamespace())
        until(root, lambda: any("operação concluída" in w.cget("text")
                                for w in widgets(panel, ttk.Label)))
        actions = {w.cget("text"): w for w in widgets(panel, ttk.Button)}
        actions["Catálogo offline"].invoke()
        until(root, lambda: "wiki.zim" in widgets(panel, tk.Text)[0].get("1.0", "end"))
    finally:
        root.destroy()
