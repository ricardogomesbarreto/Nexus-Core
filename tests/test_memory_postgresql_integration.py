"""Real PostgreSQL integration: persistence across sessions and lifecycle."""

import os
from uuid import uuid4

import psycopg
import pytest

from nexus.config.settings import Settings
from nexus.memory.store import PostgreSQLMemoryStore


pytestmark = pytest.mark.skipif(
    not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
    reason="PostgreSQL 16 test service is required",
)


def memory_settings():
    return Settings(
        database_host="127.0.0.1",
        database_name="nexus_test",
        database_user="nexus_test",
        database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"],
    )


def test_real_memory_crud_retention_and_metadata_only_audit():
    store = PostgreSQLMemoryStore(memory_settings())
    store.initialize()
    prefix = str(uuid4())
    try:
        store.clear()
        first = store.add(f"{prefix} gosta de azul %", retention_days=7)
        second = store.add(f"{prefix} prefere alpha_beta", retention_days=30)
        third = store.add(f"{prefix} prefere alphaXbeta", retention_days=30)
        assert first.id < second.id < third.id
        assert first.content.endswith("%")
        assert first.expires_at > first.created_at
        assert [x.id for x in store.list_entries()] == [third.id, second.id, first.id]
        assert [x.id for x in store.search("alpha_beta")] == [second.id]
        assert [x.id for x in store.search("%")] == [first.id]
        assert store.search("' OR 1=1 --") == []
        assert store.delete(second.id)
        assert not store.delete(second.id)
        assert {row.id for row in store.list_entries()} == {first.id, third.id}
        metrics = store.stats()
        assert metrics["active"] == 2
        assert metrics["audit_events"] >= 1
        with psycopg.connect(
            host="127.0.0.1", dbname="nexus_test", user="nexus_test",
            password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"],
        ) as verify:
            with verify.cursor() as cur:
                cur.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'nexus_memory_audit'"
                )
                columns = {row[0] for row in cur.fetchall()}
                assert "content" not in columns
                assert "query" not in columns
        store.close()
        store.initialize()
        assert {row.id for row in store.list_entries()} == {first.id, third.id}
        with store._connection.cursor() as cur:
            cur.execute(
                "UPDATE nexus_memories SET created_at = CURRENT_TIMESTAMP - "
                "INTERVAL '3 days', expires_at = CURRENT_TIMESTAMP - "
                "INTERVAL '1 day' WHERE id = %s",
                (first.id,),
            )
        store._connection.commit()
        assert store.purge_expired() == 1
        assert all(entry.id != first.id for entry in store.list_entries())
        assert store.clear() == 1
        assert store.list_entries() == []
    finally:
        store.clear()
        store.close()


def test_explicit_memory_transaction_commits_and_survives_restart():
    store = PostgreSQLMemoryStore(memory_settings())
    store.initialize()
    key = f"mem-{uuid4()}"
    try:
        created = store.add(key)
        store.close()
        store.initialize()
        assert any(m.id == created.id for m in store.search(key))
        assert store.delete(created.id)
        store.close()
        store.initialize()
        assert store.search(key) == []
    finally:
        store.close()
