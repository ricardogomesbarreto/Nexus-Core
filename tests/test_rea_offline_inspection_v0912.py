"""REA-style offline triage, without executing any analyzed artifact."""
import hashlib
import io
import json
import os
from pathlib import Path
import struct
import zipfile

import pytest

from nexus.agent import AgentPlanner
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import InspectArtifactTool, ToolExecutor, ToolRegistry


class Confirmation:
    def __init__(self, approved):
        self.approved = approved
        self.calls = []

    def confirm(self, request):
        self.calls.append(request)
        return self.approved


def setup(tmp_path, approved=True):
    home = tmp_path / "user"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh", home / ".config"]
    registry = ToolRegistry()
    registry.register(InspectArtifactTool())
    confirm = Confirmation(approved)
    executor = ToolExecutor(
        registry, SecurityGate(
            path_security=policy,
            audit_logger=AuditLogger(tmp_path / "audit.log"),
        ), confirm,
    )
    return home, confirm, executor


def test_elf_scan_is_offline_read_only_and_needs_individual_consent(tmp_path, monkeypatch):
    home, confirmation, executor = setup(tmp_path, approved=False)
    target = home / "programa.elf"
    header = bytearray(80)
    header[:4] = bytes.fromhex("7f454c46")
    header[4:6] = bytes((2, 1))
    struct.pack_into("<H", header, 18, 62)
    target.write_bytes(header)
    before = target.read_bytes()

    def no_subprocess(*args, **kwargs):
        pytest.fail("Analisador nunca executa o arquivo")

    monkeypatch.setattr("subprocess.run", no_subprocess)
    monkeypatch.setattr("subprocess.Popen", no_subprocess)
    denied = executor.execute("inspect_artifact_local", source=str(target))
    assert not denied.success
    assert len(confirmation.calls) == 1
    assert target.read_bytes() == before

    confirmation.approved = True
    accepted = executor.execute("inspect_artifact_local", source=str(target))
    assert accepted.success
    assert accepted.data["kind"] == "ELF"
    assert accepted.data["size_bytes"] == 80
    assert accepted.data["sha256"] == hashlib.sha256(before).hexdigest()
    assert "64 bits" in accepted.data["summary"]
    assert target.read_bytes() == before
    assert len(confirmation.calls) == 2


def test_archives_are_classified_without_extracting_private_payloads(tmp_path, monkeypatch):
    home, _, executor = setup(tmp_path)
    apk = home / "app.apk"
    with zipfile.ZipFile(apk, "w") as stream:
        stream.writestr("AndroidManifest.xml", b"sensitive-android-xml")
        stream.writestr("classes.dex", b"private-dex-bytes")
    def no_extract(*args, **kwargs):
        pytest.fail("ZIP extraction forbidden")
    monkeypatch.setattr(zipfile.ZipFile, "extract", no_extract)
    monkeypatch.setattr(zipfile.ZipFile, "extractall", no_extract)
    result = executor.execute("inspect_artifact_local", source=str(apk))
    assert result.success
    assert result.data["kind"] == "APK"
    assert "arquivos DEX=1" in result.data["summary"]
    assert "private" not in json.dumps(result.data)
    assert zipfile.ZipFile(apk).namelist() == [
        "AndroidManifest.xml", "classes.dex",
    ]


def test_javascript_is_triaged_without_node_or_network(tmp_path, monkeypatch):
    home, _, executor = setup(tmp_path)
    source = home / "app.js"
    source.write_text("import library from 'library';\nexport const x = 1;\n")
    import socket
    monkeypatch.setattr(socket, "create_connection",
                        lambda *a, **kw: pytest.fail("Network prohibited"))
    result = executor.execute("inspect_artifact_local", source=str(source))
    assert result.success
    assert result.data["kind"] == "CODIGO_TEXTO"
    assert "aproximadas" in result.data["summary"]
    assert "library" not in result.data["summary"]


