from unittest.mock import MagicMock

from nexus.core.application import NexusApplication


def test_application_uses_injected_database_without_initializing_it():
    database = MagicMock()

    app = NexusApplication(
        database=database,
    )

    assert app.database is database
    database.initialize.assert_not_called()
    database.healthcheck.assert_not_called()
    database.add_event.assert_not_called()
    database.close.assert_not_called()
