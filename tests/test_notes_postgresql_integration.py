"""CRUD e busca real no PostgreSQL da CI, sem servidor extra."""
import os
from uuid import uuid4

import pytest

from nexus.config.settings import Settings
from nexus.notes.store import PostgreSQLNotes


@pytest.mark.skipif(not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
                    reason="PostgreSQL de teste indisponível")
def test_explicit_notes_crud_search_and_delete_on_postgresql():
    store = PostgreSQLNotes(Settings(
        database_name="nexus_test", database_user="nexus_test",
        database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"],
    ))
    store.initialize()
    identifier = f"Nexus-{uuid4().hex}"
    created_id = None
    try:
        created = store.create(identifier, "Texto **local** com detalhe original")
        created_id = created.id
        assert store.get(created.id).body.startswith("Texto **local**")
        assert any(item.id == created.id for item in store.search(identifier))
        edited = store.update(created.id, identifier, "Texto revisado")
        assert edited.body == "Texto revisado"
        assert any(item.id == created.id for item in store.list(50))
        assert store.delete(created.id) is True
        created_id = None
        assert store.get(created.id) is None
    finally:
        if created_id is not None:
            store.delete(created_id)
        store.close()
