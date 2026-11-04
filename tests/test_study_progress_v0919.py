"""Results are saved only after opt-in; tied to a source and bounded."""
import os
from uuid import uuid4

import pytest

from nexus.config.settings import Settings
from nexus.knowledge.store import PostgreSQLKnowledgeBase
from nexus.security.paths import PathSecurity
from nexus.study.store import PostgreSQLStudyCards, StudyError


def test_progress_rejects_invalid_scores_without_database():
    store = PostgreSQLStudyCards(Settings(database_password="test"))
    for chunk, good, total in ((1, True, 1), (1, 2, 1), (1, -1, 1),
                               (1, 0, 0), (1, 0, 11), (0, 0, 1)):
        with pytest.raises(StudyError):
            store.record_session(chunk, good, total)
    with pytest.raises(StudyError):
        store.recent_sessions(21)


@pytest.mark.skipif(not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
                    reason="PostgreSQL de teste indisponível")
def test_progress_postgresql_cascade(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home.resolve()
    policy.protected_paths = []
    config = Settings(database_name="nexus_test", database_user="nexus_test",
                      database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"])
    library = PostgreSQLKnowledgeBase(config, policy)
    library.initialize()
    store = PostgreSQLStudyCards(config)
    token = uuid4().hex
    source = home / "materia.md"
    source.write_text(f"Esta aula explica o conceito {token}.", encoding="utf-8")
    doc = library.ingest(source)
    try:
        chunk = library.search(token)[0].chunk_id
        store.initialize()
        result_id = store.record_session(chunk, 2, 3)
        assert result_id > 0
        assert store.recent_sessions()[0] == (chunk, 2, 3)
        library.delete(doc.id)
        assert all(x[0] != chunk for x in store.recent_sessions())
        with pytest.raises(StudyError):
            store.record_session(chunk, 0, 1)
    finally:
        library.delete(doc.id)
        store.close()
        library.close()
