"""Busca semântica *opt-in* usando embeddings Ollama locais.

Não baixa modelos, não inicia Ollama e não faz requisições externas.
O índice opcional é persistido apenas pelo armazenamento PostgreSQL.
"""
from __future__ import annotations

import http.client
import json
import math
import re
from dataclasses import dataclass
from urllib.parse import urlsplit

from nexus.config.local_endpoint import normalize_local_http_origin
from nexus.models.resource_budget import ResourceBudget


class SemanticSearchError(RuntimeError):
    """Falha sanitizada de pesquisa semântica offline."""


@dataclass(frozen=True)
class SemanticMatch:
    hit: object
    score: float


class LocalSemanticReranker:
    MAX_CHUNKS = 8
    MAX_EMBED_INPUTS = 16
    MAX_MODEL_SIZE = 900 * 1024 * 1024
    MAX_EMBED_REPLY = 1024 * 1024
    MODEL_NAME = re.compile(r"[A-Za-z0-9][A-Za-z0-9_.:/+-]{0,95}\Z")

    def __init__(self, origin="http://127.0.0.1:11434",
                 connection_factory=http.client.HTTPConnection):
        normalized = normalize_local_http_origin(origin)
        parsed = urlsplit(normalized)
        self._host = parsed.hostname
        self._port = parsed.port or 80
        self._connection_factory = connection_factory

    def _request(self, method: str, resource: str, payload=None, *, max_bytes=262144):
        conn = self._connection_factory(self._host, self._port, timeout=25)
        try:
            encoded = json.dumps(payload, ensure_ascii=False).encode("utf-8") if payload is not None else None
            conn.request(method, resource, body=encoded,
                         headers={"Content-Type": "application/json"} if encoded is not None else {})
            response = conn.getresponse()
            # HTTPConnection does not follow HTTP redirects to outside networks.
            if response.status != 200:
                raise SemanticSearchError("Ollama local não retornou uma resposta válida.")
            body = response.read(max_bytes + 1)
            if len(body) > max_bytes:
                raise SemanticSearchError("Resposta local de embeddings excedeu o limite.")
            obj = json.loads(body.decode("utf-8"))
            if not isinstance(obj, dict):
                raise ValueError
            return obj
        except SemanticSearchError:
            raise
        except (OSError, TimeoutError, http.client.HTTPException,
                UnicodeError, ValueError, json.JSONDecodeError) as exc:
            raise SemanticSearchError("Serviço local de embeddings indisponível ou inválido.") from exc
        finally:
            conn.close()

    @staticmethod
    def _vector(item):
        if (not isinstance(item, list) or not 8 <= len(item) <= 2048
                or any(type(x) not in (float, int) or not math.isfinite(x)
                       for x in item)):
            raise SemanticSearchError("Vetor de embeddings local inválido.")
        norm = math.sqrt(sum(x * x for x in item))
        if not math.isfinite(norm) or norm <= 0:
            raise SemanticSearchError("Vetor de embeddings vazio.")
        return [x / norm for x in item]

    def rerank(self, question: str, hits: list, model: str, *, limit: int = 5):
        if (not isinstance(question, str) or not 1 <= len(question.strip()) <= 160
                or "\x00" in question):
            raise SemanticSearchError("Consulta semântica inválida.")
        if not isinstance(model, str) or not self.MODEL_NAME.fullmatch(model):
            raise SemanticSearchError("Nome de modelo de embeddings inválido.")
        if not isinstance(hits, list) or not 1 <= len(hits) <= self.MAX_CHUNKS:
            raise SemanticSearchError("Selecione entre 1 e 8 trechos locais.")
        if type(limit) is not int or not 1 <= limit <= 5:
            raise SemanticSearchError("Limite de resultados inválido.")
        texts = []
        for hit in hits:
            content = getattr(hit, "text", None)
            if not isinstance(content, str) or not content.strip() or len(content) > 1000:
                raise SemanticSearchError("Trecho inválido para busca semântica.")
            texts.append(content)
        vectors = self.embed([question.strip(), *texts], model)
        ranked = [
            SemanticMatch(hit, round(sum(a * b for a, b in zip(vectors[0], vector)), 5))
            for hit, vector in zip(hits, vectors[1:])
        ]
        return sorted(ranked, key=lambda m: m.score, reverse=True)[:limit]

    def embed(self, texts: list[str], model: str) -> list[list[float]]:
        """Embed at most 16 short local texts in one bounded request."""
        if (not isinstance(model, str) or not self.MODEL_NAME.fullmatch(model)
                or not isinstance(texts, list)
                or not 1 <= len(texts) <= self.MAX_EMBED_INPUTS
                or any(not isinstance(text, str) or not text.strip()
                       or len(text) > 1000 or "\x00" in text for text in texts)):
            raise SemanticSearchError("Modelo ou textos de embeddings inválidos.")
        models = self._request("GET", "/api/tags").get("models")
        if not isinstance(models, list):
            raise SemanticSearchError("Catálogo Ollama local inválido.")
        installed = [
            entry for entry in models
            if isinstance(entry, dict) and entry.get("name") == model
        ]
        if not installed:
            raise SemanticSearchError(
                "Modelo de embeddings não instalado; nenhuma instalação foi iniciada."
            )
        size = installed[0].get("size")
        if type(size) is not int or not 0 < size <= self.MAX_MODEL_SIZE:
            raise SemanticSearchError(
                "Modelo de embeddings grande demais ou sem tamanho verificado."
            )
        # Never start loading a model when the laptop is already under pressure.
        available = ResourceBudget.available_now_mib()
        required = max(1024, math.ceil(1.6 * size / (1024 * 1024)))
        if available is None or available < required:
            raise SemanticSearchError(
                "Memória livre insuficiente ou não verificável para embeddings locais."
            )
        embedded = self._request(
            "POST", "/api/embed",
            {"model": model, "input": [text.strip() for text in texts],
             "truncate": False, "keep_alive": 0},
            max_bytes=self.MAX_EMBED_REPLY,
        ).get("embeddings")
        if not isinstance(embedded, list) or len(embedded) != len(texts):
            raise SemanticSearchError("Quantidade de vetores local inválida.")
        vectors = [self._vector(x) for x in embedded]
        width = len(vectors[0])
        if any(len(v) != width for v in vectors):
            raise SemanticSearchError("Dimensões de embeddings incompatíveis.")
        return vectors
