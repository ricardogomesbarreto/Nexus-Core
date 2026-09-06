import pytest

from nexus.core.runtime import RuntimeMode
from nexus.monitoring.health import HealthStatus


def test_health_default_runtime():
    health = HealthStatus()

    assert health.network_online is False
    assert health.runtime_mode == RuntimeMode.OFFLINE
    assert health.runtime_reason is None


def test_health_offline_is_still_ready():
    health = HealthStatus(
        core=True,
        configuration=True,
        database=True,
        logger=True,
        event_bus=True,
        security_gate=True,
        tool_registry=True,
        terminal_sandbox=True,
        local_model_layer=True,
        network_online=False,
        runtime_mode=RuntimeMode.OFFLINE,
    )

    assert health.ready is True


def test_health_online():
    health = HealthStatus(
        network_online=True,
        runtime_mode=RuntimeMode.ONLINE,
        runtime_reason="Conectividade externa disponível",
    )

    assert health.network_online is True
    assert health.runtime_mode == RuntimeMode.ONLINE
    assert health.runtime_reason == "Conectividade externa disponível"


def test_health_degraded():
    health = HealthStatus(
        network_online=True,
        runtime_mode=RuntimeMode.DEGRADED,
        runtime_reason="Mudança de conectividade aguardando confirmação",
    )

    assert health.network_online is True
    assert health.runtime_mode == RuntimeMode.DEGRADED
    assert health.runtime_reason == "Mudança de conectividade aguardando confirmação"


def test_health_runtime_snapshot_default():
    health = HealthStatus()

    snapshot = health.runtime_snapshot()

    assert snapshot.network_online is False
    assert snapshot.runtime_mode == RuntimeMode.OFFLINE
    assert snapshot.runtime_reason is None


def test_health_update_runtime_updates_state_atomically():
    health = HealthStatus()

    health.update_runtime(
        network_online=True,
        runtime_mode=RuntimeMode.ONLINE,
        runtime_reason="Conectividade externa disponível",
    )

    snapshot = health.runtime_snapshot()

    assert snapshot.network_online is True
    assert snapshot.runtime_mode == RuntimeMode.ONLINE
    assert snapshot.runtime_reason == (
        "Conectividade externa disponível"
    )

    # Compatibilidade com a API pública existente.
    assert health.network_online is True
    assert health.runtime_mode == RuntimeMode.ONLINE
    assert health.runtime_reason == (
        "Conectividade externa disponível"
    )


def test_health_runtime_snapshot_is_immutable():
    from dataclasses import FrozenInstanceError

    health = HealthStatus()

    snapshot = health.runtime_snapshot()

    with pytest.raises(FrozenInstanceError):
        snapshot.network_online = True
