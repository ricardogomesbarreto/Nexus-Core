from nexus.config.settings import settings
from nexus.core.application import NexusApplication


def test_settings():
    assert settings.app_name == "Nexus Core"
    assert settings.version == "0.1.9"


def test_application_initialization():
    app = NexusApplication()

    app.initialize()

    health = app.status()

    assert health.core is True
    assert health.configuration is True
    assert health.database is True
    assert health.logger is True
    assert health.ready is True

    app.database.close()
