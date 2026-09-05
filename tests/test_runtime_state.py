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


def test_runtime_state_snapshot_default():
    controller = RuntimeStateController()

    snapshot = controller.snapshot()

    assert snapshot.mode == RuntimeMode.OFFLINE
    assert snapshot.reason is None
    assert snapshot.changed_at is None


def test_runtime_state_snapshot_after_transition():
    controller = RuntimeStateController()

    controller.transition(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    snapshot = controller.snapshot()

    assert snapshot.mode == RuntimeMode.ONLINE
    assert snapshot.reason == "Conectividade externa disponível"
    assert snapshot.changed_at == controller.changed_at


def test_runtime_state_snapshot_is_immutable():
    from dataclasses import FrozenInstanceError

    controller = RuntimeStateController()

    snapshot = controller.snapshot()

    with pytest.raises(FrozenInstanceError):
        snapshot.mode = RuntimeMode.ONLINE


def test_runtime_state_transition_if_changed_same_state_is_noop():
    controller = RuntimeStateController(
        initial_mode=RuntimeMode.OFFLINE,
        initial_reason="Conectividade externa indisponível",
    )

    changed = controller.transition_if_changed(
        RuntimeMode.OFFLINE,
        "Conectividade externa indisponível",
    )

    assert changed is False

    snapshot = controller.snapshot()

    assert snapshot.mode == RuntimeMode.OFFLINE
    assert snapshot.reason == "Conectividade externa indisponível"
    assert snapshot.changed_at is None


def test_runtime_state_transition_if_changed_performs_transition():
    controller = RuntimeStateController()

    changed = controller.transition_if_changed(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    assert changed is True

    snapshot = controller.snapshot()

    assert snapshot.mode == RuntimeMode.ONLINE
    assert snapshot.reason == "Conectividade externa disponível"
    assert snapshot.changed_at is not None


def test_runtime_state_transition_if_changed_is_atomic_for_competing_writers():
    from threading import Barrier, Thread

    controller = RuntimeStateController()

    barrier = Barrier(3)
    results = []
    errors = []

    def worker():
        try:
            barrier.wait()

            changed = controller.transition_if_changed(
                RuntimeMode.ONLINE,
                "Conectividade externa disponível",
            )

            results.append(changed)
        except Exception as exc:
            errors.append(exc)

    first = Thread(target=worker)
    second = Thread(target=worker)

    first.start()
    second.start()

    barrier.wait()

    first.join()
    second.join()

    assert errors == []
    assert sorted(results) == [False, True]

    snapshot = controller.snapshot()

    assert snapshot.mode == RuntimeMode.ONLINE
    assert snapshot.reason == "Conectividade externa disponível"
    assert snapshot.changed_at is not None


def test_runtime_state_transition_if_changed_result_on_transition():
    controller = RuntimeStateController()

    result = controller.transition_if_changed_result(
        RuntimeMode.ONLINE,
        "Conectividade externa disponível",
    )

    assert result.changed is True
    assert result.mode == RuntimeMode.ONLINE
    assert result.reason == "Conectividade externa disponível"
    assert result.changed_at is not None

    snapshot = controller.snapshot()

    assert result.mode == snapshot.mode
    assert result.reason == snapshot.reason
    assert result.changed_at == snapshot.changed_at


def test_runtime_state_transition_if_changed_result_on_noop():
    controller = RuntimeStateController(
        initial_mode=RuntimeMode.OFFLINE,
        initial_reason="Conectividade externa indisponível",
    )

    result = controller.transition_if_changed_result(
        RuntimeMode.OFFLINE,
        "Conectividade externa indisponível",
    )

    assert result.changed is False
    assert result.mode == RuntimeMode.OFFLINE
    assert result.reason == "Conectividade externa indisponível"
    assert result.changed_at is None
