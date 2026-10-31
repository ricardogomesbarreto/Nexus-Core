"""The semantic action is explicit and never starts a model when browsing."""
import os
import time
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_semantic_button_does_not_embed_on_open_and_reuses_sources(monkeypatch):
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    from nexus.desktop import library_panel
    import nexus.knowledge.semantic_local as semantic

    hit = SimpleNamespace(document_id=9, chunk_id=12, ordinal=0,
                          name="aula.md", text="A fotossíntese utiliza luz.")
    events = []

    class FakeLibrary:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def list_documents(self, limit=20): return []
        def semantic_candidates(self, query, limit):
            assert query == "energia da luz" and limit == 8
            events.append("sample")
            return [hit]

    class FakeEmbedding:
        def rerank(self, question, hits, model, **kwargs):
            events.append((question, model))
            assert hits == [hit]
            return [semantic.SemanticMatch(hit, 0.87)]

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", FakeLibrary)
    monkeypatch.setattr(semantic, "LocalSemanticReranker", FakeEmbedding)
    monkeypatch.setattr(simpledialog, "askstring", lambda *a, **kw: "embed-local")
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw: True)
    root = tk.Tk()
    root.withdraw()

    def widgets(parent, kind):
        found = []
        for child in parent.winfo_children():
            if isinstance(child, kind):
                found.append(child)
            found.extend(widgets(child, kind))
        return found

    def until(predicate):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            root.update()
            if predicate(): return
            time.sleep(.01)
        pytest.fail("Semântica local não concluiu operação")

    try:
        panel = library_panel.open_library(root, SimpleNamespace())
        until(lambda: any("operação concluída" in w.cget("text")
                          for w in widgets(panel, ttk.Label)))
        assert events == []
        field = widgets(panel, ttk.Entry)[0]
        field.delete(0, "end")
        field.insert(0, "energia da luz")
        buttons = {w.cget("text"): w for w in widgets(panel, ttk.Button)}
        buttons["Similaridade semântica local"].invoke()
        until(lambda: "Similaridade 0.870" in widgets(panel, tk.Text)[0].get("1.0", "end"))
        assert events == ["sample", ("energia da luz", "embed-local")]
    finally:
        root.destroy()


@pytest.mark.skipif(not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
                    reason="PostgreSQL de teste indisponível")
def test_recent_chunks_are_bounded_and_source_linked(tmp_path):
    from uuid import uuid4
    from nexus.config.settings import Settings
    from nexus.security.paths import PathSecurity
    from nexus.knowledge.store import PostgreSQLKnowledgeBase, KnowledgeValidationError

    home = tmp_path / "home"
    home.mkdir()
    guard = PathSecurity()
    guard.home = home.resolve()
    guard.protected_paths = []
    config = Settings(
        database_name="nexus_test", database_user="nexus_test",
        database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"],
    )
    store = PostgreSQLKnowledgeBase(config, guard)
    store.initialize()
    document = None
    token = uuid4().hex
    source = home / "material.md"
    source.write_text(f"A energia solar {token} é renovável.", encoding="utf-8")
    try:
        document = store.ingest(source)
        results = store.recent_chunks(8)
        assert 1 <= len(results) <= 8
        assert any(hit.document_id == document.id and token in hit.text
                   for hit in results)
        with pytest.raises(KnowledgeValidationError):
            store.recent_chunks(100)
        assert store.delete(document.id)
    finally:
        if document is not None:
            store.delete(document.id)
        store.close()