@pytest.mark.parametrize("name,data,kind", [
    ("bundle.wasm", b"\\x00asm\\x01\\x00\\x00\\x00", "WASM"),
    ("pdf.pdf", b"%PDF-1.7\n", "PDF"),
    ("banner.png", bytes.fromhex("89504e470d0a1a0a"), "PNG"),
    ("binary.exe", b"MZ" + b"\\x00" * 100, "MZ"),
])
def test_static_formats_identified_without_opening_app(tmp_path, name, data, kind):
    home, _, executor = setup(tmp_path)
    # UTF-8 test fixtures only; fixtures are never executed.
    path = home / name
    path.write_bytes(data)
    out = executor.execute("inspect_artifact_local", source=str(path))
    assert out.success
    assert out.data["kind"] == kind


def test_symlink_and_protected_paths_are_denied(tmp_path):
    home, _, executor = setup(tmp_path)
    source = home / "public.elf"
    source.write_bytes(bytes.fromhex("7f454c46") + b"\\x00" * 32)
    symlink = home / "link.elf"
    symlink.symlink_to(source)
    blocked = executor.execute("inspect_artifact_local", source=str(symlink))
    assert not blocked.success
    protected = home / ".ssh"
    protected.mkdir()
    secret = protected / "id_rsa"
    secret.write_bytes(b"private key")
    blocked = executor.execute("inspect_artifact_local", source=str(secret))
    assert not blocked.success
    assert not executor.execute(
        "inspect_artifact_local", source="/etc/passwd"
    ).success


def test_oversize_and_zip_bombs_fail_closed(tmp_path, monkeypatch):
    import nexus.tools.static_analysis as module
    home, _, executor = setup(tmp_path)
    monkeypatch.setattr(module, "MAX_FILE_BYTES", 10)
    bigger = home / "large.elf"
    bigger.write_bytes(b"a" * 11)
    assert not executor.execute(
        "inspect_artifact_local", source=str(bigger)
    ).success
    monkeypatch.setattr(module, "MAX_FILE_BYTES", 128 * 1024 * 1024)
    monkeypatch.setattr(module, "MAX_ARCHIVE_MEMBERS", 2)
    z = home / "too-many.zip"
    with zipfile.ZipFile(z, "w") as archive:
        for number in range(3):
            archive.writestr(f"entry-{number}", b"abc")
    assert not executor.execute("inspect_artifact_local", source=str(z)).success


@pytest.mark.parametrize("phrase", [
    "Analise o arquivo /home/usuario/Downloads/programa.exe",
    "Inspecione o aplicativo /home/usuario/Downloads/aplicativo.apk",
    "Analise o binário /home/usuario/Downloads/programa.elf",
])
def test_chat_routes_exact_rea_analysis_without_ollama(phrase):
    from nexus.agent.planner import _simple_creative_request
    action = _simple_creative_request(
        json.dumps({"mensagem_atual": phrase, "historico": []}),
    )
    assert action is not None
    assert action[0] == "inspect_artifact_local"
    assert action[1]["source"].startswith("/home/usuario/")


def test_prior_history_cannot_trigger_static_inspection():
    from nexus.agent.planner import _simple_creative_request
    document = json.dumps({
        "mensagem_atual": "O que é engenharia reversa?",
        "historico": [
            {"usuario": "Analise o arquivo /home/usuario/Downloads/app.exe"},
        ],
    })
    assert _simple_creative_request(document) is None


def test_agent_executes_only_with_confirmation_and_never_loads_ollama(tmp_path):
    home, _, executor = setup(tmp_path, approved=True)
    sample = home / "example.wasm"
    sample.write_bytes(bytes.fromhex("0061736d01000000"))

    class Model:
        def generate(self, request):
            pytest.fail("Complete static request cannot start Ollama")

    planner = AgentPlanner(Model(), executor.registry, executor)
    query = json.dumps({
        "mensagem_atual": f"Analise o arquivo {sample}",
        "historico": [],
    })
    result = planner.run(query)
    assert result.success
    assert result.tool_result is not None
    assert result.tool_result.data["kind"] == "WASM"
