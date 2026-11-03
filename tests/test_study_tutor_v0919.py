"""Nível de estudo explícito, baseado em fontes, sem persistência."""
import pytest

from nexus.study.tutor import LEVELS, TutorValidationError, tutor_question


@pytest.mark.parametrize("level", tuple(LEVELS))
def test_tutor_levels_fit_local_answer_limit(level):
    prompt = tutor_question("algoritmos", level)
    assert len(prompt) <= 160
    assert "3 etapas" in prompt
    assert "fontes" in prompt.lower()


@pytest.mark.parametrize("topic,level", [
    ("", "Iniciante"), ("a" * 66, "Iniciante"),
    ("matemática", "inexistente"), ("tema\x00", "Iniciante"),
])
def test_invalid_tutor_input_rejected(topic, level):
    with pytest.raises(TutorValidationError):
        tutor_question(topic, level)
