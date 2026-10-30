"""Kolibri export UI checks: opt-in and no PostgreSQL/embeddings for inspection."""
import os
import time
from types import SimpleNamespace

import pytest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")
def test_kolibri_export_ui_never_starts_service_or_imports(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from nexus.desktop import library_panel
    import nexus.knowledge.kolibri_export as kolibri

    export = tmp_path / "KOLIBRI_DATA"
    export.mkdir()
    events = []

    class Library:
        def __init__(self, settings): pass
        def initialize(self): pass
        def list_documents(self, limit=20): return []
        def close(self): pass

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", Library)
    monkeypatch.setattr(filedialog, "askdirectory", lambda **kw: str(export))
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw:
                        events.append("consent") or True)
    monkeypatch.setattr(
        kolibri, "inspect_kolibri_export",
        lambda folder: events.append(folder) or
        kolibri.KolibriExport(
            (kolibri.KolibriChannel("a" * 32, 2048),), True,
        ),
    )

    def children(widget, kind):
        found = []
        for child in widget.winfo_children():
            if isinstance(child, kind):
                found.append(child)
            found.extend(children(child, kind))
        return found

    def wait(root, condition):
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline:
            root.update()
            if condition():
                return
            time.sleep(.01)
        pytest.fail("Inspeção Kolibri não terminou")

    root = tk.Tk()
    root.withdraw()
    try:
        window = library_panel.open_library(root, SimpleNamespace())
        wait(root, lambda: any("operação concluída" in x.cget("text")
                               for x in children(window, ttk.Label)))
        assert events == []
        buttons = {x.cget("text"): x for x in children(window, ttk.Button)}
        buttons["Inspecionar exportação Kolibri"].invoke()
        wait(root, lambda: "Canal " + "a" * 32 in children(window, tk.Text)[0].get("1.0", "end"))
        assert events == ["consent", str(export)]
        assert "nenhum canal importado" in (
            " ".join(x.cget("text") for x in children(window, ttk.Label)).lower()
        )
    finally:
        root.destroy()
