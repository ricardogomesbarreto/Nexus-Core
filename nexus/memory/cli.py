"""Explicit local memory commands, without automatic chat transcript capture."""

import json
import sys

from nexus.config.settings import settings
from nexus.memory.store import MemoryEntry, MemoryStoreError, MemoryValidationError, PostgreSQLMemoryStore
from nexus.database.errors import DatabaseError


def _item(entry: MemoryEntry) -> dict:
    return {
        "id": entry.id,
        "content": entry.content,
        "created_at": entry.created_at.isoformat(),
        "expires_at": entry.expires_at.isoformat(),
    }


def execute_memory_command(args, store_factory=PostgreSQLMemoryStore) -> int:
    """Operate on memories only after an explicit --memory-* CLI action.

    Each command opens its own local PostgreSQL connection and closes it.
    No commands are forwarded to Ollama or privileged system tools.
    """
    if args.memory_clear and not args.memory_confirm:
        print("Para apagar todas as memórias, informe --memory-confirm.", file=sys.stderr)
        return 2

    store = None
    try:
        store = store_factory(settings)
        store.initialize()
        if args.memory_add is not None:
            result = {"saved": _item(store.add(args.memory_add, args.memory_days))}
        elif args.memory_list:
            result = {"memories": [_item(item) for item in store.list_entries()]}
        elif args.memory_search is not None:
            result = {"memories": [_item(item) for item in store.search(args.memory_search)]}
        elif args.memory_delete is not None:
            result = {"deleted": store.delete(args.memory_delete)}
        elif args.memory_clear:
            result = {"deleted_count": store.clear()}
        elif args.memory_status:
            result = {"status": store.stats()}
        else:
            raise ValueError("Ação de memória não reconhecida.")
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (MemoryValidationError, MemoryStoreError, DatabaseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if store is not None:
            store.close()
