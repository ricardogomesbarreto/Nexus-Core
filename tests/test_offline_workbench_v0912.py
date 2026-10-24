"""Contratos de dados locais e persistência explícita de anotações."""
import json
import subprocess
import sys
from datetime import datetime, timezone
from io import StringIO
from types import SimpleNamespace

import pytest

from nexus.config.settings import Settings
from nexus.notes.cli import execute_notes
from nexus.notes.store import NoteError, PostgreSQLNotes
from nexus.tools.data_local import MAX_BYTES, transform_text
from nexus.platforms.benchmark import benchmark_cpu
from nexus.updates.launcher import should_run_maintenance


def test_text_tools_are_local_bounded_and_reject_invalid_utf8():
    assert transform_text("sha256", b"abc") == (
        "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"
    )
    assert transform_text("base64-decode", b"T2zDoQ==") == "Olá"
    assert transform_text("hex-decode", "4f6cc3a1".encode()) == "Olá"
    assert transform_text("url-decode", b"Ol%C3%A1") == "Olá"
    with pytest.raises(ValueError):
        transform_text("hex-decode", b"nope")
    with pytest.raises(ValueError):
        transform_text("url-decode", b"%FF")
    with pytest.raises(ValueError, match="64 KiB"):
        transform_text("base64-encode", b"a" * MAX_BYTES)
    with pytest.raises(ValueError, match="64 KiB"):
        transform_text("sha256", b"a" * (MAX_BYTES + 1))


def test_data_cli_uses_stdin_without_booting_postgresql_or_ollama():
    proc = subprocess.run(
        [sys.executable, "-m", "nexus.main", "--data-tool", "sha256"],
        input=b"abc", capture_output=True, timeout=10,
    )
    assert proc.returncode == 0
    assert proc.stdout.decode().strip() == transform_text("sha256", b"abc")
    assert b"Inicializando" not in proc.stderr


def test_cpu_benchmark_is_explicit_bounded_and_local():
    with pytest.raises(ValueError):
        benchmark_cpu(10000)
    result = benchmark_cpu(200)
    assert result["cpu_hash_mib_per_s"] > 0
    assert result["external_network_used"] is False
    assert result["leaderboard_uploaded"] is False
    assert result["elapsed_ms"] >= 180
    assert not should_run_maintenance(["--benchmark"])
    assert not should_run_maintenance(["--note-list"])
    assert not should_run_maintenance(["--data-tool", "sha256"])


def test_notes_require_local_postgresql_and_limit_input():
    with pytest.raises(Exception, match="PostgreSQL local"):
        PostgreSQLNotes(Settings(database_host="remote.example"))
    with pytest.raises(NoteError):
        PostgreSQLNotes._text("x" * 121, 120, "Título")
    with pytest.raises(NoteError):
        PostgreSQLNotes._text("texto\x00", 16000, "Texto")
    with pytest.raises(NoteError):
        PostgreSQLNotes._limit(51)
    with pytest.raises(NoteError):
        PostgreSQLNotes._id(True)


def test_notes_parameterized_transactions_and_rollback(monkeypatch):
    from nexus.notes import store as module
    sql_calls = []
    row = (8, "Título", "Corpo", datetime.now(timezone.utc))
    class Cursor:
        rowcount = 1
        def __enter__(self): return self
        def __exit__(self, *args): pass
        def execute(self, sql, params=None):
            sql_calls.append((sql, params))
        def fetchone(self): return row
        def fetchall(self): return [row]
    class Connection:
        commits = 0
        rollbacks = 0
        def cursor(self): return Cursor()
        def commit(self): self.commits += 1
        def rollback(self): self.rollbacks += 1
        def close(self): pass
    connection = Connection()
    monkeypatch.setattr(module.psycopg, "connect", lambda **kwargs: connection)
    notes = PostgreSQLNotes(Settings(database_password="test"))
    notes.initialize()
    injected = "'; DROP TABLE nexus_notes; --"
    assert notes.create(injected, "segredo").id == 8
    assert sql_calls[-1][1] == (injected, "segredo")
    assert notes.search(injected)[0].body == "Corpo"
    assert sql_calls[-1][1] == (injected, 20)
    assert notes.update(8, "Novo", "Texto").title == "Título"
    assert notes.delete(8)
    with pytest.raises(NoteError):
        notes.create("", "texto")
    assert connection.rollbacks == 0  # rejected before opening a transaction
    assert connection.commits >= 5
    notes.close()


def test_note_cli_reads_bounded_stdin_and_omits_body_from_create_output(capsys):
    class FakeStore:
        def __init__(self, settings): self.closed = False
        def initialize(self): pass
        def create(self, title, body):
            assert body == "conteúdo privado"
            return SimpleNamespace(id=1, title=title, body=body,
                                   updated_at=datetime.now(timezone.utc))
        def close(self): self.closed = True
    args = SimpleNamespace(note_create="Minha nota", note_update=None, note_title=None)
    assert execute_notes(args, store_factory=FakeStore,
                         input_stream=StringIO("conteúdo privado")) == 0
    printed = json.loads(capsys.readouterr().out)
    assert printed["note"]["title"] == "Minha nota"
    assert "body" not in printed["note"]
