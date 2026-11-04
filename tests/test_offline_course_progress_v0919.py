"""Progresso opt-in de curso: validação, privacidade e PostgreSQL16 real."""
import os
from uuid import uuid4

import pytest

from nexus.config.settings import Settings
from nexus.study.offline_course import CourseLesson, OfflineCourse
from nexus.study.offline_course_progress import (
    CourseProgressError, PostgreSQLOfflineCourseProgress, course_key,
)


def sample(tmp_path, title="Curso"):
    return OfflineCourse(
        tmp_path, title,
        (CourseLesson("Aula 1", "a.md"), CourseLesson("Aula 2", "b.txt")),
    )


def test_course_identifier_is_deterministic_and_never_exposes_path(tmp_path):
    value = sample(tmp_path)
    key = course_key(value)
    assert len(key) == 64
    assert key == course_key(value)
    assert str(tmp_path) not in key
    assert key != course_key(sample(tmp_path, "Outro curso"))


@pytest.mark.parametrize("result", [
    {True}, {-1}, {2}, {"0"}, {0, 2}, {0.0},
])
def test_reject_invalid_completed_lessons_without_database(tmp_path, result):
    store = PostgreSQLOfflineCourseProgress(Settings(database_password="dummy"))
    with pytest.raises(CourseProgressError):
        store.save(sample(tmp_path), result)


def test_nonlocal_database_provider_rejected():
    with pytest.raises(Exception):
        PostgreSQLOfflineCourseProgress(Settings(
            database_host="example.com", database_password="dummy",
        ))


@pytest.mark.skipif(not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
                    reason="PostgreSQL local de teste não está configurado")
def test_real_postgres_progress_save_load_clear_and_no_plaintext(tmp_path):
    import psycopg

    settings = Settings(
        database_name="nexus_test", database_user="nexus_test",
        database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"],
    )
    value = sample(tmp_path, "Curso " + uuid4().hex)
    store = PostgreSQLOfflineCourseProgress(settings)
    key = course_key(value)
    try:
        assert store.load(value) == set()
        assert store.save(value, {1}) == 1
        assert store.load(value) == {1}
        assert store.save(value, {0, 1}) == 2
        assert store.load(value) == {0, 1}
        with psycopg.connect(
            host="127.0.0.1", dbname="nexus_test",
            user="nexus_test", password=settings.database_password,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "SELECT course_key, completed FROM nexus_offline_course_progress "
                    "WHERE course_key = %s", (key,),
                )
                row = cursor.fetchone()
                assert row[0].strip() == key
                assert row[1] == [0, 1]
                assert str(tmp_path) not in str(row)
                assert value.title not in str(row)
        assert store.save(value, set()) == 0
        assert store.load(value) == set()
    finally:
        with psycopg.connect(
            host="127.0.0.1", dbname="nexus_test",
            user="nexus_test", password=settings.database_password,
        ) as conn:
            with conn.cursor() as cursor:
                cursor.execute(
                    "DELETE FROM nexus_offline_course_progress WHERE course_key = %s",
                    (key,),
                )
