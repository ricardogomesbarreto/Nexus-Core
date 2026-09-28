import pytest

from nexus.config.settings import Settings
from nexus.database.errors import DatabaseConfigurationError


def test_build_database_provider_requires_password():
    from nexus.database.factory import build_database_provider

    settings = Settings(
        database_password=None,
    )

    with pytest.raises(
        DatabaseConfigurationError,
        match="NEXUS_DATABASE_PASSWORD",
    ):
        build_database_provider(settings)


def test_build_database_provider_rejects_unsupported_provider():
    from nexus.database.factory import build_database_provider

    settings = Settings(
        database_provider="mysql",
        database_password="test-secret",
    )

    with pytest.raises(
        DatabaseConfigurationError,
        match="database provider",
    ):
        build_database_provider(settings)


def test_build_database_provider_creates_postgresql_provider(
    monkeypatch,
):
    from nexus.database import factory

    captured = {}

    class FakePostgreSQLProvider:
        provider_id = "postgresql"

        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(
        factory,
        "PostgreSQLProvider",
        FakePostgreSQLProvider,
    )

    settings = Settings(
        database_provider="postgresql",
        database_host="127.0.0.1",
        database_port=5432,
        database_name="nexus",
        database_user="nexus",
        database_password="test-secret",
        database_connect_timeout=5,
    )

    provider = factory.build_database_provider(settings)

    assert provider.provider_id == "postgresql"
    assert captured == {
        "host": "127.0.0.1",
        "port": 5432,
        "database": "nexus",
        "user": "nexus",
        "password": "test-secret",
        "connect_timeout": 5,
    }
