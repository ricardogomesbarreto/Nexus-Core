"""Progresso de curso explicitamente salvo, apenas em PostgreSQL loopback.

Armazena identificador SHA-256 e índices de aulas concluídas; nunca títulos,
caminhos, textos, respostas ou notas de áudio. Nada é salvo ou restaurado sem
clique do usuário; não inicia PostgreSQL nem serviços adicionais.
"""
from __future__ import annotations

import hashlib
import json

import psycopg

from nexus.config.settings import Settings
from nexus.database.errors import DatabaseConfigurationError
from nexus.study.offline_course import OfflineCourse


class CourseProgressError(RuntimeError):
    """Erro sanitizado de acompanhamento de curso."""


def course_key(course: OfflineCourse) -> str:
    if not isinstance(course, OfflineCourse) or not 1 <= len(course.lessons) <= 20:
        raise CourseProgressError("Curso inválido para registrar progresso.")
    payload = json.dumps(
        [str(course.directory), course.title,
         [[lesson.title, lesson.filename] for lesson in course.lessons]],
        ensure_ascii=False, separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


class PostgreSQLOfflineCourseProgress:
    MAX_COURSES = 100

    def __init__(self, settings: Settings):
        if (settings.database_provider != "postgresql"
                or settings.database_host not in ("127.0.0.1", "localhost", "::1")
                or not settings.database_password):
            raise DatabaseConfigurationError("Progresso exige PostgreSQL local configurado.")
        self.settings = settings

    def _connect(self):
        s = self.settings
        return psycopg.connect(
            host=s.database_host, port=s.database_port,
            dbname=s.database_name, user=s.database_user,
            password=s.database_password,
            connect_timeout=s.database_connect_timeout,
        )

    @staticmethod
    def _schema(cursor) -> None:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nexus_offline_course_progress (
                course_key CHAR(64) PRIMARY KEY,
                completed SMALLINT[] NOT NULL DEFAULT ARRAY[]::SMALLINT[],
                updated_at TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
                CHECK (cardinality(completed) <= 20)
            )
        """)

    def save(self, course: OfflineCourse, completed: set[int]) -> int:
        key = course_key(course)
        if (type(completed) is not set or
                any(type(i) is not int or not 0 <= i < len(course.lessons)
                    for i in completed)):
            raise CourseProgressError("Aulas concluídas inválidas.")
        indexes = sorted(completed)
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    self._schema(cursor)
                    cursor.execute(
                        "INSERT INTO nexus_offline_course_progress "
                        "(course_key, completed) VALUES (%s, %s::smallint[]) "
                        "ON CONFLICT (course_key) DO UPDATE SET "
                        "completed = EXCLUDED.completed, "
                        "updated_at = CURRENT_TIMESTAMP",
                        (key, indexes),
                    )
                    cursor.execute(
                        "DELETE FROM nexus_offline_course_progress "
                        "WHERE course_key IN "
                        "(SELECT course_key FROM nexus_offline_course_progress "
                        "ORDER BY updated_at DESC, course_key OFFSET %s)",
                        (self.MAX_COURSES,),
                    )
            return len(indexes)
        except psycopg.Error as exc:
            raise CourseProgressError(
                "Falha ao salvar progresso no PostgreSQL local."
            ) from exc

    def load(self, course: OfflineCourse) -> set[int]:
        key = course_key(course)
        try:
            with self._connect() as connection:
                with connection.cursor() as cursor:
                    self._schema(cursor)
                    cursor.execute(
                        "SELECT completed FROM nexus_offline_course_progress "
                        "WHERE course_key = %s", (key,),
                    )
                    row = cursor.fetchone()
            if row is None:
                return set()
            indexes = set(int(i) for i in row[0])
            if any(not 0 <= i < len(course.lessons) for i in indexes):
                raise CourseProgressError("Progresso incompatível com o curso.")
            return indexes
        except psycopg.Error as exc:
            raise CourseProgressError(
                "Falha ao consultar progresso no PostgreSQL local."
            ) from exc
