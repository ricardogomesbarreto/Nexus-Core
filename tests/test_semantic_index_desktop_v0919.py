"""Indexing is an explicit Library menu action and remains inactive on open."""
import os
import time
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_index_requires_selection_and_consent(monkeypatch):
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    from nexus.desktop import library_panel
    import nexus.knowledge.semantic_local as semantic

    events = []
    doc = SimpleNamespace(id=9, name="material.md", chunk_count=1)
    hit = SimpleNamespace(document_id=9, chunk_id=12, ordinal=0,
                          name=doc.name, text="A luz alimenta as plantas.")

    class Store:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def list_documents(self, limit=20): return [doc]
        def indexable_chunks(self, document_id):
            events.append("read")
            return [hit]
        def save_embeddings(self, document_id, model, entries):
            events.append("save")
            assert entries == [(12, [1.0] + [0.0] * 7)]
            return 1

    class Embedding:
        def embed(self, texts, model):
            events.append("embed")
            assert texts == [hit.text]
            return [[1.0] + [0.0] * 7]

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", Store)
    monkeypatch.setattr(semantic, "LocalSemanticReranker", Embedding)
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "embed-local")
    consent = [False, True]
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw: consent.pop(0))
    root = tk.Tk()
    root.withdraw()

    def wait(predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            root.update()
            if predicate(): return
            time.sleep(.01)
        pytest.fail("Índice local não concluiu")

    panel = None
    try:
        panel = library_panel.open_library(root, SimpleNamespace())
        labels = lambda: [w for w in panel.winfo_children()[0].winfo_children()
                          if isinstance(w, ttk.Label)]
        wait(lambda: any("operação concluída" in w.cget("text")
                         for w in labels()))
        assert events == []
        menu = panel.nametowidget(panel.cget("menu"))
        assert menu.type(0) == "cascade"
        actions = panel.nametowidget(menu.entrycget(0, "menu"))
        assert actions.type(0) == "command"
        actions.invoke(0)
        assert events == []  # No document selected.
        listing = next(w for w in panel.winfo_children()[0].winfo_children()
                       if isinstance(w, tk.Listbox))
        listing.selection_set(0)
        actions.invoke(0)
        assert events == []  # Consent denied.
        actions.invoke(0)
        wait(lambda: events == ["read", "embed", "save"])
        wait(lambda: any("operação concluída" in w.cget("text")
                         for w in labels()))
        entry = next(w for w in panel.winfo_children()[0].winfo_children()
                     if isinstance(w, ttk.Entry))
        entry.delete(0, "end")
        entry.insert(0, "Explique a luz")
        def fake_answer(question, model, store, router_factory):
            events.append("answer")
            assert (question, model) == ("Explique a luz", "embed-local")
            return {"answer": "A luz alimenta as plantas.", "sources": [{
                "document_id": 9, "chunk_id": 12, "name": "material.md",
                "excerpt": hit.text}], "model_used": True}
        monkeypatch.setattr(semantic, "answer_from_index", fake_answer)
        consent.extend([False, True])
        actions.invoke(2)
        assert "answer" not in events
        actions.invoke(2)
        wait(lambda: "answer" in events)
    finally:
        root.destroy()
        if panel is not None:
            assert panel._nexus_index_menus == ()
