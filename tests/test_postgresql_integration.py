import os
from uuid import uuid4

import psycopg
import pytest

from nexus.database.postgresql import PostgreSQLProvider


@pytest.mark.skipif(
    not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
    reason="Servidor PostgreSQL de teste não configurado",
)
def test_postgresql_real_lifecycle_and_event_persistence():
    password = os.environ["NEXUS_TEST_POSTGRES_PASSWORD"]
    provider = PostgreSQLProvider(
        host="127.0.0.1",
        port=5432,
        database="nexus_test",
        user="nexus_test",
        password=password,
        connect_timeout=5.0,
    )
    message = f"integration-{uuid4()}"

    try:
        provider.initialize()
        assert provider.healthcheck()
        provider.add_event("TEST", message)

        with psycopg.connect(
            host="127.0.0.1",
            port=5432,
            dbname="nexus_test",
            user="nexus_test",
            password=password,
        ) as verifier:
            with verifier.cursor() as cursor:
                cursor.execute(
                    "SELECT event_type FROM system_events WHERE message = %s",
                    (message,),
                )
                assert cursor.fetchone() == ("TEST",)
    finally:
        provider.close()
    assert not provider.initialized
