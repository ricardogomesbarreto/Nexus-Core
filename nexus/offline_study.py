"""Gerador determinístico e offline de exercícios baseados em trechos autorizados.

Não consulta rede, modelos de IA ou banco; não persiste dados. O chamador
deve obter o trecho da biblioteca somente após autorização do usuário.
"""
from __future__ import annotations

import re
from dataclasses import dataclass

_MAX_TEXT = 16000
_MAX_QUESTIONS = 10
_SENTENCE = re.compile(r"(?<=[.!?])\\s+")


@dataclass(frozen=True)
class StudyQuestion:
    prompt: str
    expected_answer: str
    source_excerpt: str


def generate_cloze_questions(text: str, *, limit: int = 5) -> list[StudyQuestion]:
    """Cria questões de lacuna verificáveis; não inventa fatos nem avalia alunos."""
    if not isinstance(text, str):
        raise TypeError("text deve ser uma string")
    if not isinstance(limit, int) or isinstance(limit, bool) or not 1 <= limit <= _MAX_QUESTIONS:
        raise ValueError("limit deve estar entre 1 e 10")
    if len(text) > _MAX_TEXT:
        raise ValueError("trecho excede o limite de 16000 caracteres")
    questions: list[StudyQuestion] = []
    seen: set[str] = set()
    for sentence in _SENTENCE.split(re.sub(r"\\s+", " ", text).strip()):
        if not 30 <= len(sentence) <= 350:
            continue
        candidates = re.findall(r"(?u)\\b[^\\W\\d_][\\wÀ-ÿ-]{5,}\\b", sentence)
        if not candidates:
            continue
        answer = max(candidates, key=lambda word: (len(word), word.casefold()))
        key = sentence.casefold()
        if key in seen:
            continue
        seen.add(key)
        start = re.search(r"(?<!\\w)" + re.escape(answer) + r"(?!\\w)", sentence)
        if start is None:
            continue
        question = sentence[:start.start()] + "_____" + sentence[start.end():]
        questions.append(StudyQuestion(
            prompt="Complete a lacuna conforme o material: " + question,
            expected_answer=answer,
            source_excerpt=sentence,
        ))
        if len(questions) >= limit:
            break
    return questions


def check_exact_answer(question: StudyQuestion, answer: str) -> bool:
    """Compara somente a resposta literal; não faz avaliação semântica."""
    if not isinstance(answer, str):
        return False
    return answer.strip().casefold() == question.expected_answer.strip().casefold()
