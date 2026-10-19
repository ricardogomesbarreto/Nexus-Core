"""Bounded local color analysis requires consent and never stores a copy."""

import json
from pathlib import Path
import tempfile
import unittest

from nexus.agent.planner import AgentPlanner, _simple_creative_request
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import ImageColorsTool, ToolExecutor, ToolRegistry


class Confirmation:
    def __init__(self):
        self.approved = False
        self.requests = []

    def confirm(self, request):
        self.requests.append(request)
        return self.approved


class ImageColorsTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.home = Path(self.temp.name) / "home"
        self.home.mkdir()
        policy = PathSecurity()
        policy.home = self.home
        policy.protected_paths = [self.home / ".ssh"]
        registry = ToolRegistry()
        registry.register(ImageColorsTool())
        self.confirmation = Confirmation()
        self.executor = ToolExecutor(registry, SecurityGate(
            path_security=policy, audit_logger=AuditLogger(Path(self.temp.name) / "audit.log")),
            self.confirmation)
        self.photo = self.home / "foto.png"

    def test_consent_result_and_original_untouched(self):
        try:
            from PIL import Image
        except ImportError:
            self.skipTest("Pillow opcional")
        Image.new("RGB", (4, 3), (0, 0, 0)).save(self.photo)
        original = self.photo.read_bytes()
        self.assertFalse(self.executor.execute("image_colors_local", source=str(self.photo)).success)
        self.confirmation.approved = True
        result = self.executor.execute("image_colors_local", source=str(self.photo))
        self.assertTrue(result.success)
        self.assertEqual(result.data, {"width": 4, "height": 3,
                                       "brightness": 0, "dark_percent": 100,
                                       "light_percent": 0})
        self.assertEqual(self.photo.read_bytes(), original)
        self.assertEqual([p.name for p in self.home.iterdir()], ["foto.png"])
        self.assertEqual(len(self.confirmation.requests[0].resources), 1)

    def test_rejects_invalid_content_and_symlink(self):
        self.photo.write_bytes(b"not a PNG")
        self.confirmation.approved = True
        self.assertFalse(self.executor.execute("image_colors_local", source=str(self.photo)).success)
        linked = self.home / "alias.png"
        linked.symlink_to(self.photo)
        self.assertFalse(self.executor.execute("image_colors_local", source=str(linked)).success)

    def test_current_turn_only(self):
        phrase = f"Analise as cores da foto {self.photo}"
        self.assertEqual(_simple_creative_request(phrase),
                         ("image_colors_local", {"source": str(self.photo)}))
        self.assertEqual(AgentPlanner(None, self.executor.registry, self.executor).plan(phrase).arguments,
                         {"source": str(self.photo)})
        self.assertIsNone(_simple_creative_request(json.dumps({
            "mensagem_atual": "Olá", "historico": [phrase]})))


if __name__ == "__main__":
    unittest.main()
