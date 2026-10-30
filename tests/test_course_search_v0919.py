"""Busca em aulas offline: somente texto autorizado, sem indexacao persistente."""
import json

import pytest

from nexus.security.paths import PathSecurity
from nexus.study.course_search import CourseSearchHit, search_course
from nexus.study.offline_course import CourseError, load_course


def fixture_course(tmp_path):
    directory = tmp_path / "curso"
    directory.mkdir()
    (directory / "course.json").write_text(json.dumps({
        "version": 1, "title": "Natureza",
        "lessons": [
            {"title": "Sol", "file": "sol.md"},
            {"title": "Água", "file": "agua.txt"},
            {"title": "Outros", "file": "outros.md"},
        ],
    }), encoding="utf-8")
    (directory / "sol.md").write_text(
        "# Sol\n\nA fotossíntese utiliza a energia solar para produzir açúcares.\n",
        encoding="utf-8",
    )
    (directory / "agua.txt").write_text(
        "O ciclo da água inclui a evaporação, a condensação e a precipitação.\n",
        encoding="utf-8",
    )
    (directory / "outros.md").write_text(
        "As árvores precisam de energia solar para crescer.\n",
        encoding="utf-8",
    )
    guard = PathSecurity()
    guard.home = tmp_path.resolve()
    guard.protected_paths = []
    return load_course(directory, guard), guard


def test_search_by_phrase_case_and_accent(tmp_path):
    course, guard = fixture_course(tmp_path)
    matches = search_course(course, "FOTOSSINTESE", paths=guard)
    assert len(matches) == 1
    assert matches[0] == CourseSearchHit(
        0, "Sol", "A fotossíntese utiliza a energia solar para produzir açúcares."
    )
    solar = search_course(course, "energia solar", paths=guard)
    assert [x.lesson_index for x in solar] == [0, 2]
    assert search_course(course, "eletrônica", paths=guard) == []


def test_search_is_explicitly_bounded(tmp_path):
    course, guard = fixture_course(tmp_path)
    hits = search_course(course, "energia solar", limit=1, paths=guard)
    assert len(hits) == 1
    assert len(hits[0].excerpt) <= 181


@pytest.mark.parametrize("query,limit", [
    ("", 8), ("a", 8), ("x" * 121, 8),
    ("abc\nother", 8), ("abc\x00", 8),
    ("agua", 0), ("agua", 13), ("agua", True), ("agua", 2.0),
])
def test_invalid_query_and_limit_are_rejected(tmp_path, query, limit):
    course, guard = fixture_course(tmp_path)
    with pytest.raises(CourseError):
        search_course(course, query, limit=limit, paths=guard)


def test_mutated_lesson_symlink_rejected_on_search(tmp_path):
    course, guard = fixture_course(tmp_path)
    file = course.directory / "sol.md"
    file.unlink()
    file.symlink_to(course.directory / "outros.md")
    with pytest.raises(CourseError):
        search_course(course, "solar", paths=guard)


def test_search_never_executes_nonlisted_file(tmp_path):
    course, guard = fixture_course(tmp_path)
    (course.directory / "extra.md").write_text(
        "SegredoNaoListadoNaoDeveAparecer",
        encoding="utf-8",
    )
    assert search_course(course, "SegredoNaoListadoNaoDeveAparecer", paths=guard) == []
