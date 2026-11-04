"""Explicit, offline Knowledge Base commands and opt-in memory context."""
import json
import sys

from nexus.config.settings import settings
from nexus.database.errors import DatabaseError
from nexus.knowledge.store import KnowledgeStoreError, KnowledgeValidationError, PostgreSQLKnowledgeBase
from nexus.knowledge.answer import KnowledgeAnswerError
from nexus.knowledge.semantic_local import LocalSemanticReranker, SemanticSearchError
from nexus.memory.store import MemoryStoreError, MemoryValidationError, PostgreSQLMemoryStore


def execute_knowledge_command(args, store_factory=PostgreSQLKnowledgeBase,
                              memory_factory=PostgreSQLMemoryStore) -> int:
    store = None
    memory = None
    try:
        store = store_factory(settings)
        store.initialize()
        if args.knowledge_import is not None:
            entry = store.ingest(args.knowledge_import)
            result = {"document": _document(entry)}
        elif args.knowledge_list:
            result = {"documents": [_document(d) for d in
                                    store.list_documents(args.knowledge_limit)]}
        elif args.knowledge_search is not None:
            result = {"hits": [_hit(h) for h in
                               store.search(args.knowledge_search, args.knowledge_limit)]}
        elif args.knowledge_delete is not None:
            result = {"deleted": store.delete(args.knowledge_delete)}
        elif args.knowledge_context is not None:
            query = args.knowledge_context
            hits = store.search(query, args.knowledge_limit, for_context=True)
            result = {"query": query, "documents": [_hit(h) for h in hits], "memories": []}
            if args.knowledge_with_memory:
                # Memory access is explicit; do not inject this result into Ollama.
                memory = memory_factory(settings)
                memory.initialize()
                result["memories"] = [
                    {"id": m.id, "content": m.content, "expires_at": m.expires_at.isoformat()}
                    for m in memory.search(query, limit=args.knowledge_limit)
                ]
        elif args.knowledge_answer is not None:
            from nexus.knowledge.answer import answer_from_hits
            from nexus.models.model_factory import build_model_router
            hits = store.search(args.knowledge_answer, min(args.knowledge_limit, 3),
                                for_context=True)
            # A miss is answered locally without activating Ollama.
            result = answer_from_hits(args.knowledge_answer, hits,
                                      build_model_router(settings) if hits else None)
        elif getattr(args, "knowledge_index", None) is not None:
            hits = store.indexable_chunks(args.knowledge_index)
            if not hits:
                raise KnowledgeValidationError("Documento sem trechos para indexar.")
            model = args.embedding_model
            vectors = LocalSemanticReranker().embed([hit.text for hit in hits], model)
            count = store.save_embeddings(args.knowledge_index, model,
                                          [(hit.chunk_id, vector)
                                           for hit, vector in zip(hits, vectors)])
            result = {"indexed": count, "document_id": args.knowledge_index,
                      "model": model}
        elif getattr(args, "knowledge_semantic_search", None) is not None:
            query = store._valid_query(args.knowledge_semantic_search)
            model = args.embedding_model
            if not store.indexed_count(model):
                raise KnowledgeValidationError("Nenhum trecho indexado com este modelo.")
            vector = LocalSemanticReranker().embed([query], model)[0]
            matches = store.search_embeddings(vector, model, min(args.knowledge_limit, 5))
            result = {"hits": [{**_hit(match.hit), "score": match.score}
                               for match in matches], "model": model}
        elif getattr(args, "knowledge_semantic_answer", None) is not None:
            from nexus.knowledge.semantic_local import answer_from_index
            from nexus.models.model_factory import build_model_router
            result = answer_from_index(
                args.knowledge_semantic_answer, args.embedding_model, store,
                lambda: build_model_router(settings))
        elif getattr(args, "knowledge_index_delete", None) is not None:
            result = {"removed": store.clear_embeddings(args.knowledge_index_delete)}
        else:
            raise KnowledgeValidationError("Ação de conhecimento não reconhecida.")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (KnowledgeAnswerError, SemanticSearchError, KnowledgeStoreError, KnowledgeValidationError, MemoryStoreError,
            MemoryValidationError, DatabaseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if memory is not None:
            memory.close()
        if store is not None:
            store.close()


def _document(entry):
    return {"id": entry.id, "name": entry.name, "source_path": entry.source_path,
            "sha256": entry.sha256, "chunks": entry.chunk_count,
            "created_at": entry.created_at.isoformat(), "added": entry.added}


def _hit(hit):
    return {"document_id": hit.document_id, "chunk_id": hit.chunk_id,
            "name": hit.name, "ordinal": hit.ordinal, "excerpt": hit.text}
