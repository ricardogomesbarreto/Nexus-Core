"""Busca semântica: somente loopback, modelo instalado e limites definidos."""
import json
from types import SimpleNamespace

import pytest

from nexus.knowledge.semantic_local import LocalSemanticReranker, SemanticSearchError
from nexus.models.resource_budget import ResourceBudget


@pytest.fixture(autouse=True)
def enough_test_memory(monkeypatch):
    monkeypatch.setattr(ResourceBudget, "available_now_mib", lambda: 8192)


class FakeConnection:
    instances = []
    responses = []

    def __init__(self, host, port, *, timeout):
        assert host in ("127.0.0.1", "localhost", "::1")
        self.calls = []
        self.host = host
        self.port = port
        self.timeout = timeout
        self.instances.append(self)

    def request(self, method, path, *, body=None, headers=None):
        self.calls.append((method, path, body))

    def getresponse(self):
        data = self.responses.pop(0)
        class Response:
            status = data[0]
            def read(self, size): return json.dumps(data[1]).encode()
        return Response()

    def close(self): pass


def hits():
    return [
        SimpleNamespace(text="O sol é uma estrela.", chunk_id=1),
        SimpleNamespace(text="O futebol é um esporte.", chunk_id=2),
    ]


def test_semantic_rerank_with_installed_small_model():
    FakeConnection.instances = []
    FakeConnection.responses = [
        (200, {"models": [{"name": "embed-local:latest", "size": 200_000_000}]}),
        (200, {"embeddings": [
            [1, 0, 0, 0, 0, 0, 0, 0],
            [0.9, 0.1, 0, 0, 0, 0, 0, 0],
            [0.1, 0.9, 0, 0, 0, 0, 0, 0],
        ]}),
    ]
    matches = LocalSemanticReranker(connection_factory=FakeConnection).rerank(
        "O que é o sol?", hits(), "embed-local:latest",
    )
    assert [m.hit.chunk_id for m in matches] == [1, 2]
    assert matches[0].score > matches[1].score
    commands = [call for instance in FakeConnection.instances for call in instance.calls]
    assert [x[:2] for x in commands] == [
        ("GET", "/api/tags"), ("POST", "/api/embed"),
    ]
    payload = json.loads(commands[1][2])
    assert payload["keep_alive"] == 0 and payload["truncate"] is False
    assert len(payload["input"]) == 3


def test_not_installed_or_model_too_large_never_embeddings():
    for model in (None, "embed-small"):
        FakeConnection.instances = []
        FakeConnection.responses = [(200, {"models": [
            {"name": "embed-small", "size": 2_000_000_000},
        ]})]
        search = LocalSemanticReranker(connection_factory=FakeConnection)
        with pytest.raises(SemanticSearchError):
            search.rerank("tema", hits(), model or "other-model")
        assert sum(len(c.calls) for c in FakeConnection.instances) == 1


@pytest.mark.parametrize("query,model,data", [
    ("", "embed-small", hits()),
    ("algo", "../unsafe", hits()),
    ("algo", "embed-small", []),
    ("algo", "embed-small", hits() * 5),
    ("algo", "embed-small", [SimpleNamespace(text="x" * 1001)]),
])
def test_invalid_inputs_are_rejected_without_model_request(query, model, data):
    search = LocalSemanticReranker(connection_factory=FakeConnection)
    with pytest.raises(SemanticSearchError):
        search.rerank(query, data, model)


def test_bad_vectors_rejected():
    FakeConnection.responses = [
        (200, {"models": [{"name": "embed-small", "size": 100}]}),
        (200, {"embeddings": [[1] * 8, [float("nan")] * 8, [2] * 8]}),
    ]
    with pytest.raises(SemanticSearchError):
        LocalSemanticReranker(connection_factory=FakeConnection).rerank(
            "tema", hits(), "embed-small",
        )


def test_low_memory_blocks_optional_embedding_before_loading(monkeypatch):
    FakeConnection.instances = []
    FakeConnection.responses = [
        (200, {"models": [{"name": "embed-small", "size": 500_000_000}]}),
    ]
    monkeypatch.setattr(ResourceBudget, "available_now_mib", lambda: 200)
    with pytest.raises(SemanticSearchError, match="Memória"):
        LocalSemanticReranker(connection_factory=FakeConnection).rerank(
            "tema", hits(), "embed-small"
        )
    assert sum(len(item.calls) for item in FakeConnection.instances) == 1
