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
        runtime_reason="Serviço externo parcialmente indisponível",
    )

    assert health.network_online is True
    assert health.runtime_mode == RuntimeMode.DEGRADED
    assert health.runtime_reason == "Serviço externo parcialmente indisponível"
