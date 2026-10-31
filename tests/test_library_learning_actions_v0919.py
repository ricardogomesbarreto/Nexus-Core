"""Resumo e plano local só após clique e usando trechos recuperados."""
import os
import time
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")
def test_summary_and_study_outline_are_explicit_and_source_grounded(monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from nexus.desktop import library_panel

    hit = SimpleNamespace(document_id=1, chunk_id=2, ordinal=0,
                          name="aula.md", text="A ciência estuda a natureza.")
    asked = []

    class Store:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def list_documents(self, limit=20): return []
        def search(self, query, limit, for_context=False):
            assert query == "ciência"
            assert limit == 3 and for_context
            return [hit]

    def fake_answer(question, hits, model_router):
        asked.append((question, hits, model_router))
        return {"answer": "Resposta fundamentada [1:2].",
                "sources": [{"document_id": 1, "chunk_id": 2, "name": "aula.md",
                             "excerpt": hit.text}], "model_used": True}

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", Store)
    monkeypatch.setattr(library_panel, "answer_from_hits", fake_answer)
    app = SimpleNamespace(model_router=object())
    root = tk.Tk()
    root.withdraw()

    def all_widgets(parent, kind):
        found = []
        for child in parent.winfo_children():
            if isinstance(child, kind):
                found.append(child)
            found.extend(all_widgets(child, kind))
        return found

    def wait(predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            root.update()
            if predicate():
                return
            time.sleep(.01)
        pytest.fail("A ação local não terminou")

    try:
        panel = library_panel.open_library(root, app)
        wait(lambda: any("operação concluída" in w.cget("text")
                         for w in all_widgets(panel, ttk.Label)))
        assert asked == []  # Abrir Biblioteca não consulta Ollama.
        query = all_widgets(panel, ttk.Entry)[0]
        query.delete(0, "end")
        query.insert(0, "ciência")
        actions = {w.cget("text"): w for w in all_widgets(panel, ttk.Button)}
        actions["Resumir trechos com IA local"].invoke()
        wait(lambda: len(asked) == 1)
        wait(lambda: "Resposta fundamentada" in all_widgets(panel, tk.Text)[0].get("1.0", "end"))
        actions["Plano de estudo com IA local"].invoke()
        wait(lambda: len(asked) == 2)
        assert asked[0][0].startswith("Resuma com fontes")
        assert asked[1][0].startswith("Proponha etapas")
        assert all(item[1] == [hit] and item[2] is app.model_router for item in asked)
    finally:
        root.destroy()
