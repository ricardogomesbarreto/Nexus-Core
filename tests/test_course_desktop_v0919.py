"""Tk/Xvfb: cursos offline somente após escolha, sem serviço ou banco."""
import os
import time
from pathlib import Path
from types import SimpleNamespace

import pytest

pytestmark = pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Exige Tk/Xvfb")


def find_all(parent, kind):
    result = []
    for child in parent.winfo_children():
        if isinstance(child, kind):
            result.append(child)
        result.extend(find_all(child, kind))
    return result


def eventually(root, predicate):
    deadline = time.monotonic() + 4
    while time.monotonic() < deadline:
        root.update()
        if predicate():
            return
        time.sleep(.01)
    pytest.fail("Interface do curso não concluiu a operação")


def test_course_panel_reads_only_after_click_and_offers_quiz(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import simpledialog, ttk
    from nexus.desktop import course_panel
    from nexus.study.offline_course import OfflineCourse, CourseLesson
    from nexus.offline_study import generate_cloze_questions

    text = "A fotossíntese transforma energia luminosa em energia química."
    course = OfflineCourse(tmp_path, "Ciências", (
        CourseLesson("Aula 1", "aula1.md"), CourseLesson("Aula 2", "aula2.md"),
    ))
    opened = []
    monkeypatch.setattr(course_panel, "read_lesson",
                        lambda current, index: opened.append(index) or text)
    monkeypatch.setattr(simpledialog, "askstring",
                        lambda *a, **kw: generate_cloze_questions(text)[0].expected_answer)
    root = tk.Tk()
    root.withdraw()
    try:
        panel = course_panel.open_course(root, course)
        listing = find_all(panel, tk.Listbox)[0]
        actions = {x.cget("text"): x for x in find_all(panel, ttk.Button)}
        assert opened == []
        actions["Concluir aula"].invoke()
        assert "□" in listing.get(0)
        actions["Ler aula"].invoke()
        assert opened == [0]
        actions["Concluir aula"].invoke()
        assert "✓" in listing.get(0)
        actions["Gerar exercícios"].invoke()
        assert "_____" in find_all(panel, tk.Text)[0].get("1.0", "end")
        actions["Responder exercício"].invoke()
        assert "1/1" in find_all(panel, tk.Text)[0].get("1.0", "end")
        actions["Sugerir próximo passo"].invoke()
        assert "Pratique ao menos cinco" in find_all(panel, tk.Text)[0].get("1.0", "end")
        actions["Próxima aula"].invoke()
        assert listing.curselection() == (1,)
        assert opened == [0]  # No automatic reading of the next lesson.
    finally:
        root.destroy()


def test_library_course_button_loads_metadata_without_database(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk
    from nexus.desktop import library_panel, course_panel
    from nexus.study.offline_course import OfflineCourse, CourseLesson
    from nexus.study import offline_course

    seen = []
    prepared = OfflineCourse(tmp_path, "Matemática", (CourseLesson("Frações", "a.md"),))
    class Library:
        def __init__(self, settings): pass
        def initialize(self): pass
        def close(self): pass
        def list_documents(self, limit=20): return []

    monkeypatch.setattr(library_panel, "PostgreSQLKnowledgeBase", Library)
    monkeypatch.setattr(filedialog, "askdirectory", lambda **kw: str(tmp_path))
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw: True)
    monkeypatch.setattr(offline_course, "load_course",
                        lambda directory: seen.append(directory) or prepared)
    monkeypatch.setattr(course_panel, "open_course",
                        lambda root, course: seen.append(course))
    root = tk.Tk()
    root.withdraw()
    try:
        panel = library_panel.open_library(root, SimpleNamespace())
        eventually(root, lambda: any("operação concluída" in x.cget("text")
                                     for x in find_all(panel, ttk.Label)))
        actions = {x.cget("text"): x for x in find_all(panel, ttk.Button)}
        assert seen == []
        actions["Abrir curso offline"].invoke()
        eventually(root, lambda: len(seen) == 2)
        assert seen == [str(tmp_path), prepared]
    finally:
        root.destroy()
