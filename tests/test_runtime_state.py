from datetime import timezone
import pytest

from nexus.core.runtime import RuntimeMode
from nexus.core.runtime_state import RuntimeStateController


def test_runtime_state_default():
    controller = RuntimeStateController()

    assert controller.mode == RuntimeMode.OFFLINE
    assert controller.reason is None
    assert controller.changed_at is None


def test_runtime_state_offline_to_online():
    controller = RuntimeStateController()

    changed = controller.transition(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    assert changed is True
    assert controller.mode == RuntimeMode.ONLINE
    assert controller.reason == "Conectividade externa disponível"
    assert controller.changed_at is not None


def test_runtime_state_online_to_offline():
    controller = RuntimeStateController()

    controller.transition(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    changed = controller.transition(
        RuntimeMode.OFFLINE,
        "Conectividade externa indisponível",
    )

    assert changed is True
    assert controller.mode == RuntimeMode.OFFLINE
    assert controller.reason == "Conectividade externa indisponível"
    assert controller.changed_at is not None


def test_runtime_state_rejects_offline_to_degraded():
    controller = RuntimeStateController()

    with pytest.raises(ValueError):
        controller.transition(
            RuntimeMode.DEGRADED,
            "Serviço externo parcialmente indisponível",
        )

    assert controller.mode == RuntimeMode.OFFLINE
    assert controller.reason is None
    assert controller.changed_at is None


def test_runtime_state_rejects_online_to_degraded():
    controller = RuntimeStateController()

    controller.transition(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    with pytest.raises(ValueError):
        controller.transition(
            RuntimeMode.DEGRADED,
            "Serviço externo parcialmente indisponível",
        )

    assert controller.mode == RuntimeMode.ONLINE
    assert controller.reason == "Conectividade externa disponível"


def test_runtime_state_rejects_degraded_to_online():
    controller = RuntimeStateController(
        initial_mode=RuntimeMode.DEGRADED,
        initial_reason="Estado reservado para evolução futura",
    )

    with pytest.raises(ValueError):
        controller.transition(
            RuntimeMode.ONLINE,
            "Conectividade externa disponível",
        )

    assert controller.mode == RuntimeMode.DEGRADED
    assert controller.reason == "Estado reservado para evolução futura"


def test_runtime_state_rejects_degraded_to_offline():
    controller = RuntimeStateController(
        initial_mode=RuntimeMode.DEGRADED,
        initial_reason="Estado reservado para evolução futura",
    )

    with pytest.raises(ValueError):
        controller.transition(
            RuntimeMode.OFFLINE,
            "Conectividade externa indisponível",
        )

    assert controller.mode == RuntimeMode.DEGRADED
    assert controller.reason == "Estado reservado para evolução futura"


def test_runtime_state_rejects_same_state_transition():
    controller = RuntimeStateController()

    with pytest.raises(ValueError):
        controller.transition(
            RuntimeMode.OFFLINE,
            "Nenhuma mudança de estado",
        )

    assert controller.mode == RuntimeMode.OFFLINE
    assert controller.reason is None
    assert controller.changed_at is None


def test_runtime_state_changed_at_is_utc():
    controller = RuntimeStateController()

    controller.transition(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    assert controller.changed_at is not None
    assert controller.changed_at.tzinfo == timezone.utc


def test_runtime_state_invalid_transition_does_not_change_timestamp():
    controller = RuntimeStateController()

    controller.transition(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    original_changed_at = controller.changed_at

    with pytest.raises(ValueError):
        controller.transition(
            RuntimeMode.DEGRADED,
            "Serviço externo parcialmente indisponível",
        )

    assert controller.changed_at == original_changed_at
