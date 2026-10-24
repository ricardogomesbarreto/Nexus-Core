"""Comandos explícitos para anotações; conteúdo nunca entra nos logs."""
import json
import sys

from nexus.config.settings import settings
from nexus.database.errors import DatabaseError
from nexus.notes.store import NoteError, PostgreSQLNotes


def _data(note, *, body=False):
    value = {"id": note.id, "title": note.title,
             "updated_at": note.updated_at.isoformat()}
    if body:
        value["body"] = note.body
    return value


def execute_notes(args, store_factory=PostgreSQLNotes, input_stream=None) -> int:
    stream = input_stream if input_stream is not None else sys.stdin
    store = None
    try:
        store = store_factory(settings)
        store.initialize()
        if args.note_create is not None or args.note_update is not None:
            body = stream.read(PostgreSQLNotes.MAX_BODY + 1)
            title = args.note_create if args.note_create is not None else args.note_title
            note = (store.create(title, body) if args.note_create is not None
                    else store.update(args.note_update, title, body))
            result = {"note": _data(note) if note else None}
        elif args.note_get is not None:
            note = store.get(args.note_get)
            result = {"note": _data(note, body=True) if note else None}
        elif args.note_list:
            result = {"notes": [_data(n) for n in store.list(args.note_limit)]}
        elif args.note_search is not None:
            result = {"notes": [_data(n) for n in store.search(args.note_search, args.note_limit)]}
        else:
            result = {"deleted": store.delete(args.note_delete)}
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (NoteError, DatabaseError) as exc:
        print(str(exc), file=sys.stderr)
        return 1
    finally:
        if store is not None:
            store.close()
