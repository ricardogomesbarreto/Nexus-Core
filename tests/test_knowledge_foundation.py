"""Security, bounds, API and CLI regression for Knowledge Base."""
from argparse import Namespace
from datetime import datetime, timezone
from pathlib import Path

import psycopg
import pytest

from nexus.config.settings import Settings
from nexus.database.errors import DatabaseConfigurationError, DatabaseLifecycleError
from nexus.knowledge.cli import execute_knowledge_command
from nexus.knowledge.store import (
    KnowledgeDocument, KnowledgeHit, KnowledgeStoreError,
    KnowledgeValidationError, PostgreSQLKnowledgeBase,
)
from nexus.security.paths import PathSecurity


def settings():
    return Settings(database_password="dummy")


def make_store(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home.resolve()
    policy.protected_paths = [home / ".ssh", home / ".gnupg"]
    return PostgreSQLKnowledgeBase(settings(), path_security=policy), home


@pytest.mark.parametrize("query", ["", " ", None, "z" * 161, "a\x00b"])
def test_search_query_validation(query):
    store = PostgreSQLKnowledgeBase(settings())
    with pytest.raises(KnowledgeValidationError):
        store.search(query)


@pytest.mark.parametrize("limit", [-1, 0, 21, True, "5", 1.2])
def test_limits_enforced(limit):
    store = PostgreSQLKnowledgeBase(settings())
    with pytest.raises(KnowledgeValidationError):
        store.list_documents(limit)


@pytest.mark.parametrize("identifier", [0, -5, True, 3.2, "1"])
def test_deletion_rejects_invalid_document_ids(identifier):
    store = PostgreSQLKnowledgeBase(settings())
    with pytest.raises(KnowledgeValidationError):
        store.delete(identifier)


def test_requires_local_postgresql_and_credentials():
    with pytest.raises(DatabaseConfigurationError):
        PostgreSQLKnowledgeBase(Settings(database_provider="sqlite", database_password="x"))
    with pytest.raises(DatabaseConfigurationError):
        PostgreSQLKnowledgeBase(Settings(database_host="example.org", database_password="x"))
    with pytest.raises(DatabaseConfigurationError):
        PostgreSQLKnowledgeBase(Settings(database_password=None))


def test_connection_not_automatic_and_failure_is_sanitized(monkeypatch):
    def fail(**kwargs):
        raise psycopg.OperationalError("password should-never-be-leaked")
    monkeypatch.setattr("nexus.knowledge.store.psycopg.connect", fail)
    store = PostgreSQLKnowledgeBase(settings())
    with pytest.raises(KnowledgeStoreError) as error:
        store.initialize()
    assert "should-never" not in str(error.value)
    assert not store.initialized
    with pytest.raises(DatabaseLifecycleError):
        store.list_documents()
    store.close()


def test_import_authorized_utf8_and_chunk_bounds(tmp_path):
    store, home = make_store(tmp_path)
    document = home / "study.md"
    document.write_text("python\r\n" * 1000, encoding="utf-8")
    name, source, text = store._read_file(document)
    assert name == "study.md"
    assert source == str(document)
    assert "\r" not in text
    chunks = store._chunks(text)
    assert len(chunks) >= 2
    assert all(0 < len(c) <= 1000 for c in chunks)
    assert chunks[0][-100:] == chunks[1][:100]


@pytest.mark.parametrize("suffix,body", [
    (".pdf", "not really a pdf"), (".png", "not really an image"),
    (".md", ""), (".txt", "a\x00b"),
])
def test_rejects_unsupported_and_invalid_documents(tmp_path, suffix, body):
    store, home = make_store(tmp_path)
    document = home / ("file" + suffix)
    document.write_text(body, encoding="utf-8")
    with pytest.raises(KnowledgeValidationError):
        store._read_file(document)


def test_rejects_binary_and_oversized_documents(tmp_path):
    store, home = make_store(tmp_path)
    path = home / "binary.txt"
    path.write_bytes(b"\xff\xfe")
    with pytest.raises(KnowledgeValidationError):
        store._read_file(path)
    path.write_bytes(b"x" * (PostgreSQLKnowledgeBase.MAX_BYTES + 1))
    with pytest.raises(KnowledgeValidationError):
        store._read_file(path)


def test_rejects_symlinks_private_dir_and_outside_home(tmp_path):
    store, home = make_store(tmp_path)
    public = home / "notes.txt"
    public.write_text("allowed")
    link = home / "link.txt"
    link.symlink_to(public)
    with pytest.raises(KnowledgeValidationError):
        store._read_file(link)
    private = home / ".ssh"
    private.mkdir()
    (private / "keys.txt").write_text("do not import")
    with pytest.raises(KnowledgeValidationError):
        store._read_file(private / "keys.txt")
    outside = tmp_path / "outside.txt"
    outside.write_text("forbidden")
    with pytest.raises(KnowledgeValidationError):
        store._read_file(outside)


def test_descriptor_pin_resists_symlink_swap_after_approval(tmp_path):
    store, home = make_store(tmp_path)
    original = home / "source.txt"
    original.write_text("safe")
    outside = tmp_path / "secret.txt"
    outside.write_text("PRIVATE-SECRET")
    original_open = store._paths.open_regular_file

    def swap_then_open(path):
        original.unlink()
        original.symlink_to(outside)
        return original_open(path)

    store._paths.open_regular_file = swap_then_open
    with pytest.raises(KnowledgeValidationError):
        store._read_file(original)


def test_context_source_is_not_automatically_model_input():
    import nexus.desktop.conversation as chat
    import inspect
    source = inspect.getsource(chat.ChatSession.ask)
    assert "PostgreSQLKnowledgeBase" not in source
    assert "knowledge_context" not in source


def args(**updates):
    base = dict(knowledge_import=None, knowledge_list=False,
                knowledge_search=None, knowledge_delete=None,
                knowledge_context=None, knowledge_limit=5,
                knowledge_with_memory=False)
    base.update(updates)
    return Namespace(**base)


class FakeStore:
    instances = []

    def __init__(self, settings):
        self.calls = []
        self.closed = False
        self.instances.append(self)

    def initialize(self):
        self.calls.append("init")

    def close(self):
        self.closed = True

    def ingest(self, path):
        self.calls.append(("import", path))
        t = datetime(2026, 10, 9, tzinfo=timezone.utc)
        return KnowledgeDocument(9, "doc.txt", "/home/user/doc.txt", "a" * 64, 1, t, True)

    def list_documents(self, limit):
        self.calls.append(("list", limit))
        return []

    def search(self, text, limit, *, for_context=False):
        self.calls.append(("search", text, limit, for_context))
        return [KnowledgeHit(9, 11, "doc.txt", 0, "Python local")]

    def delete(self, identifier):
        self.calls.append(("delete", identifier))
        return True


class FakeMemory:
    instances = []

    def __init__(self, settings):
        self.events = []
        self.closed = False
        self.instances.append(self)

    def initialize(self):
        self.events.append("init")

    def close(self):
        self.closed = True

    def search(self, text, limit):
        self.events.append(("search", text, limit))
        return []


@pytest.mark.parametrize("params,expected", [
    ({"knowledge_import": "/home/a/doc.md"}, ("import", "/home/a/doc.md")),
    ({"knowledge_list": True}, ("list", 5)),
    ({"knowledge_search": "Python"}, ("search", "Python", 5, False)),
    ({"knowledge_delete": 8}, ("delete", 8)),
    ({"knowledge_context": "Python"}, ("search", "Python", 5, True)),
])
def test_cli_explicit_knowledge_actions(params, expected, capsys):
    FakeStore.instances.clear()
    assert execute_knowledge_command(args(**params), FakeStore, FakeMemory) == 0
    assert FakeStore.instances[-1].closed
    assert FakeStore.instances[-1].calls == ["init", expected]
    assert capsys.readouterr().out.strip()


def test_memory_lookup_requires_explicit_opt_in(capsys):
    FakeMemory.instances.clear()
    assert execute_knowledge_command(
        args(knowledge_context="Python"), FakeStore, FakeMemory
    ) == 0
    assert FakeMemory.instances == []
    assert execute_knowledge_command(
        args(knowledge_context="Python", knowledge_with_memory=True),
        FakeStore, FakeMemory
    ) == 0
    assert FakeMemory.instances[-1].events == ["init", ("search", "Python", 5)]
    assert FakeMemory.instances[-1].closed
    assert '"memories": []' in capsys.readouterr().out


def test_main_knowledge_does_not_launch_agent(monkeypatch):
    import nexus.main as main
    import nexus.knowledge.cli as cli
    actions = []
    monkeypatch.setattr(cli, "execute_knowledge_command",
                        lambda opts: actions.append(opts.knowledge_search) or 0)
    monkeypatch.setattr(main, "build_application",
                        lambda: pytest.fail("Do not initialize the agent for knowledge search"))
    main.cli(["--knowledge-search", "Python"])
    assert actions == ["Python"]


@pytest.mark.parametrize("params", [
    ["--knowledge-delete", "2", "--knowledge-import", "doc.txt"],
    ["--knowledge-with-memory", "--knowledge-list"],
    ["--knowledge-limit", "30", "--knowledge-list"],
    ["--knowledge-limit", "3"],
    ["--memory-list", "--knowledge-search", "x"],
])
def test_cli_rejects_unsafe_combinations(params):
    import nexus.main as main
    with pytest.raises(SystemExit) as result:
        main.cli(params)
    assert result.value.code == 2
