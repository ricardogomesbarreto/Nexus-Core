"""Busca textual local em aulas autorizadas, sem banco, rede ou servidor.

Apenas quando solicitada, percorre ate 20 arquivos TXT/MD do manifesto
previamente validado; o total de material e limitado a 512 KiB por curso.
Os resultados sao referencias ao titulo, numero da aula e excertos, nunca
um indice persistente.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass

from nexus.security.paths import PathSecurity
from nexus.study.offline_course import OfflineCourse, CourseError, read_lesson

MAX_QUERY = 120
MAX_RESULTS = 12
MAX_SNIPPET = 180


@dataclass(frozen=True)
class CourseSearchHit:
    lesson_index: int
    lesson_title: str
    excerpt: str


def _normalized(value: str) -> str:
    # Match accents and case, but leave the displayed source untouched.
    folded = unicodedata.normalize("NFD", value.casefold())
    return "".join(ch for ch in folded if unicodedata.category(ch) != "Mn")


def search_course(
    course: OfflineCourse, query: str, *,
    limit: int = 8, paths: PathSecurity | None = None,
) -> list[CourseSearchHit]:
    """Busca exata tolerante a acentos nas aulas, sem carregar modelos.

    Nao executa comandos nem percorre diretorios nao descritos no manifesto.
    Limitacoes de arquivo/permissoes sao impostas por read_lesson em cada aula.
    """
    if not isinstance(course, OfflineCourse) or not 1 <= len(course.lessons) <= 20:
        raise CourseError("Curso local invalido para pesquisa.")
    if (not isinstance(query, str) or not 2 <= len(query.strip()) <= MAX_QUERY
            or "\x00" in query or "\n" in query or "\r" in query):
        raise CourseError("Pesquisa deve ter de 2 a 120 caracteres em uma linha.")
    if type(limit) is not int or not 1 <= limit <= MAX_RESULTS:
        raise CourseError("Limite de resultados da pesquisa invalido.")

    needle = _normalized(" ".join(query.strip().split()))
    results: list[CourseSearchHit] = []
    for index, lesson in enumerate(course.lessons):
        text = read_lesson(course, index, paths)
        # Match across whitespace in one logical line while retaining source.
        # Never build an index or store searched texts past this call.
        for paragraph in re.split(r"\n\s*\n", text):
            if not paragraph.strip():
                continue
            single = " ".join(paragraph.split())
            if needle not in _normalized(single):
                continue
            # Display only a bounded excerpt around a match.
            # Since normalized text can have differing codepoint lengths,
            # show the beginning of the matched paragraph without unsafe
            # Unicode offsets or revealing unrelated files.
            excerpt = single[:MAX_SNIPPET]
            if len(single) > MAX_SNIPPET:
                excerpt = excerpt.rstrip() + "…"
            results.append(CourseSearchHit(index, lesson.title, excerpt))
            if len(results) >= limit:
                return results
    return results
