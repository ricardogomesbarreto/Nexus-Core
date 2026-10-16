"""Persistence: offline XDG preferences, text archive, symlinks and restarts."""

import json
import os
import stat
from dataclasses import replace

import pytest

from nexus.desktop.preferences import (
    DesktopPreferences, DesktopPreferenceStore, PreferenceStoreError,
    default_preferences_path,
)
from nexus.desktop.chat_archive import ChatArchive, ChatArchiveError
from nexus.desktop.conversation import ChatSession
from nexus.agent import AgentOutcome
from nexus.tools import ToolResult


def test_preferences_roundtrip_atomic_and_private(tmp_path):
    store = DesktopPreferenceStore(tmp_path / "nexus-core" / "preferences.json")
    assert store.load() == DesktopPreferences()
    options = DesktopPreferences(
        voice="Masculina", speech_enabled=False, wake_required=True,
        audio_backend="alsa", listening_enabled=False,
        geometry="1024x768", remember_history=False,
    )
    store.save(options)
    assert store.load() == options
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.path.parent.stat().st_mode) == 0o700
    assert json.loads(store.path.read_text())["version"] == 1
    assert "password" not in store.path.read_text().lower()
    assert not list(store.path.parent.glob(".preferences-*"))


@pytest.mark.parametrize("updates", [
    {"voice": "Inexistente"},
    {"voice": ""},
    {"speech_enabled": "true"},
    {"wake_required": 1},
    {"listening_enabled": None},
    {"audio_backend": "shell_command"},
    {"geometry": "30x4"},
    {"geometry": "980x720+30+10"},
    {"remember_history": "yes"},
])
def test_invalid_preferences_are_rejected_before_writing(tmp_path, updates):
    store = DesktopPreferenceStore(tmp_path / "options.json")
    with pytest.raises(PreferenceStoreError):
        store.save(replace(DesktopPreferences(), **updates))
    assert not store.path.exists()


def test_preferences_corruption_never_overwrites_user_file(tmp_path):
    store = DesktopPreferenceStore(tmp_path / "preferences.json")
    store.path.write_text("not-json", encoding="utf-8")
    with pytest.raises(PreferenceStoreError, match="Configurações inválidas"):
        store.load()
    assert store.path.read_text() == "not-json"


def test_preferences_reject_symlink_target_and_folder(tmp_path):
    other = tmp_path / "private-data"
    other.write_text("sensitive")
    store = DesktopPreferenceStore(tmp_path / "link.json")
    store.path.symlink_to(other)
    with pytest.raises(PreferenceStoreError):
        store.load()
    with pytest.raises(PreferenceStoreError):
        store.save(DesktopPreferences())
    assert other.read_text() == "sensitive"
    original_dir = tmp_path / "dir"
    original_dir.mkdir()
    linked_dir = tmp_path / "linked-dir"
    linked_dir.symlink_to(original_dir, target_is_directory=True)
    with pytest.raises(PreferenceStoreError):
        DesktopPreferenceStore(linked_dir / "config.json").save(DesktopPreferences())


def test_xdg_config_location_does_not_require_internet(monkeypatch, tmp_path):
    monkeypatch.setenv("XDG_CONFIG_HOME", str(tmp_path))
    assert default_preferences_path() == tmp_path / "nexus-core" / "preferences.json"


def test_archived_text_roundtrip_bounded_private_and_clear(tmp_path):
    store = ChatArchive(tmp_path / "nexus-core" / "chat-history.json")
    assert store.load() == []
    for index in range(220):
        store.append(f"pergunta {index}", f"resposta {index}")
    assert len(store.load()) == ChatArchive.MAX_RECORDS
    assert store.load()[0] == ("pergunta 20", "resposta 20")
    assert store.load()[-1] == ("pergunta 219", "resposta 219")
    assert stat.S_IMODE(store.path.stat().st_mode) == 0o600
    assert stat.S_IMODE(store.path.parent.stat().st_mode) == 0o700
    assert not list(store.path.parent.glob(".chat-*"))
    store.clear()
    assert store.load() == []


def test_history_file_rejects_symlink(tmp_path):
    target = tmp_path / "target"
    target.write_text("do not alter")
    store = ChatArchive(tmp_path / "chat-history.json")
    store.path.symlink_to(target)
    with pytest.raises(ChatArchiveError):
        store.append("oi", "olá")
    with pytest.raises(ChatArchiveError):
        store.clear()
    assert target.read_text() == "do not alter"


class TextAgent:
    def __init__(self):
        self.calls = []

    def run(self, prompt, **kwargs):
        self.calls.append(json.loads(prompt))
        return AgentOutcome(True, content="Explicação local do modelo.")


class ToolAgent:
    def run(self, prompt, **kwargs):
        return AgentOutcome(True, tool_result=ToolResult(
            True, "read_file", data={"content": "segredo-local"}
        ))


def test_chat_restarts_with_history_but_without_tool_outputs_or_vision_pixels(tmp_path):
    archive = ChatArchive(tmp_path / "history.json")
    agent = TextAgent()
    first = ChatSession(agent, archive=archive)
    assert first.ask("Explique redes locais").outcome.success
    first.note_visual("imagem", "informação da câmera")
    first.close()
    assert archive.load() == [
        ("Explique redes locais", "Explicação local do modelo.")
    ]
    second = ChatSession(TextAgent(), archive=archive)
    assert second.history == archive.load()
    assert "informação da câmera" not in str(archive.load())
    second.ask("Fale de roteadores")
    assert len(archive.load()) == 2
    tool = ChatSession(ToolAgent(), archive=archive)
    tool.ask("Leia esse arquivo")
    assert len(archive.load()) == 2
    assert "segredo-local" not in str(archive.load())


def test_archive_opt_out_does_not_delete_saved_conversations(tmp_path):
    archive = ChatArchive(tmp_path / "history.json")
    session = ChatSession(TextAgent(), archive=archive)
    session.ask("Primeira mensagem")
    session.set_archive(None)
    session.ask("Segunda mensagem")
    assert [x[0] for x in archive.load()] == ["Primeira mensagem"]
    session.set_archive(archive)
    session.ask("Terceira mensagem")
    assert [x[0] for x in archive.load()] == [
        "Primeira mensagem", "Terceira mensagem"
    ]
    archive.clear()
    session.forget_context()
    assert session.history == []
    assert archive.load() == []
