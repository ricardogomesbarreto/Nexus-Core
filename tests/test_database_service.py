from unittest.mock import MagicMock

import pytest

from nexus.database.database import Database
from nexus.database.errors import DatabaseConnectionError


def build_provider():
    provider = MagicMock()
    provider.provider_id = "postgresql"
    provider.healthcheck.return_value = True
    return provider


def test_database_construction_does_not_initialize_provider():
    provider = build_provider()

    database = Database(provider)

    assert database.provider_id == "postgresql"
    provider.initialize.assert_not_called()
    provider.healthcheck.assert_not_called()


def test_database_initialize_initializes_and_validates_provider():
    provider = build_provider()
    database = Database(provider)

    database.initialize()

    provider.initialize.assert_called_once_with()
    provider.healthcheck.assert_called_once_with()


def test_database_initialize_rejects_failed_healthcheck():
    provider = build_provider()
    provider.healthcheck.return_value = False

    database = Database(provider)

    with pytest.raises(
        DatabaseConnectionError,
        match="healthcheck",
    ):
        database.initialize()


def test_database_healthcheck_delegates_to_provider():
    provider = build_provider()
    database = Database(provider)

    assert database.healthcheck() is True
    provider.healthcheck.assert_called_once_with()


def test_database_add_event_delegates_to_provider():
    provider = build_provider()
    database = Database(provider)

    database.add_event(
        "system.start",
        "Nexus Core inicializado",
    )

    provider.add_event.assert_called_once_with(
        "system.start",
        "Nexus Core inicializado",
    )


def test_database_close_delegates_to_provider():
    provider = build_provider()
    database = Database(provider)

    database.close()

    provider.close.assert_called_once_with()
