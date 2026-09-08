from nexus.monitoring.health import HealthStatus


def make_ready_health():
    return HealthStatus(
        core=True,
        configuration=True,
        database=True,
        logger=True,
        event_bus=True,
        security_gate=True,
        tool_registry=True,
        terminal_sandbox=True,
        local_model_layer=False,
    )


def test_model_layer_defaults_not_ready():
    health = HealthStatus()

    assert health.model_layer is False


def test_model_layer_alias_reads_legacy_state():
    health = HealthStatus(
        local_model_layer=True,
    )

    assert health.model_layer is True


def test_model_layer_alias_updates_legacy_state():
    health = HealthStatus()

    health.model_layer = True

    assert health.model_layer is True
    assert health.local_model_layer is True


def test_legacy_model_layer_updates_generic_state():
    health = HealthStatus()

    health.local_model_layer = True

    assert health.model_layer is True


def test_ready_uses_same_model_layer_state():
    health = make_ready_health()

    assert health.ready is False

    health.model_layer = True

    assert health.ready is True
    assert health.local_model_layer is True
