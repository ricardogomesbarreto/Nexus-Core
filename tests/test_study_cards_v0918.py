"""Study cards are source-linked, bounded and do not start a model."""

import os
from uuid import uuid4

import psycopg
import pytest

from nexus.config.settings import Settings
from nexus.knowledge.store import PostgreSQLKnowledgeBase
from nexus.security.paths import PathSecurity
from nexus.study.store import PostgreSQLStudyCards, StudyError


def test_validation_and_local_database_boundary():
    with pytest.raises(StudyError):
        PostgreSQLStudyCards._id(True)
    with pytest.raises(StudyError):
        PostgreSQLStudyCards._text("\x00", 10, "Resposta")
    with pytest.raises(StudyError):
        PostgreSQLStudyCards._text("x" * 241, 240, "Pergunta")
    assert PostgreSQLStudyCards._normal("  Python\n  3.12 ") == "python 3.12"
    with pytest.raises(StudyError):
        PostgreSQLStudyCards(Settings(database_password="test")).due(21)
    with pytest.raises(Exception):
        PostgreSQLStudyCards(Settings(database_host="elsewhere", database_password="test"))


@pytest.mark.skipif(not os.environ.get("NEXUS_TEST_POSTGRES_PASSWORD"),
                    reason="PostgreSQL local de teste indisponível")
def test_real_postgresql_cards_grade_and_source_cascade(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    path_policy = PathSecurity()
    path_policy.home = home.resolve()
    path_policy.protected_paths = []
    config = Settings(database_name="nexus_test", database_user="nexus_test",
                      database_password=os.environ["NEXUS_TEST_POSTGRES_PASSWORD"])
    library = PostgreSQLKnowledgeBase(config, path_policy)
    library.initialize()
    store = PostgreSQLStudyCards(config)
    token = uuid4().hex
    source = home / "aula.md"
    source.write_text(f"A resposta {token} está neste texto.\n", encoding="utf-8")
    document = library.ingest(source)
    try:
        hit = library.search(token)[0]
        store.initialize()
        with pytest.raises(StudyError, match="constar no trecho"):
            store.create(hit.chunk_id, f"Qual é {token}?", "resposta inventada")
        assert store.due() == [] or all(card.source_chunk_id != hit.chunk_id for card in store.due())
        card = store.create(hit.chunk_id, f"Qual é {token}?", f"resposta {token}")
        assert card.source_name == "aula.md"
        assert card.id in [item.id for item in store.due()]
        assert card.box == 1
        assert store.grade(card.id, True)
        assert not store.grade(card.id, True)  # No repeat before its next due date.
        with psycopg.connect(host="127.0.0.1", dbname="nexus_test",
                            user="nexus_test", password=config.database_password) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT box, review_count, due_at > CURRENT_TIMESTAMP "
                               "FROM nexus_study_cards WHERE id = %s", (card.id,))
                assert cursor.fetchone() == (2, 1, True)
        assert library.delete(document.id)
        with psycopg.connect(host="127.0.0.1", dbname="nexus_test",
                            user="nexus_test", password=config.database_password) as conn:
            with conn.cursor() as cursor:
                cursor.execute("SELECT COUNT(*) FROM nexus_study_cards WHERE id = %s", (card.id,))
                assert cursor.fetchone()[0] == 0
        assert store.due() == [] or all(item.id != card.id for item in store.due())
    finally:
        library.delete(document.id)
        store.close()
        library.close()


def test_explicit_voice_preview_stops_listening_and_uses_current_voice(monkeypatch):
    from nexus.desktop.window import DesktopWindow
    ui = DesktopWindow.__new__(DesktopWindow)
    ui._closing = ui._busy = False
    ui._permission_dialog = None
    ui._listening = True
    ui._speaking = False
    ui._listen_generation = 4
    events = []
    ui.speech_enabled = type("Switch", (), {"get": lambda self: True})()
    ui.voice_choice = type("Choice", (), {"get": lambda self: "Feminina"})()
    ui.recognizer = type("Recognizer", (), {"stop": lambda self: events.append("stop")})()
    ui.status = type("Status", (), {"configure": lambda self, **kw: events.append(kw)})()
    monkeypatch.setattr(ui, "_say_response", lambda text: events.append(text) or True)
    ui._preview_selected_voice()
    assert ui._listen_generation == 5
    assert events[0] == "stop"
    assert "voz feminina" in events[-1]


def test_voice_preview_respects_mute_without_opening_microphone(monkeypatch):
    from nexus.desktop.window import DesktopWindow
    ui = DesktopWindow.__new__(DesktopWindow)
    ui._closing = ui._busy = False
    ui._permission_dialog = None
    ui.speech_enabled = type("Switch", (), {"get": lambda self: False})()
    events = []
    ui.status = type("Status", (), {"configure": lambda self, **kw: events.append(kw)})()
    monkeypatch.setattr(ui, "_say_response", lambda _: pytest.fail("voz muda"))
    ui._preview_selected_voice()
    assert "Ative Responder em voz" in events[0]["text"]
