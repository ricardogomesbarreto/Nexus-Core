from nexus.config.settings import load_settings
from nexus.core.application import NexusApplication
from tests.fakes import FakeDatabase


def test_settings():
    settings = load_settings({})

    assert settings.app_name == "Nexus Core"
    assert settings.version == "0.7.1"
    assert settings.connectivity_monitor_interval == 30.0
    assert settings.connectivity_confirmation_threshold == 2


def test_application_initialization():
    app = NexusApplication(
        database=FakeDatabase(),
    )

    app.initialize()

    health = app.status()

    assert health.core is True
    assert health.configuration is True
    assert health.database is True
    assert health.logger is True
    assert health.ready is True

    app.shutdown()
