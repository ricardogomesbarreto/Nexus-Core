from nexus.core.runtime import RuntimeMode, RuntimeStatus


def test_runtime_modes():
    assert RuntimeMode.ONLINE.value == "ONLINE"
    assert RuntimeMode.OFFLINE.value == "OFFLINE"
    assert RuntimeMode.DEGRADED.value == "DEGRADED"


def test_runtime_status_default():
    status = RuntimeStatus()

    assert status.mode == RuntimeMode.OFFLINE
    assert status.reason is None


def test_runtime_status_online():
    status = RuntimeStatus(
        mode=RuntimeMode.ONLINE,
        reason="Conectividade externa disponível",
    )

    assert status.mode == RuntimeMode.ONLINE
    assert status.reason == "Conectividade externa disponível"


def test_runtime_status_degraded():
    status = RuntimeStatus(
        mode=RuntimeMode.DEGRADED,
        reason="Serviço externo parcialmente indisponível",
    )

    assert status.mode == RuntimeMode.DEGRADED
    assert status.reason == "Serviço externo parcialmente indisponível"
