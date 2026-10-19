"""Offline workspace features must remain permission-scoped and never start services."""
import json
import os
from pathlib import Path
from types import SimpleNamespace

import pytest

from nexus.agent.planner import _simple_creative_request
from nexus.desktop.conversation import ChatSession
from nexus.agent import AgentOutcome
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import LocalDataTool, LocalNoteTool, ToolExecutor, ToolRegistry, ToolResult
from nexus.tools.offline_workspace import _transform, offline_capabilities
from nexus.voice.local import LocalRecognizer


class Approval:
    def __init__(self, approve):
        self.approve = approve
        self.called = 0

    def confirm(self, request):
        self.called += 1
        return self.approve


def setup(tmp_path, approve=True):
    home = tmp_path / "home"
    home.mkdir()
    p = PathSecurity()
    p.home = home
    p.protected_paths = [home / ".ssh"]
    reg = ToolRegistry()
    reg.register(LocalDataTool())
    reg.register(LocalNoteTool())
    approval = Approval(approve)
    exec_ = ToolExecutor(reg, SecurityGate(
        path_security=p, audit_logger=AuditLogger(tmp_path / "audit.log")), approval)
    return exec_, home, approval


def test_private_note_requires_confirmation_and_never_overwrites(tmp_path):
    executor, home, approval = setup(tmp_path, approve=False)
    path = home / "anotacoes.md"
    denied = executor.execute("local_note_create", output=str(path), content="# Título\nCorpo")
    assert not denied.success and not path.exists() and approval.called == 1
    approval.approve = True
    ok = executor.execute("local_note_create", output=str(path), content="# Título\nCorpo")
    assert ok.success and ok.data["bytes"] == len("# Título\nCorpo".encode())
    assert path.read_text() == "# Título\nCorpo"
    assert path.stat().st_mode & 0o777 == 0o600
    assert not executor.execute("local_note_create", output=str(path), content="OUTRO").success
    assert path.read_text() == "# Título\nCorpo"


@pytest.mark.parametrize("invalid_path", [
    ".ssh/chave.md", "ligacao.md", "fora.txt", "ausente/teste.md",
])
def test_note_rejects_invalid_or_protected_destination(tmp_path, invalid_path):
    executor, home, _ = setup(tmp_path)
    (home / ".ssh").mkdir()
    if invalid_path == "ligacao.md":
        (home / "ligacao.md").symlink_to(tmp_path / "fora.md")
    result = executor.execute(
        "local_note_create", output=str(home / invalid_path), content="nota")
    assert not result.success


def test_note_limits_are_hard(tmp_path):
    executor, home, approval = setup(tmp_path)
    bad = executor.execute("local_note_create", output=str(home / "too.md"),
                           content="a" * (64 * 1024 + 1))
    assert not bad.success
    assert not (home / "too.md").exists()


@pytest.mark.parametrize("op,payload,expected", [
    ("sha256", "abc", "ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad"),
    ("base64_encode", "ação", "YcOnw6Nv"),
    ("base64_decode", "YQ==", "a"),
    ("hex_encode", "abc", "616263"),
    ("hex_decode", "616263", "abc"),
    ("url_encode", "á b", "%C3%A1%20b"),
    ("url_decode", "%C3%A1%20b", "á b"),
    ("rot13", "aBc", "nOp"),
])
def test_local_data_transforms_are_bounded_and_deterministic(op, payload, expected):
    assert _transform(op, payload) == expected


@pytest.mark.parametrize("operation,value", [
    ("sha1", "abc"), ("base64_decode", "!!!"),
    ("hex_decode", "abc"), ("url_decode", "%QZ"),
    ("sha256", "z" * 8193), ("sha256", "x\x00z"),
])
def test_data_transform_fails_closed(operation, value):
    assert not LocalDataTool().execute(operation, value).success


def test_data_transform_does_not_use_model_or_files(tmp_path):
    executor, home, approval = setup(tmp_path, approve=True)
    result = executor.execute("local_data_transform", operation="sha256", value="abc")
    assert result.success
    assert result.data["result"].startswith("ba7816bf")
    assert approval.called == 0
    assert list(home.iterdir()) == []


@pytest.mark.parametrize("utterance,name", [
    ('Crie uma nota com o texto "Olá" em /home/usuario/Notas/hoje.md', "local_note_create"),
    ('Calcule SHA-256 do texto "abc"', "local_data_transform"),
    ('Codifique em base64 o texto "abc"', "local_data_transform"),
    ('Decodifique base64 "YQ=="', "local_data_transform"),
    ('Codifique em hexadecimal o texto "abc"', "local_data_transform"),
])
def test_explicit_current_turn_parser_only(utterance, name):
    action = _simple_creative_request(json.dumps(
        {"mensagem_atual": utterance, "historico": []}))
    assert action is not None and action[0] == name


def test_history_cannot_trigger_notes_or_local_transforms():
    value = json.dumps({
        "mensagem_atual": "O que é uma nota Markdown?",
        "historico": [{"usuario": 'Crie uma nota com o texto "secreto" em /home/u/a.md'}],
    })
    assert _simple_creative_request(value) is None


def test_capabilities_is_passive_with_no_docker_or_network():
    calls = []
    def which(name):
        calls.append(name)
        return "/usr/bin/" + name if name == "kolibri" else None
    report = offline_capabilities(which=which)
    assert set(calls) == {"kiwix-serve", "kolibri", "pmtiles", "docker"}
    assert any(x["capability"] == "cursos_offline" and
               x["status"] == "opcional_detectado_nao_iniciado" for x in report)
    assert any(x["capability"] == "busca_semantica_vetorial" and
               x["status"] == "planejada_nao_integrada" for x in report)


def test_voice_pcm_alignment_can_cross_odd_pipe_reads():
    data, tail = LocalRecognizer._aligned_pcm(b"", b"\x00")
    assert data == b"" and tail == b"\x00"
    data, tail = LocalRecognizer._aligned_pcm(tail, b"\x01\x02")
    assert data == b"\x00\x01" and tail == b"\x02"
    data, tail = LocalRecognizer._aligned_pcm(tail, b"\x03")
    assert data == b"\x02\x03" and tail == b""


def test_native_chat_reports_private_note_without_displaying_its_body():
    outcome = AgentOutcome(
        True, tool_result=ToolResult(
            True, "local_note_create", data={"path": "/home/u/n.md", "bytes": 50}))
    message = ChatSession._describe(outcome)
    assert message == "Nota local criada: /home/u/n.md"
    assert "content" not in message
