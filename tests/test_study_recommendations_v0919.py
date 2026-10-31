"""Aconselhamento pedagógico determinístico, sem diagnóstico ou perfil oculto."""
import pytest

from nexus.study.recommendations import recommend_study_step


@pytest.mark.parametrize("history,level,accuracy", [
    ([], "Iniciante", 0),
    ([(2, 2)], "Iniciante", 100),
    ([(0, 5)], "Iniciante", 0),
    ([(3, 5)], "Intermediário", 60),
    ([(4, 5)], "Intermediário", 80),
    ([(5, 5)], "Avançado", 100),
    ([(0, 5), (5, 5)], "Intermediário", 50),
])
def test_recommendation_is_bounded_and_transparent(history, level, accuracy):
    result = recommend_study_step(history)
    if history == [(0, 5), (5, 5)]:
        assert result.level == "Iniciante"  # under 60% after ten questions
        assert result.accuracy_percent == 50
    else:
        assert result.level == level
        assert result.accuracy_percent == accuracy
    assert result.action
    assert result.questions == sum(total for _, total in history)


def test_only_last_ten_sessions_contribute():
    history = [(0, 5)] * 10 + [(5, 5)] * 10
    result = recommend_study_step(history)
    assert result.level == "Avançado"
    assert result.questions == 50
    assert result.accuracy_percent == 100


@pytest.mark.parametrize("results", [
    [(True, 1)], [(0, True)], [(-1, 5)], [(3, 2)],
    [(0, 0)], [(11, 11)], [(2, 11)], [(1, 2)] * 21,
])
def test_invalid_results_do_not_produce_a_level(results):
    with pytest.raises(ValueError):
        recommend_study_step(results)
