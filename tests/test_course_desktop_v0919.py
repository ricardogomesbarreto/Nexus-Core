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


def test_course_search_button_is_on_demand_and_displays_excerpts(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import ttk
    from nexus.desktop import course_panel
    import nexus.study.course_search as course_search
    from nexus.study.offline_course import OfflineCourse, CourseLesson

    course = OfflineCourse(tmp_path, "Curso local", (
        CourseLesson("Biologia", "biologia.md"),
    ))
    calls = []
    def fake_search(chosen, question, *, limit):
        calls.append((chosen, question, limit))
        return [course_search.CourseSearchHit(0, "Biologia",
                                             "A fotossíntese utiliza luz.")]

    monkeypatch.setattr(course_search, "search_course", fake_search)
    root = tk.Tk()
    root.withdraw()
    try:
        panel = course_panel.open_course(root, course)
        assert calls == []
        entries = find_all(panel, ttk.Entry)
        assert len(entries) == 1
        entries[0].delete(0, "end")
        entries[0].insert(0, "fotossintese")
        buttons = {x.cget("text"): x for x in find_all(panel, ttk.Button)}
        buttons["Pesquisar no curso"].invoke()
        assert calls == [(course, "fotossintese", 8)]
        assert "fotossíntese" in find_all(panel, tk.Text)[0].get("1.0", "end")
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


def test_course_progress_is_only_saved_or_loaded_on_click(monkeypatch, tmp_path):
    import tkinter as tk
    from tkinter import messagebox, ttk
    from nexus.desktop import course_panel
    import nexus.study.offline_course_progress as progress_module
    from nexus.study.offline_course import OfflineCourse, CourseLesson

    value = OfflineCourse(tmp_path, "Curso demonstrativo", (
        CourseLesson("Aula principal", "a.md"),
    ))
    state = {"saved": None, "writes": 0, "loads": 0}

    class FakeProgress:
        def __init__(self, settings): pass
        def save(self, course, completed):
            assert course is value
            state["saved"] = set(completed)
            state["writes"] += 1
            return len(completed)
        def load(self, course):
            assert course is value
            state["loads"] += 1
            return set(state["saved"] or ())

    monkeypatch.setattr(progress_module, "PostgreSQLOfflineCourseProgress", FakeProgress)
    monkeypatch.setattr(course_panel, "read_lesson", lambda c, i:
                        "A fotossíntese transforma energia luminosa em energia química.")
    monkeypatch.setattr(messagebox, "askyesno", lambda *a, **kw: True)
    root = tk.Tk()
    root.withdraw()
    try:
        panel = course_panel.open_course(root, value)
        actions = {w.cget("text"): w for w in find_all(panel, ttk.Button)}
        listing = find_all(panel, tk.Listbox)[0]
        assert state == {"saved": None, "writes": 0, "loads": 0}
        actions["Ler aula"].invoke()
        actions["Concluir aula"].invoke()
        assert "✓" in listing.get(0)
        assert state["writes"] == 0
        actions["Salvar progresso"].invoke()
        eventually(root, lambda: state["writes"] == 1)
        assert state["saved"] == {0}
        panel.destroy()

        new_panel = course_panel.open_course(root, value)
        new_list = find_all(new_panel, tk.Listbox)[0]
        new_actions = {w.cget("text"): w for w in find_all(new_panel, ttk.Button)}
        assert "□" in new_list.get(0)
        assert state["loads"] == 0
        new_actions["Carregar progresso"].invoke()
        eventually(root, lambda: "✓" in new_list.get(0))
        assert state["loads"] == 1
    finally:
        root.destroy()
