"""PDF page editing stays local, explicit and subject to the normal gate."""

import json
from pathlib import Path
import subprocess
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from nexus.agent.planner import AgentPlanner, ProposalError, _simple_creative_request
from nexus.models.contracts import ModelResponse
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import PdfOrganizeTool, ToolExecutor, ToolRegistry
from scripts.validate_craft_cli import _write_pdf


class Confirmation:
    def __init__(self, approved=True):
        self.approved = approved
        self.calls = []

    def confirm(self, request):
        self.calls.append(request)
        return self.approved


class PdfOrganizeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        self.home = base / "home"
        self.home.mkdir()
        policy = PathSecurity()
        policy.home = self.home
        policy.protected_paths = [self.home / ".ssh"]
        self.registry = ToolRegistry()
        self.registry.register(PdfOrganizeTool())
        self.confirmation = Confirmation()
        self.executor = ToolExecutor(
            self.registry,
            SecurityGate(path_security=policy, audit_logger=AuditLogger(base / "audit.log")),
            self.confirmation,
        )
        self.source = self.home / "original.pdf"
        self.output = self.home / "novo.pdf"
        _write_pdf(self.source)

    def args(self, **changes):
        return {**{"source": str(self.source), "output": str(self.output),
                   "operation": "rotate", "pages": "1", "value": 90}, **changes}

    def test_rotation_and_move_use_private_copy_and_approval(self):
        seen = []

        def fake_run(argv, **kwargs):
            seen.append(argv)
            self.assertEqual(argv[:2], ["/trusted/pdfcraft-cli", "edit"])
            self.assertEqual(Path(argv[2]).read_bytes(), self.source.read_bytes())
            self.assertEqual(argv[3], "--out")
            self.assertEqual(kwargs["timeout"], 90)
            self.assertEqual(kwargs["stdin"], subprocess.DEVNULL)
            _write_pdf(Path(argv[4]))
            return SimpleNamespace(returncode=0)

        with patch("nexus.tools.pdf_organize.shutil.which", return_value="/trusted/pdfcraft-cli"), \
             patch("nexus.tools.pdf_organize.subprocess.run", side_effect=fake_run):
            self.confirmation.approved = False
            self.assertFalse(self.executor.execute("pdf_organize_local", **self.args()).success)
            self.assertFalse(seen)
            self.confirmation.approved = True
            self.assertTrue(self.executor.execute("pdf_organize_local", **self.args()).success)
            self.assertEqual(seen[0][-2:], ["--rotate", "1:90"])
            self.assertEqual(self.output.stat().st_mode & 0o777, 0o600)
            self.output.unlink()
            self.assertTrue(self.executor.execute("pdf_organize_local", **self.args(
                operation="move", pages="1", value=2)).success)
            self.assertEqual(seen[1][-2:], ["--move", "1:2"])
        self.assertEqual([r.name for r in self.confirmation.calls[0].resources],
                         ["source", "output"])

    def test_invalid_inputs_and_untrusted_output_fail_without_new_file(self):
        with patch("nexus.tools.pdf_organize.shutil.which", return_value="/trusted/pdfcraft-cli"), \
             patch("nexus.tools.pdf_organize.subprocess.run") as run:
            for changes in ({"operation": "delete"}, {"value": 45},
                            {"operation": "move", "pages": "1,2"},
                            {"operation": "move", "value": 0},
                            {"pages": "1-5000"}, {"pages": "9999"}):
                self.assertFalse(self.executor.execute("pdf_organize_local", **self.args(**changes)).success)
            run.assert_not_called()
            def invalid(argv, **kwargs):
                Path(argv[4]).write_bytes(b"%PDF-1.7\nbroken")
                return SimpleNamespace(returncode=0)
            run.side_effect = invalid
            self.assertFalse(self.executor.execute("pdf_organize_local", **self.args()).success)
            self.assertFalse(self.output.exists())
            run.side_effect = lambda argv, **kwargs: (_ for _ in ()).throw(
                subprocess.TimeoutExpired(argv, 90))
            self.assertFalse(self.executor.execute("pdf_organize_local", **self.args()).success)
            self.assertFalse(self.output.exists())

    def test_symlinks_and_existing_destination_do_not_replace_original(self):
        with patch("nexus.tools.pdf_organize.shutil.which", return_value="/trusted/pdfcraft-cli"), \
             patch("nexus.tools.pdf_organize.subprocess.run") as run:
            self.output.symlink_to(self.source)
            self.assertFalse(self.executor.execute("pdf_organize_local", **self.args()).success)
            self.output.unlink()
            linked = self.home / "linked.pdf"
            linked.symlink_to(self.source)
            self.assertFalse(self.executor.execute("pdf_organize_local", **self.args(
                source=str(linked))).success)
            run.assert_not_called()

    def test_exact_intent_and_model_cannot_change_page_or_destination(self):
        rotate = f"Gire as páginas 1 do PDF {self.source} em 90 graus e salve em {self.output}"
        expected = self.args()
        self.assertEqual(_simple_creative_request(rotate), ("pdf_organize_local", expected))
        self.assertEqual(AgentPlanner(None, self.registry, self.executor).plan(rotate).arguments, expected)
        move = f"Mova a página 1 do PDF {self.source} para a posição 2 e salve em {self.output}"
        self.assertEqual(_simple_creative_request(move),
                         ("pdf_organize_local", self.args(operation="move", pages="1", value=2)))
        self.assertIsNone(_simple_creative_request(json.dumps({
            "mensagem_atual": "Oi", "historico": [rotate]})))

        class Router:
            def generate(self, request):
                return ModelResponse(json.dumps({"type": "tool_call",
                    "tool_name": "pdf_organize_local",
                    "arguments": {**expected, "value": 180}}), "test", True, 0, 0)

        with self.assertRaises(ProposalError):
            AgentPlanner(Router(), self.registry, self.executor).plan("Por favor, " + rotate)


if __name__ == "__main__":
    unittest.main()
