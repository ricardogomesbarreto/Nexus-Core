"""Tutor level control explicitly invokes local source-grounded model only on click."""
import os
import time
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")
def test_level_aware_tutor_requires_explicit_click_and_sources(monkeypatch):
    import tkinter as tk
    from tkinter import ttk
    from nexus.desktop import library_panel

    hit = SimpleNamespace(document_id=21, chunk_id=33, ordinal=0,
                          name="manual.md", text="Programação usa algoritmos.")
    calls = []

    class Store:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def list_documents(self, limit=20): return []
        def search(self, term, limit, for_context=False):
            assert term == "algoritmos" and limit == 3 and for_context
            return [hit]

    def fake_answer(prompt, hits, router):
        calls.append((prompt, hits, router))
        return {"answer": "3 etapas sobre algoritmos [21:33]",
                "sources": [{"document_id": 21, "chunk_id": 33, "name": "manual.md",
                             "excerpt": hit.text}], "model_used": True}

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", Store)
    monkeypatch.setattr(library_panel, "answer_from_hits", fake_answer)
    app = SimpleNamespace(model_router=object())
    root = tk.Tk()
    root.withdraw()

    def find_all(widget, kind):
        found = []
        for sub in widget.winfo_children():
            if isinstance(sub, kind): found.append(sub)
            found.extend(find_all(sub, kind))
        return found

    def await_ready(predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            root.update()
            if predicate(): return
            time.sleep(.01)
        pytest.fail("Consulta guiada não finalizada")
    try:
        win = library_panel.open_library(root, app)
        await_ready(lambda: any("operação concluída" in x.cget("text")
                                for x in find_all(win, ttk.Label)))
        assert calls == []
        find_all(win, ttk.Combobox)[0].set("Avançado")
        entry = find_all(win, ttk.Entry)[0]
        entry.delete(0, "end")
        entry.insert(0, "algoritmos")
        buttons = {x.cget("text"): x for x in find_all(win, ttk.Button)}
        buttons["Tutor guiado por fontes"].invoke()
        await_ready(lambda: len(calls) == 1)
        assert "técnico" in calls[0][0]
        assert calls[0][1] == [hit]
        assert calls[0][2] is app.model_router
    finally:
        root.destroy()
