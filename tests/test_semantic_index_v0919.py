"""Opt-in PostgreSQL vector index with bounded local Ollama requests."""
import json
import os
import subprocess
import sys
from uuid import uuid4

import pytest

from nexus.config.settings import Settings
from nexus.knowledge.semantic_local import LocalSemanticReranker, SemanticSearchError
from nexus.knowledge.store import KnowledgeValidationError, PostgreSQLKnowledgeBase
from nexus.models.resource_budget import ResourceBudget
from nexus.security.paths import PathSecurity
from nexus.updates.launcher import should_run_maintenance


MODEL = "embed-local:latest"
V1 = [1.0] + [0.0] * 7
V2 = [0.0, 1.0] + [0.0] * 6


def test_index_vectors_and_model_are_validated_before_database():
    store = PostgreSQLKnowledgeBase(Settings(database_password="test"))
    for entries in ([(1, [float("nan")] * 8)], [(1, [1.0] * 8)],
                    [(1, V1), (1, V1)], [(1, V1)] * 17):
        with pytest.raises(KnowledgeValidationError):
            store.save_embeddings(1, MODEL, entries)
    with pytest.raises(KnowledgeValidationError):
        store.save_embeddings(1, "../unsafe", [(1, V1)])
    with pytest.raises(KnowledgeValidationError):
        store.search_embeddings([0.0] * 8, MODEL)


def test_embed_batch_uses_single_local_request_and_rejects_mismatch(monkeypatch):
    class FakeConnection:
        responses = []
        instances = []
        def __init__(self, host, port, *, timeout):
            assert host in ("127.0.0.1", "localhost", "::1")
            self.calls = []
            self.instances.append(self)
        def request(self, method, path, *, body=None, headers=None):
            self.calls.append((method, path, body))
        def getresponse(self):
            status, data = self.responses.pop(0)
            class Response:
                def read(self, size): return json.dumps(data).encode()
            response = Response()
            response.status = status
            return response
        def close(self): pass
    monkeypatch.setattr(ResourceBudget, "available_now_mib", lambda: 8192)
    FakeConnection.instances = []
    FakeConnection.responses = [
        (200, {"models": [{"name": MODEL, "size": 100_000_000}]}),
        (200, {"embeddings": [V1, V2]}),
    ]
    vectors = LocalSemanticReranker(connection_factory=FakeConnection).embed(
        ["primeiro", "segundo"], MODEL)
    assert vectors == [V1, V2]
    requests = [call for conn in FakeConnection.instances for call in conn.calls]
    assert len(requests) == 2
    assert json.loads(requests[1][2])["keep_alive"] == 0
    with pytest.raises(SemanticSearchError):
        LocalSemanticReranker(connection_factory=FakeConnection).embed(["x"] * 17, MODEL)


def test_index_cli_requires_model_and_does_not_check_releases():
    process = subprocess.run([sys.executable, "-m", "nexus.main", "--knowledge-index", "1"],
                             capture_output=True, timeout=10)
    assert process.returncode != 0
    assert b"embedding-model" in process.stderr
    assert not should_run_maintenance(["--knowledge-index", "1", "--embedding-model", MODEL])


@pytest.mark.skipif(not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
                    reason="PostgreSQL de teste indisponível")
def test_real_postgresql_index_search_and_cascade(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    security = PathSecurity()
    security.home = home.resolve()
    security.protected_paths = []
    config = Settings(database_name="nexus_test", database_user="nexus_test",
                      database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"])
    store = PostgreSQLKnowledgeBase(config, security)
    store.initialize()
    ids = []
    try:
        for i in range(2):
            path = home / f"{i}.md"
            path.write_text(uuid4().hex + " assunto diferente " + str(i), encoding="utf-8")
            document = store.ingest(path)
            ids.append(document.id)
            hit = store.indexable_chunks(document.id)[0]
            assert store.save_embeddings(document.id, MODEL,
                                         [(hit.chunk_id, V1 if i == 0 else V2)]) == 1
        results = store.search_embeddings(V1, MODEL, 2)
        assert store.indexed_count(MODEL) >= 2
        assert [match.hit.document_id for match in results[:2]] == ids
        assert results[0].score > results[1].score
        assert store.clear_embeddings(ids[0]) == 1
        assert all(match.hit.document_id != ids[0]
                   for match in store.search_embeddings(V1, MODEL))
        store.MAX_INDEX_ROWS = 1
        with pytest.raises(KnowledgeValidationError, match="256 trechos"):
            hit = store.indexable_chunks(ids[0])[0]
            store.save_embeddings(ids[0], MODEL, [(hit.chunk_id, V1)])
        assert store.delete(ids[1])
        assert store.search_embeddings(V1, MODEL) == []
        assert store.indexed_count(MODEL) == 0
    finally:
        for identifier in ids:
            store.delete(identifier)
        store.close()
