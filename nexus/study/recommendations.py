"""Recomendação determinística e transparente de estudo, somente a pedido.

Sem diagnóstico educacional, perfil sensível, rede, modelo nem alteração
automática de nível. Usa apenas notas agregadas da sessão atual ou histórico
local que o usuário já optou por salvar.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable


@dataclass(frozen=True)
class StudyRecommendation:
    level: str
    accuracy_percent: int
    questions: int
    action: str


def recommend_study_step(results: Iterable[tuple[int, int]]) -> StudyRecommendation:
    """Calcula tendência nos últimos dez resultados válidos e sugere uma ação."""
    items = list(results)
    if len(items) > 20:
        raise ValueError("São aceitos até 20 resultados.")
    for correct, total in items:
        if (type(correct) is not int or type(total) is not int
                or not 1 <= total <= 10 or not 0 <= correct <= total):
            raise ValueError("Pontuação inválida.")
    recent = items[-10:]
    questions = sum(total for _, total in recent)
    correct = sum(hit for hit, _ in recent)
    accuracy = round(100 * correct / questions) if questions else 0
    if questions < 5:
        return StudyRecommendation(
            "Iniciante", accuracy, questions,
            "Pratique ao menos cinco questões antes de avaliar o avanço.",
        )
    if accuracy < 60:
        return StudyRecommendation(
            "Iniciante", accuracy, questions,
            "Revise o material-fonte e refaça exercícios de compreensão.",
        )
    if accuracy < 85:
        return StudyRecommendation(
            "Intermediário", accuracy, questions,
            "Relacione os conceitos e pratique exemplos de aplicação.",
        )
    return StudyRecommendation(
        "Avançado", accuracy, questions,
        "Tente explicar limitações e resolver problemas mais complexos.",
    )
