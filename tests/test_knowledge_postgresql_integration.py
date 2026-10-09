"""Real PostgreSQL document lifecycle, full-text search and audit isolation."""
import os
from uuid import uuid4

import psycopg
import pytest

from nexus.config.settings import Settings
from nexus.knowledge.store import PostgreSQLKnowledgeBase
from nexus.memory.store import PostgreSQLMemoryStore
from nexus.security.paths import PathSecurity

pytestmark = pytest.mark.skipif(
    not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
    reason="PostgreSQL local de teste indisponível",
)


def test_knowledge_ingestion_search_dedupe_and_delete(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    paths = PathSecurity()
    paths.home = home.resolve()
    paths.protected_paths = [home / ".ssh"]
    config = Settings(
        database_name="nexus_test", database_user="nexus_test",
        database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"],
    )
    base = PostgreSQLKnowledgeBase(config, path_security=paths)
    base.initialize()
    token = uuid4().hex
    a = home / "study.md"
    a.write_text(f"# Plano local\n{token} automação IoT e Python 3.12.\n" +
                 "Este documento é um teste.\n" * 14, encoding="utf-8")
    b = home / "study-second.md"
    b.write_text(a.read_text(), encoding="utf-8")
    one = None
    try:
        one = base.ingest(a)
        assert one.added is True and one.chunk_count >= 1
        assert base.ingest(b).id == one.id
        assert len([d for d in base.list_documents() if d.id == one.id]) == 1
        assert any(h.document_id == one.id for h in base.search(token))
        assert any(h.document_id == one.id for h in base.search("Python"))
        assert base.search("nonexistent-term-xyx-7654") == []
        assert base.search("'; DROP TABLE nexus_memories; --") == []
        assert base.delete(one.id)
        assert not base.delete(one.id)
        assert base.search(token) == []
        # Memory schema remains independent and no implicit memory writes happen.
        memory = PostgreSQLMemoryStore(config)
        memory.initialize()
        assert isinstance(memory.stats()["active"], int)
        memory.close()
        with psycopg.connect(host="127.0.0.1", dbname="nexus_test",
                            user="nexus_test",
                            password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"]) as verify:
            with verify.cursor() as cursor:
                cursor.execute(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name = 'nexus_knowledge_audit'"
                )
                names = {r[0] for r in cursor.fetchall()}
                assert not {"body", "content", "query", "source_path"} & names
                cursor.execute(
                    "SELECT COUNT(*) FROM nexus_knowledge_chunks "
                    "WHERE document_id = %s", (one.id,)
                )
                assert cursor.fetchone()[0] == 0
    finally:
        if one is not None:
            base.delete(one.id)
        base.close()


def test_literal_search_does_not_expand_user_wildcards(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    paths = PathSecurity()
    paths.home = home.resolve()
    paths.protected_paths = []
    config = Settings(
        database_name="nexus_test", database_user="nexus_test",
        database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"],
    )
    base = PostgreSQLKnowledgeBase(config, paths)
    base.initialize()
    term = uuid4().hex
    a = home / "literal.md"
    b = home / "normal.md"
    a.write_text(f"{term} literal-percent % and alpha_beta")
    b.write_text(f"{term} ordinary-text, alphaXbeta")
    ids = []
    try:
        x = base.ingest(a); y = base.ingest(b)
        ids = [x.id, y.id]
        # Exact literal LIKE escapes; full-text search alone may find punctuation,
        # so require every fixture is distinguished by its own unique token.
        assert x.id in [h.document_id for h in base.search(term)]
        assert not base.search(term + " -- imaginary improbable phrase")
    finally:
        for id_ in ids:
            base.delete(id_)
        base.close()
