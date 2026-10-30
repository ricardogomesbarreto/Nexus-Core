"""Cursos offline autorizados, manifestos delimitados e sem seguir symlinks."""
import json

import pytest

from nexus.security.paths import PathSecurity
from nexus.study.offline_course import (
    CourseError, MAX_COURSE_BYTES, load_course, read_lesson,
)


def policy(root):
    guard = PathSecurity()
    guard.home = root.resolve()
    guard.protected_paths = []
    return guard


def course(tmp_path, *, lessons=None, title="Aprendizagem local"):
    payload = {
        "version": 1, "title": title,
        "lessons": lessons if lessons is not None else [
            {"title": "Aula 1", "file": "inicio.md"},
            {"title": "Aula 2", "file": "continua.txt"},
        ],
    }
    (tmp_path / "course.json").write_text(
        json.dumps(payload, ensure_ascii=False), encoding="utf-8",
    )
    (tmp_path / "inicio.md").write_text(
        "A fotossíntese transforma energia luminosa em energia química.",
        encoding="utf-8",
    )
    (tmp_path / "continua.txt").write_text(
        "A água passa por evaporação e condensação durante o ciclo hidrológico.",
        encoding="utf-8",
    )
    return policy(tmp_path)


def test_course_loads_only_metadata_then_selected_lesson(tmp_path):
    guard = course(tmp_path)
    loaded = load_course(tmp_path, guard)
    assert loaded.title == "Aprendizagem local"
    assert [x.filename for x in loaded.lessons] == ["inicio.md", "continua.txt"]
    assert "fotossíntese" in read_lesson(loaded, 0, guard)
    assert "evaporação" in read_lesson(loaded, 1, guard)
    with pytest.raises(CourseError):
        read_lesson(loaded, True, guard)


def test_manifest_rejects_path_traversal_and_duplicate(tmp_path):
    for filenames in (
        ["../private.md"],
        ["dir/file.md"],
        ["file.html"],
        [".hidden.md"],
        ["inicio.md", "INICIO.MD"],
    ):
        lessons = [{"title": "Exemplo", "file": name} for name in filenames]
        guard = course(tmp_path, lessons=lessons)
        with pytest.raises(CourseError):
            load_course(tmp_path, guard)


def test_manifest_rejects_schema_version_and_size(tmp_path):
    guard = course(tmp_path)
    path = tmp_path / "course.json"
    for payload in (
        {"version": 2, "title": "x", "lessons": []},
        {"version": 1, "title": "x", "lessons": []},
        {"version": 1, "title": "x", "lessons": [{"title": "x", "file": "inicio.md"}], "commands": "rm"},
        {"version": True, "title": "x", "lessons": [{"title": "x", "file": "inicio.md"}]},
    ):
        path.write_text(json.dumps(payload), encoding="utf-8")
        with pytest.raises(CourseError):
            load_course(tmp_path, guard)
    path.write_text("x" * (16 * 1024 + 1), encoding="utf-8")
    with pytest.raises(CourseError):
        load_course(tmp_path, guard)


def test_symlinked_lesson_manifest_and_folder_rejected(tmp_path):
    actual = tmp_path / "real"
    actual.mkdir()
    guard = course(actual)
    (actual / "inicio.md").unlink()
    (actual / "inicio.md").symlink_to(actual / "continua.txt")
    guard = policy(tmp_path)
    with pytest.raises(CourseError):
        load_course(actual, guard)
    (actual / "inicio.md").unlink()
    (actual / "inicio.md").write_text("conteúdo seguro", encoding="utf-8")
    loaded = load_course(actual, guard)
    (actual / "inicio.md").unlink()
    (actual / "inicio.md").symlink_to(actual / "continua.txt")
    with pytest.raises(CourseError):
        read_lesson(loaded, 0, guard)
    (actual / "course.json").unlink()
    (actual / "course.json").symlink_to(actual / "continua.txt")
    with pytest.raises(CourseError):
        load_course(actual, guard)
    (tmp_path / "alias").symlink_to(actual, target_is_directory=True)
    with pytest.raises(CourseError):
        load_course(tmp_path / "alias", guard)


def test_lesson_limit_and_binary_rejection(tmp_path):
    guard = course(tmp_path)
    loaded = load_course(tmp_path, guard)
    (tmp_path / "inicio.md").write_bytes(b"a" * (64 * 1024 + 1))
    with pytest.raises(CourseError):
        read_lesson(loaded, 0, guard)
    (tmp_path / "inicio.md").write_bytes(b"abc\x00def")
    with pytest.raises(CourseError):
        read_lesson(loaded, 0, guard)
    assert MAX_COURSE_BYTES == 512 * 1024


def test_rejects_missing_manifest_and_empty_course(tmp_path):
    with pytest.raises(CourseError):
        load_course(tmp_path, policy(tmp_path))
    guard = course(tmp_path, lessons=[{"title": "A", "file": "missing.md"}])
    with pytest.raises(CourseError):
        load_course(tmp_path, guard)


def test_bundled_course_example_is_readable_offline():
    from nexus.config.settings import PROJECT_ROOT
    root = PROJECT_ROOT.resolve()
    demo = root / "examples" / "offline_course"
    guard = policy(root)
    loaded = load_course(demo, guard)
    assert len(loaded.lessons) == 2
    assert "Ciências" in loaded.title
    assert "fotossíntese" in read_lesson(loaded, 0, guard)
    assert "evaporação" in read_lesson(loaded, 1, guard)
