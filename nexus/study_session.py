"""Sessão transitória de exercícios offline; não grava respostas em disco."""
from __future__ import annotations

from dataclasses import dataclass, field

from nexus.offline_study import StudyQuestion, check_exact_answer, generate_cloze_questions


@dataclass(frozen=True)
class StudyAttempt:
    question: StudyQuestion
    answer: str
    correct: bool


@dataclass
class StudySession:
    questions: tuple[StudyQuestion, ...]
    attempts: list[StudyAttempt] = field(default_factory=list)

    @classmethod
    def from_text(cls, text: str, *, limit: int = 5) -> "StudySession":
        return cls(tuple(generate_cloze_questions(text, limit=limit)))

    @property
    def completed(self) -> bool:
        return len(self.attempts) == len(self.questions)

    @property
    def score(self) -> tuple[int, int]:
        return sum(attempt.correct for attempt in self.attempts), len(self.attempts)

    def next_question(self) -> StudyQuestion | None:
        if self.completed:
            return None
        return self.questions[len(self.attempts)]

    def submit(self, answer: str) -> StudyAttempt:
        if not isinstance(answer, str):
            raise TypeError("answer deve ser uma string")
        if len(answer) > 1000:
            raise ValueError("resposta excede 1000 caracteres")
        question = self.next_question()
        if question is None:
            raise ValueError("sessão concluída ou sem questões")
        attempt = StudyAttempt(question, answer, check_exact_answer(question, answer))
        self.attempts.append(attempt)
        return attempt
