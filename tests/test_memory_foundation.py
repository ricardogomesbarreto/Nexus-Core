"""Contract, privacy and CLI tests for explicit PostgreSQL memory."""

from argparse import Namespace
from datetime import datetime, timezone

import psycopg
import pytest

from nexus.config.settings import Settings
from nexus.database.errors import DatabaseConfigurationError, DatabaseLifecycleError
from nexus.memory.cli import execute_memory_command
from nexus.memory.store import MemoryEntry, MemoryStoreError, MemoryValidationError, PostgreSQLMemoryStore


def settings():
    return Settings(database_password="dummy")


@pytest.mark.parametrize("text", ["", "  ", None, "x" * 1201, "bad\x00text"])
def test_memory_rejects_invalid_content_before_db_access(text):
    store = PostgreSQLMemoryStore(settings())
    with pytest.raises(MemoryValidationError):
        store.add(text)


@pytest.mark.parametrize("days", [0, -3, 366, True, 1.5, "90"])
def test_memory_retention_is_bounded_and_integer_only(days):
    store = PostgreSQLMemoryStore(settings())
    with pytest.raises(MemoryValidationError):
        store.add("gosto de estudar", days)


@pytest.mark.parametrize("value", [-1, 0, True, 1.25, "1"])
def test_memory_delete_requires_valid_id(value):
    store = PostgreSQLMemoryStore(settings())
    with pytest.raises(MemoryValidationError):
        store.delete(value)


@pytest.mark.parametrize("limit", [0, -1, 101, True, "10"])
def test_memory_list_limit_rejects_unsafe_values(limit):
    store = PostgreSQLMemoryStore(settings())
    with pytest.raises(MemoryValidationError):
        store.list_entries(limit)


def test_memory_is_not_initialized_implicitly():
    store = PostgreSQLMemoryStore(settings())
    with pytest.raises(DatabaseLifecycleError):
        store.list_entries()
    with pytest.raises(DatabaseLifecycleError):
        store.purge_expired()
    store.close()


def test_memory_enforces_postgres_loopback_and_password():
    with pytest.raises(DatabaseConfigurationError):
        PostgreSQLMemoryStore(Settings(database_password=None))
    with pytest.raises(DatabaseConfigurationError):
        PostgreSQLMemoryStore(Settings(database_password="x", database_host="example.com"))
    with pytest.raises(DatabaseConfigurationError):
        PostgreSQLMemoryStore(Settings(database_password="x", database_provider="unsupported"))


def test_memory_connection_errors_hide_raw_driver_details(monkeypatch):
    def fail(**kwargs):
        raise psycopg.OperationalError("secret credential leaked from driver")
    monkeypatch.setattr("nexus.memory.store.psycopg.connect", fail)
    store = PostgreSQLMemoryStore(settings())
    with pytest.raises(MemoryStoreError) as error:
        store.initialize()
    assert "secret" not in str(error.value)
    assert not store.initialized


def args(**overrides):
    base = dict(memory_add=None, memory_add_stdin=False, memory_list=False, memory_search=None,
                memory_delete=None, memory_clear=False, memory_status=False,
                memory_days=90, memory_confirm=False)
    base.update(overrides)
    return Namespace(**base)


class FakeStore:
    created = []

    def __init__(self, settings):
        self.calls = []
        self.closed = False
        self.created.append(self)

    def initialize(self):
        self.calls.append("initialize")

    def close(self):
        self.closed = True

    def add(self, content, days):
        self.calls.append(("add", content, days))
        now = datetime(2026, 10, 9, tzinfo=timezone.utc)
        return MemoryEntry(7, content, now, now)

    def list_entries(self):
        self.calls.append("list")
        return []

    def search(self, term):
        self.calls.append(("search", term))
        return []

    def delete(self, identifier):
        self.calls.append(("delete", identifier))
        return True

    def clear(self):
        self.calls.append("clear")
        return 2

    def stats(self):
        self.calls.append("stats")
        return {"active": 1, "audit_events": 3}


def test_cli_add_only_saves_explicit_input(capsys):
    FakeStore.created.clear()
    result = execute_memory_command(args(memory_add="alguma preferência", memory_days=30), FakeStore)
    assert result == 0
    assert FakeStore.created[-1].calls == ["initialize", ("add", "alguma preferência", 30)]
    assert FakeStore.created[-1].closed
    assert '"id": 7' in capsys.readouterr().out


def test_cli_stdin_saves_without_command_argument(monkeypatch):
    import io
    import sys
    FakeStore.created.clear()
    monkeypatch.setattr(sys, "stdin", io.StringIO("dado privado digitado\\n"))
    assert execute_memory_command(args(memory_add_stdin=True), FakeStore) == 0
    assert FakeStore.created[-1].calls[1] == ("add", "dado privado digitado\\n", 90)


def test_cli_clear_requires_explicit_confirmation(capsys):
    FakeStore.created.clear()
    assert execute_memory_command(args(memory_clear=True), FakeStore) == 2
    assert FakeStore.created == []
    assert "--memory-confirm" in capsys.readouterr().err
    assert execute_memory_command(args(memory_clear=True, memory_confirm=True), FakeStore) == 0
    assert FakeStore.created[-1].calls == ["initialize", "clear"]


@pytest.mark.parametrize("kwargs,expected", [
    ({"memory_list": True}, "list"),
    ({"memory_search": "azul"}, ("search", "azul")),
    ({"memory_delete": 8}, ("delete", 8)),
    ({"memory_status": True}, "stats"),
])
def test_cli_supports_explicit_memory_actions(kwargs, expected):
    FakeStore.created.clear()
    assert execute_memory_command(args(**kwargs), FakeStore) == 0
    assert FakeStore.created[-1].calls == ["initialize", expected]


def test_entrypoint_memory_mode_does_not_boot_agent(monkeypatch):
    import nexus.main as main
    import nexus.memory.cli as memory_cli
    calls = []
    monkeypatch.setattr(memory_cli, "execute_memory_command", lambda a: calls.append(a.memory_search) or 0)
    monkeypatch.setattr(main, "build_application", lambda: pytest.fail("No agent or app startup"))
    main.cli(["--memory-search", "projeto"])
    assert calls == ["projeto"]


def test_entrypoint_rejects_unsafe_memory_flag_combinations(capsys):
    import nexus.main as main
    with pytest.raises(SystemExit) as exc:
        main.cli(["--memory-add", "text", "--agent-prompt", "hello"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        main.cli(["--memory-clear", "--memory-days", "365"])
    assert exc.value.code == 2
    with pytest.raises(SystemExit) as exc:
        main.cli(["--memory-confirm", "--memory-list"])
    assert exc.value.code == 2
