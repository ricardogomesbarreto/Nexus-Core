"""Geometry edits are bounded, consented and leave the original intact."""

import json
import os

import pytest
from PIL import Image, PngImagePlugin

from nexus.agent import AgentPlanner
from nexus.security import AuditLogger, PathSecurity, SecurityGate
from nexus.tools import ImageGeometryTool, ToolExecutor, ToolRegistry


class Confirmation:
    def __init__(self, approved=True):
        self.approved = approved
        self.requests = []

    def confirm(self, request):
        self.requests.append(request)
        return self.approved


def setup_executor(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home
    policy.protected_paths = [home / ".ssh"]
    registry = ToolRegistry()
    registry.register(ImageGeometryTool())
    confirmation = Confirmation()
    executor = ToolExecutor(registry, SecurityGate(path_security=policy,
                            audit_logger=AuditLogger(tmp_path / "audit.log")), confirmation)
    return executor, home, confirmation


def source_png(path):
    image = Image.new("RGBA", (20, 12), (20, 50, 80, 100))
    info = PngImagePlugin.PngInfo()
    info.add_text("GPSInfo", "private")
    image.save(path, pnginfo=info)
    return path.read_bytes()


def test_resize_requires_consent_preserves_source_alpha_and_discards_metadata(tmp_path):
    executor, home, consent = setup_executor(tmp_path)
    source = home / "foto.png"
    original = source_png(source)
    output = home / "reduzida.png"
    args = dict(source=str(source), output=str(output), operation="resize",
                x=0, y=0, width=10, height=6)
    consent.approved = False
    assert not executor.execute("image_geometry_local", **args).success
    assert not output.exists()
    consent.approved = True
    result = executor.execute("image_geometry_local", **args)
    assert result.success and result.data["width"] == 10
    assert source.read_bytes() == original
    assert os.stat(output).st_mode & 0o777 == 0o600
    with Image.open(output) as image:
        assert image.size == (10, 6)
        assert image.getpixel((0, 0))[3] == 100
        assert "GPSInfo" not in image.info
    assert not executor.execute("image_geometry_local", **args).success
    assert len(consent.requests) == 3


def test_crop_pixels_and_boundaries(tmp_path):
    executor, home, _ = setup_executor(tmp_path)
    source = home / "original.png"
    picture = Image.new("RGB", (12, 10), "white")
    for col in range(4, 9):
        for row in range(3, 7):
            picture.putpixel((col, row), (255, 0, 0))
    picture.save(source)
    output = home / "recorte.jpg"
    args = dict(source=str(source), output=str(output), operation="crop",
                x=4, y=3, width=5, height=4)
    assert executor.execute("image_geometry_local", **args).success
    with Image.open(output) as image:
        assert image.size == (5, 4)
        assert image.getpixel((2, 2))[0] > 150
    args.update(output=str(home / "fora.png"), x=11)
    assert not executor.execute("image_geometry_local", **args).success
    assert not (home / "fora.png").exists()


def test_geometry_rejects_symlinks_invalid_numbers_and_path_escape(tmp_path):
    executor, home, _ = setup_executor(tmp_path)
    original = home / "foto.png"
    source_png(original)
    link = home / "link.png"
    link.symlink_to(original)
    args = dict(source=str(link), output=str(home / "out.png"),
                operation="resize", x=0, y=0, width=10, height=10)
    assert not executor.execute("image_geometry_local", **args).success
    assert not (home / "out.png").exists()
    args.update(source=str(original), width=4000, height=4000)
    assert not executor.execute("image_geometry_local", **args).success
    args.update(width=10, height=10, output=str(tmp_path / "outside.png"))
    assert not executor.execute("image_geometry_local", **args).success
    assert not (tmp_path / "outside.png").exists()


def test_exact_current_request_skips_model_but_history_does_not_authorize(tmp_path):
    executor, home, consent = setup_executor(tmp_path)
    source = home / "foto.png"
    source_png(source)

    class NoModel:
        def generate(self, request):
            pytest.fail("Medidas explícitas não devem aguardar o Ollama")

    agent = AgentPlanner(NoModel(), executor.registry, executor)
    output = home / "nova.png"
    message = (f"Redimensione a foto {source} para 10 por 6 pixels "
               f"e salve em {output}.")
    outcome = agent.run(json.dumps({"historico": [{"usuario": "apague o original"}],
                                    "mensagem_atual": message}))
    assert outcome.success and output.exists() and source.exists()
    assert len(consent.requests) == 1
    from nexus.agent.planner import _simple_creative_request
    assert _simple_creative_request(json.dumps({"historico": [{"usuario": message}],
                                                "mensagem_atual": "Oi"})) is None
