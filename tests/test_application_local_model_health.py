import nexus.core.application as application_module

from nexus.core.application import NexusApplication
from tests.fakes import FakeDatabase
from nexus.monitoring.health import HealthStatus


def test_health_local_model_layer_defaults_not_ready():
    health = HealthStatus()

    assert health.local_model_layer is False


def test_health_ready_requires_local_model_layer():
    health = HealthStatus(
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

    assert health.ready is False


def test_health_ready_with_local_model_layer():
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
    )

    assert health.ready is True


def test_application_initializes_local_model_layer_without_building_router(
    monkeypatch,
):
    calls = []

    def fake_build_model_router(settings):
        calls.append(settings)
        raise AssertionError(
            "initialize() não deve construir o ModelRouter"
        )

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
    )

    app = NexusApplication(
        database=FakeDatabase(),
    )

    try:
        assert app.health.local_model_layer is False

        app.initialize()

        assert app.health.local_model_layer is True
        assert calls == []
        assert app._model_router is None
    finally:
        app.shutdown()
