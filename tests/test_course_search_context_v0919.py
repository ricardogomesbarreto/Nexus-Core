"""Unicode-aware, context-bounded course search snippets."""
import json

from nexus.security.paths import PathSecurity
from nexus.study.course_search import search_course
from nexus.study.offline_course import load_course


def setup_course(tmp_path, text):
    folder = tmp_path / "curso"
    folder.mkdir()
    (folder / "course.json").write_text(json.dumps({
        "version": 1,
        "title": "Curso",
        "lessons": [{"title": "Aula", "file": "aula.md"}],
    }), encoding="utf-8")
    (folder / "aula.md").write_text(text, encoding="utf-8")
    guard = PathSecurity()
    guard.home = tmp_path.resolve()
    guard.protected_paths = []
    return load_course(folder, guard), guard


def test_late_match_is_inside_visible_excerpt(tmp_path):
    course, guard = setup_course(
        tmp_path,
        "Contexto introdutório: " + "palavras " * 100 +
        "o fenômeno da FOTOSSÍNTESE recebe luz solar.\n",
    )
    matches = search_course(course, "fotossintese", paths=guard)
    assert len(matches) == 1
    assert "FOTOSSÍNTESE" in matches[0].excerpt
    assert len(matches[0].excerpt) <= 180
    assert matches[0].excerpt.startswith("…")


def test_decomposed_accents_are_mapped_correctly(tmp_path):
    course, guard = setup_course(
        tmp_path,
        "Uma explicação: " + "crescimento " * 40 +
        "o fenômeno de fotossi\u0301ntese ocorre nas árvores.\n",
    )
    matches = search_course(course, "fotossíntese", paths=guard)
    assert len(matches) == 1
    assert "fotossi\u0301ntese" in matches[0].excerpt
