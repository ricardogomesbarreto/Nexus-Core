"""Opt-in semantic candidate retrieval balances keyword recall and diversity."""
import os
from uuid import uuid4

import pytest

from nexus.config.settings import Settings
from nexus.knowledge.store import PostgreSQLKnowledgeBase, KnowledgeValidationError
from nexus.security.paths import PathSecurity


@pytest.mark.parametrize("term,limit", [
    ("", 8), ("abc", 0), ("abc", 9),
    ("abc", True), ("abc", 8.0), ("x" * 161, 8),
])
def test_invalid_semantic_candidates_are_rejected_before_database(term, limit):
    store = PostgreSQLKnowledgeBase(Settings(database_password="test"))
    with pytest.raises(KnowledgeValidationError):
        store.semantic_candidates(term, limit)


def test_candidate_sampling_merges_lexical_and_diverse_documents_without_models(monkeypatch):
    store = PostgreSQLKnowledgeBase(Settings(database_password="test"))
    calls = []
    rows = [
        (1, 101, "aula-antiga.md", 3, "A fotossíntese utiliza luz."),
        (9, 901, "aula-nova.md", 0, "A produção de alimentos depende de energia."),
        (8, 801, "aula-2.md", 0, "A água passa pelo ciclo hidrológico."),
        (1, 100, "aula-antiga.md", 0, "Introdução à ciência."),
    ]

    class Cursor:
        batch = []
        def execute(self, query, parameters=None):
            calls.append((query, parameters))
            if "WHERE to_tsvector" in query:
                self.batch = rows[:1]
            elif "WHERE c.ordinal = 0" in query:
                self.batch = [rows[1], rows[2], rows[3]]
            elif "ORDER BY d.id DESC, c.ordinal ASC" in query:
                self.batch = rows[1:]
            else:
                self.batch = []
        def fetchall(self):
            return self.batch
    monkeypatch.setattr(store, "_transaction", lambda action: action(Cursor()))
    monkeypatch.setattr(store, "_audit", lambda *args, **kw: None)
    found = store.semantic_candidates("fotossíntese", 4)
    assert [h.chunk_id for h in found] == [101, 901, 801, 100]
    assert len({h.chunk_id for h in found}) == len(found)
    assert any("plainto_tsquery" in q for q, _ in calls)
    assert any("WHERE c.ordinal = 0" in q for q, _ in calls)
    assert all("http" not in q.lower() for q, _ in calls)


@pytest.mark.skipif(not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
                    reason="PostgreSQL 16 de teste indisponível")
def test_postgres_candidates_include_older_matching_document(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    guard = PathSecurity()
    guard.home = home.resolve()
    guard.protected_paths = []
    config = Settings(database_name="nexus_test", database_user="nexus_test",
                      database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"])
    store = PostgreSQLKnowledgeBase(config, guard)
    store.initialize()
    docs = []
    token = uuid4().hex
    try:
        old_file = home / "antigo.md"
        old_file.write_text(f"Fotossíntese {token}: plantas usam luz para criar açúcar.",
                            encoding="utf-8")
        old = store.ingest(old_file)
        docs.append(old)
        for n in range(10):
            recent = home / f"recente{n}.md"
            recent.write_text(
                f"Documento {n} {token[:6]} sobre oceanos e navegação marítima.",
                encoding="utf-8",
            )
            docs.append(store.ingest(recent))
        results = store.semantic_candidates(f"Fotossíntese {token}", 8)
        assert 1 <= len(results) <= 8
        assert any(item.document_id == old.id and token in item.text
                   for item in results)
        assert len({hit.chunk_id for hit in results}) == len(results)
        assert len({hit.document_id for hit in results}) >= 4
    finally:
        for doc in reversed(docs):
            store.delete(doc.id)
        store.close()
