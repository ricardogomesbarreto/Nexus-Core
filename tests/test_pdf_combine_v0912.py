"""Two-source PdfCraft action: exact intent, consent and no partial overwrite."""

import json
from pathlib import Path
import subprocess
from types import SimpleNamespace

import pytest

from nexus.agent.planner import AgentPlanner, ProposalError, _simple_creative_request
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import PdfCombineTool, ToolExecutor, ToolRegistry
from scripts.validate_craft_cli import _write_pdf


class Confirmation:
    def __init__(self, approved):
        self.approved = approved
        self.calls = []

    def confirm(self, request):
        self.calls.append(request)
        return self.approved


def setup(tmp_path, approved=True):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    registry = ToolRegistry()
    registry.register(PdfCombineTool())
    confirmation = Confirmation(approved)
    executor = ToolExecutor(registry, SecurityGate(path_security=policy,
                            audit_logger=AuditLogger(tmp_path / "audit.log")), confirmation)
    a, b, out = home / "a.pdf", home / "b.pdf", home / "junto.pdf"
    _write_pdf(a)
    _write_pdf(b)
    b.write_bytes(b.read_bytes().replace(b"NEXUS CORE CLI", b"SECOND PDF DOC"))
    return executor, confirmation, a, b, out


def test_combine_uses_private_copies_in_order_and_requires_consent(tmp_path, monkeypatch):
    executor, confirmation, a, b, out = setup(tmp_path, False)
    argv_seen = []

    def fake_run(argv, **kwargs):
        argv_seen.append(argv)
        assert argv[0:2] == ["/trusted/pdfcraft-cli", "combine"]
        assert Path(argv[2]).read_bytes() == a.read_bytes()
        assert Path(argv[3]).read_bytes() == b.read_bytes()
        assert argv[4] == "--out" and kwargs["timeout"] == 90
        assert kwargs["stdin"] == subprocess.DEVNULL
        assert Path(argv[2]).parent == Path(argv[3]).parent == Path(argv[5]).parent
        _write_pdf(Path(argv[5]))
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.pdf_combine.shutil.which", lambda _: "/trusted/pdfcraft-cli")
    monkeypatch.setattr("nexus.tools.pdf_combine.subprocess.run", fake_run)
    args = {"source_a": str(a), "source_b": str(b), "output": str(out)}
    assert not executor.execute("pdf_combine_local", **args).success
    assert not argv_seen
    assert [r.name for r in confirmation.calls[0].resources] == ["source_a", "source_b", "output"]
    confirmation.approved = True
    assert executor.execute("pdf_combine_local", **args).data == {"path": str(out)}
    assert out.stat().st_mode & 0o777 == 0o600 and len(argv_seen) == 1
    assert not executor.execute("pdf_combine_local", **args).success
    assert len(argv_seen) == 2  # Existing output refused at the exclusive-write boundary.


@pytest.mark.parametrize("failure", ["missing_cli", "bad_pdf", "symlink", "oversize", "timeout", "bad_exit"])
def test_combine_fails_closed_without_output(tmp_path, monkeypatch, failure):
    executor, _, a, b, out = setup(tmp_path)
    monkeypatch.setattr("nexus.tools.pdf_combine.shutil.which",
                        lambda _: None if failure == "missing_cli" else "/trusted/pdfcraft-cli")
    if failure == "bad_pdf":
        a.write_bytes(b"not PDF")
    if failure == "symlink":
        b.unlink()
        b.symlink_to(a)
    if failure == "oversize":
        with b.open("ab") as f:
            f.truncate(10 * 1024 * 1024 + 1)

    def fake_run(argv, **kwargs):
        if failure == "timeout":
            raise subprocess.TimeoutExpired(argv, 90)
        if failure == "bad_exit":
            return SimpleNamespace(returncode=1)
        raise AssertionError("CLI must not run")

    monkeypatch.setattr("nexus.tools.pdf_combine.subprocess.run", fake_run)
    result = executor.execute("pdf_combine_local", source_a=str(a),
                              source_b=str(b), output=str(out))
    assert not result.success and not out.exists()


def test_untrusted_output_and_dest_symlink_never_committed(tmp_path, monkeypatch):
    executor, _, a, b, out = setup(tmp_path)
    data = a.read_bytes()
    monkeypatch.setattr("nexus.tools.pdf_combine.shutil.which", lambda _: "/trusted/pdfcraft-cli")

    def invalid(argv, **kwargs):
        Path(argv[5]).write_bytes(b"%PDF-1.7\nbroken")
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.pdf_combine.subprocess.run", invalid)
    args = {"source_a": str(a), "source_b": str(b), "output": str(out)}
    assert not executor.execute("pdf_combine_local", **args).success
    assert not out.exists()

    def linked(argv, **kwargs):
        Path(argv[5]).symlink_to(a)
        return SimpleNamespace(returncode=0)

    monkeypatch.setattr("nexus.tools.pdf_combine.subprocess.run", linked)
    assert not executor.execute("pdf_combine_local", **args).success
    assert not out.exists() and a.read_bytes() == data
    out.symlink_to(a)
    assert not executor.execute("pdf_combine_local", **args).success
    assert a.read_bytes() == data


def test_current_turn_only_and_exact_source_order(tmp_path):
    executor, _, a, b, out = setup(tmp_path)
    utterance = f"Junte os PDFs {a} e {b} em {out}"
    intent = _simple_creative_request(json.dumps({"mensagem_atual": utterance, "historico": []}))
    assert intent == ("pdf_combine_local", {"source_a": str(a), "source_b": str(b),
                                             "output": str(out)})
    assert _simple_creative_request(json.dumps({"mensagem_atual": "Oi", "historico": [utterance]})) is None
    assert _simple_creative_request(f"Junte os PDFs {a} e {b}") is None
    planner = AgentPlanner(None, executor.registry, executor)
    assert planner.plan(utterance).arguments == intent[1]
    for wrong in ({"source_a": str(b), "source_b": str(a), "output": str(out)},
                  {"source_a": str(a), "source_b": str(b), "output": str(b)}):
        class Router:
            def generate(self, request):
                from nexus.models.contracts import ModelResponse
                payload = json.dumps({"type": "tool_call", "tool_name": "pdf_combine_local", "arguments": wrong})
                return ModelResponse(payload, "test", True, 0, 0)

        with pytest.raises(ProposalError):
            AgentPlanner(Router(), executor.registry, executor).plan(
                f"Por favor, {utterance}")
