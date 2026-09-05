import pytest

from nexus.core.connectivity_runtime_evaluator import (
    ConnectivityRuntimeEvaluator,
)
from nexus.core.runtime import RuntimeMode


def test_evaluator_rejects_confirmation_threshold_below_two():
    with pytest.raises(ValueError):
        ConnectivityRuntimeEvaluator(
            initial_network_online=True,
            confirmation_threshold=1,
        )


@pytest.mark.parametrize(
    ("initial_network_online", "expected_mode"),
    [
        (True, RuntimeMode.ONLINE),
        (False, RuntimeMode.OFFLINE),
    ],
)
def test_evaluator_preserves_stable_observation(
    initial_network_online,
    expected_mode,
):
    evaluator = ConnectivityRuntimeEvaluator(
        initial_network_online=initial_network_online,
        confirmation_threshold=2,
    )

    result = evaluator.evaluate(initial_network_online)

    assert result.target_mode == expected_mode
    assert result.network_online is initial_network_online
    assert result.network_changed is False


def test_online_loss_enters_degraded_then_confirms_offline():
    evaluator = ConnectivityRuntimeEvaluator(
        initial_network_online=True,
        confirmation_threshold=2,
    )

    first = evaluator.evaluate(False)

    assert first.target_mode == RuntimeMode.DEGRADED
    assert first.network_online is False
    assert first.network_changed is True
    assert first.reason == (
        "Perda de conectividade aguardando confirmação"
    )

    second = evaluator.evaluate(False)

    assert second.target_mode == RuntimeMode.OFFLINE
    assert second.network_online is False
    assert second.network_changed is False
    assert second.reason == (
        "Conectividade externa indisponível"
    )


def test_offline_recovery_enters_degraded_then_confirms_online():
    evaluator = ConnectivityRuntimeEvaluator(
        initial_network_online=False,
        confirmation_threshold=2,
    )

    first = evaluator.evaluate(True)

    assert first.target_mode == RuntimeMode.DEGRADED
    assert first.network_online is True
    assert first.network_changed is True
    assert first.reason == (
        "Conectividade externa detectada; aguardando confirmação"
    )

    second = evaluator.evaluate(True)

    assert second.target_mode == RuntimeMode.ONLINE
    assert second.network_online is True
    assert second.network_changed is False
    assert second.reason == (
        "Conectividade externa disponível"
    )


def test_recovery_before_confirmation_cancels_degraded_state():
    evaluator = ConnectivityRuntimeEvaluator(
        initial_network_online=True,
        confirmation_threshold=2,
    )

    degraded = evaluator.evaluate(False)
    recovered = evaluator.evaluate(True)

    assert degraded.target_mode == RuntimeMode.DEGRADED

    assert recovered.target_mode == RuntimeMode.ONLINE
    assert recovered.network_online is True
    assert recovered.network_changed is True
    assert recovered.reason == (
        "Conectividade externa disponível"
    )


def test_network_change_is_independent_from_runtime_confirmation():
    evaluator = ConnectivityRuntimeEvaluator(
        initial_network_online=True,
        confirmation_threshold=2,
    )

    first = evaluator.evaluate(False)
    second = evaluator.evaluate(False)

    assert first.network_changed is True
    assert first.target_mode == RuntimeMode.DEGRADED

    assert second.network_changed is False
    assert second.target_mode == RuntimeMode.OFFLINE


def test_threshold_three_requires_three_consecutive_observations():
    evaluator = ConnectivityRuntimeEvaluator(
        initial_network_online=True,
        confirmation_threshold=3,
    )

    first = evaluator.evaluate(False)
    second = evaluator.evaluate(False)
    third = evaluator.evaluate(False)

    assert first.target_mode == RuntimeMode.DEGRADED
    assert second.target_mode == RuntimeMode.DEGRADED
    assert third.target_mode == RuntimeMode.OFFLINE


def test_oscillation_resets_pending_confirmation():
    evaluator = ConnectivityRuntimeEvaluator(
        initial_network_online=True,
        confirmation_threshold=3,
    )

    first_loss = evaluator.evaluate(False)
    recovery = evaluator.evaluate(True)

    second_loss = evaluator.evaluate(False)
    repeated_loss = evaluator.evaluate(False)

    assert first_loss.target_mode == RuntimeMode.DEGRADED
    assert recovery.target_mode == RuntimeMode.ONLINE

    assert second_loss.target_mode == RuntimeMode.DEGRADED
    assert repeated_loss.target_mode == RuntimeMode.DEGRADED

    confirmed_loss = evaluator.evaluate(False)

    assert confirmed_loss.target_mode == RuntimeMode.OFFLINE
