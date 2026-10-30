"""The native library exposes source-linked study without an external UI."""

import os
import time
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")
def test_library_study_card_creation_and_review(monkeypatch):
    import tkinter as tk
    from tkinter import messagebox, ttk
    from nexus.desktop import library_panel, study_panel
    from nexus.study.store import PostgreSQLStudyCards

    hit = SimpleNamespace(document_id=3, chunk_id=9, name="aula.md",
                          text="PostgreSQL é o banco de dados do Nexus Core.")
    class Library:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def list_documents(self, limit=20): return []
        def search(self, query, limit): return [hit]

    card = SimpleNamespace(id=10, source_chunk_id=9, source_name="aula.md",
                           question="Qual é o banco?", answer="PostgreSQL",
                           source_excerpt=hit.text)
    saved = []
    class Study:
        _text = staticmethod(PostgreSQLStudyCards._text)
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def due(self): return saved[:]
        def create(self, chunk_id, question, answer):
            assert (chunk_id, question, answer) == (9, card.question, card.answer)
            saved.append(card)
            return card
        def grade(self, card_id, correct):
            assert (card_id, correct) == (10, True)
            saved.clear()
            return True

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", Library)
    monkeypatch.setattr(study_panel, "PostgreSQLStudyCards", Study)
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw: True)
    root = tk.Tk()
    root.withdraw()
    def widgets(parent, kind):
        result = []
        for child in parent.winfo_children():
            if isinstance(child, kind): result.append(child)
            result.extend(widgets(child, kind))
        return result
    def wait_until(predicate):
        deadline = time.monotonic() + 3
        while time.monotonic() < deadline:
            root.update()
            if predicate(): return
            time.sleep(.01)
        pytest.fail("A janela não terminou a operação local")
    try:
        library = library_panel.open_library(root, SimpleNamespace())
        wait_until(lambda: any("operação concluída" in w.cget("text")
                               for w in widgets(library, ttk.Label)))
        entry = widgets(library, ttk.Entry)[0]
        entry.delete(0, "end")
        entry.insert(0, "PostgreSQL")
        buttons = {w.cget("text"): w for w in widgets(library, ttk.Button)}
        buttons["Pesquisar trechos"].invoke()
        wait_until(lambda: "Fonte 3:9" in widgets(library, tk.Text)[0].get("1.0", "end"))
        buttons["Criar cartão do 1º trecho"].invoke()
        study = [w for w in root.winfo_children() if w is not library][-1]
        inputs = widgets(study, ttk.Entry)
        inputs[0].insert(0, card.question)
        inputs[1].insert(0, card.answer)
        actions = {w.cget("text"): w for w in widgets(study, ttk.Button)}
        wait_until(lambda: any("cartões disponíveis" in w.cget("text")
                               for w in widgets(study, ttk.Label)))
        actions["Criar cartão"].invoke()
        listing = widgets(study, tk.Listbox)[0]
        wait_until(lambda: listing.size() == 1)
        listing.selection_set(0)
        listing.event_generate("<<ListboxSelect>>")
        root.update()
        actions["Mostrar resposta"].invoke()
        assert "PostgreSQL" in widgets(study, tk.Text)[0].get("1.0", "end")
        actions["Acertei"].invoke()
        wait_until(lambda: listing.size() == 0)
    finally:
        root.destroy()
