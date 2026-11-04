"""Cursos offline leves: manifesto JSON e aulas TXT/Markdown escolhidos pelo usuário.

Não executa HTML, scripts, notebooks nem servidores Kolibri. Nenhum conteúdo
é importado para PostgreSQL ou enviado ao Ollama automaticamente. Cada
leitura usa descritores de diretório/arquivo com O_NOFOLLOW no Linux.
"""
from __future__ import annotations

import json
import os
import stat
from dataclasses import dataclass
from pathlib import Path

from nexus.security.paths import PathSecurity


class CourseError(ValueError):
    """Erro de curso sem revelar conteúdos privados ou caminhos locais."""


@dataclass(frozen=True)
class CourseLesson:
    title: str
    filename: str


@dataclass(frozen=True)
class OfflineCourse:
    directory: Path
    title: str
    lessons: tuple[CourseLesson, ...]


MAX_MANIFEST = 16 * 1024
MAX_LESSONS = 20
MAX_LESSON_BYTES = 64 * 1024
MAX_COURSE_BYTES = 512 * 1024
FLAGS = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC


def _safe_file(name: object) -> bool:
    return (type(name) is str and 1 <= len(name) <= 100
            and name not in (".", "..") and "/" not in name
            and "\\" not in name and "\x00" not in name
            and not name.startswith(".") and Path(name).suffix.lower() in {".md", ".txt"})


def _read(fd: int, maximum: int) -> bytes:
    info = os.fstat(fd)
    if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= maximum:
        raise CourseError("Arquivo de curso vazio, inválido ou acima do limite.")
    data = bytearray()
    while len(data) <= maximum:
        block = os.read(fd, min(8192, maximum + 1 - len(data)))
        if not block:
            break
        data.extend(block)
    if not 0 < len(data) <= maximum:
        raise CourseError("Conteúdo de curso fora do limite.")
    return bytes(data)


def _open_read(dir_fd: int, filename: str, maximum: int) -> bytes:
    fd = os.open(filename, FLAGS, dir_fd=dir_fd)
    try:
        return _read(fd, maximum)
    finally:
        os.close(fd)


def load_course(directory: str | Path,
                paths: PathSecurity | None = None) -> OfflineCourse:
    """Inspeciona somente um course.json e metadados de no máximo 20 aulas."""
    if not isinstance(directory, (str, Path)) or not os.fspath(directory):
        raise CourseError("Escolha uma pasta local de curso.")
    guard = paths if paths is not None else PathSecurity()
    try:
        with guard.open_directory(directory) as (dir_fd, selected):
            source = _open_read(dir_fd, "course.json", MAX_MANIFEST)
            document = json.loads(source.decode("utf-8"))
            if (type(document) is not dict or set(document) !=
                    {"version", "title", "lessons"} or
                    type(document["version"]) is not int or document["version"] != 1):
                raise CourseError("O manifesto course.json precisa da versão 1.")
            title = document["title"]
            entries = document["lessons"]
            if (type(title) is not str or not 1 <= len(title.strip()) <= 120
                    or "\x00" in title or type(entries) is not list
                    or not 1 <= len(entries) <= MAX_LESSONS):
                raise CourseError("Título ou quantidade de aulas inválidos.")
            lessons = []
            seen = set()
            total = 0
            for entry in entries:
                if type(entry) is not dict or set(entry) != {"title", "file"}:
                    raise CourseError("Aula precisa de title e file.")
                lesson_title, filename = entry["title"], entry["file"]
                if (type(lesson_title) is not str
                        or not 1 <= len(lesson_title.strip()) <= 100
                        or "\x00" in lesson_title or not _safe_file(filename)
                        or filename.casefold() in seen):
                    raise CourseError("Aula de curso inválida ou repetida.")
                seen.add(filename.casefold())
                # Metadata opened with O_NOFOLLOW to reject symlinks/FIFOs.
                fd = os.open(filename, FLAGS, dir_fd=dir_fd)
                try:
                    info = os.fstat(fd)
                    if not stat.S_ISREG(info.st_mode) or not 1 <= info.st_size <= MAX_LESSON_BYTES:
                        raise CourseError("Arquivo de aula inválido ou acima de 64 KiB.")
                    total += info.st_size
                    if total > MAX_COURSE_BYTES:
                        raise CourseError("Curso acima do limite de 512 KiB.")
                finally:
                    os.close(fd)
                lessons.append(CourseLesson(lesson_title.strip(), filename))
            return OfflineCourse(selected, title.strip(), tuple(lessons))
    except CourseError:
        raise
    except (OSError, UnicodeError, ValueError, TypeError, json.JSONDecodeError) as exc:
        raise CourseError("Pasta, manifesto ou arquivos do curso indisponíveis.") from exc


def read_lesson(course: OfflineCourse, index: int,
                paths: PathSecurity | None = None) -> str:
    """Lê apenas uma aula solicitada, sem carregar todos os materiais na RAM."""
    if not isinstance(course, OfflineCourse) or type(index) is not int or not (
        0 <= index < len(course.lessons)
    ):
        raise CourseError("Aula selecionada inválida.")
    filename = course.lessons[index].filename
    if not _safe_file(filename):
        raise CourseError("Nome de aula inválido.")
    guard = paths if paths is not None else PathSecurity()
    try:
        with guard.open_directory(course.directory) as (dir_fd, _):
            data = _open_read(dir_fd, filename, MAX_LESSON_BYTES)
        text = data.decode("utf-8").replace("\r\n", "\n").strip()
        if not text or "\x00" in text:
            raise CourseError("Aula vazia ou contém dados binários.")
        return text
    except CourseError:
        raise
    except (OSError, UnicodeError, PermissionError) as exc:
        raise CourseError("Não foi possível ler a aula autorizada.") from exc
