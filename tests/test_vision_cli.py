"""Explicit-only vision CLI, no routine application or database startup."""
import json
import io

import pytest
from PIL import Image


def test_capability_check_does_not_start_app(monkeypatch, capsys):
    import nexus.main as module
    import nexus.vision.cli as vision
    monkeypatch.setattr(module, "build_application", lambda: pytest.fail("No agent"))
    monkeypatch.setattr(vision, "vision_dependencies",
                        lambda: {"screen_capture_tested": False})
    module.cli(["--vision-check"])
    assert json.loads(capsys.readouterr().out) == {"screen_capture_tested": False}


@pytest.mark.parametrize("args", [
    ["--vision-screen", "--vision-camera", "0"],
    ["--vision-image", "/home/me/photo.png", "--vision-screen"],
    ["--vision-check", "--agent-prompt", "test"],
    ["--vision-screen", "--memory-list"],
    ["--vision-screen", "--knowledge-list"],
    ["--vision-question", "What is this?"],
    ["--vision-model", "other:model"],
    ["--vision-check", "--vision-question", "test"],
    ["--vision-check", "--vision-model", "other:model"],
    ["--camera-test", "0", "--vision-question", "Descreva"],
    ["--camera-list", "--agent-prompt", "teste"],
    ["--camera-list", "--camera-test", "0"],
])
def test_cli_rejects_inert_or_conflicting_vision_modes(args):
    import nexus.main as module
    with pytest.raises(SystemExit) as error:
        module.cli(args)
    assert error.value.code == 2


def test_image_analysis_is_opt_in_and_uses_no_agent(monkeypatch, capsys):
    import nexus.main as module
    import nexus.vision.cli as visual
    calls = []

    class StubVision:
        def __init__(self, cfg):
            calls.append("init")

        def image_from_file(self, path):
            calls.append(("file", path))
            return b"image"

        def describe(self, image, *, question, model):
            calls.append(("describe", image, question, model))
            return {"model": model, "description": "Imagem recebida."}

    original = visual.execute_vision
    monkeypatch.setattr(visual, "execute_vision",
                        lambda options: original(options, vision_factory=StubVision))
    monkeypatch.setattr(module, "build_application",
                        lambda: pytest.fail("No application startup"))
    module.cli(["--vision-image", "/home/me/photo.png",
                "--vision-question", "Descreva"])
    assert calls == [
        "init", ("file", "/home/me/photo.png"),
        ("describe", b"image", "Descreva", "gemma3:4b"),
    ]
    assert json.loads(capsys.readouterr().out)["description"] == "Imagem recebida."


def test_camera_inventory_does_not_capture_or_start_agent(monkeypatch, capsys):
    import nexus.main as module
    from nexus.vision.local import LocalVision
    monkeypatch.setattr(module, "build_application", lambda: pytest.fail("No agent"))
    monkeypatch.setattr(LocalVision, "cameras", staticmethod(lambda: [(2, "Webcam USB")]))
    module.cli(["--camera-list"])
    result = json.loads(capsys.readouterr().out)
    assert result["devices"] == [{"index": 2, "name": "Webcam USB"}]
    assert result["frames_captured"] is False


def test_camera_test_captures_only_a_frame_without_inference(monkeypatch, capsys):
    import nexus.main as module
    import nexus.vision.cli as visual
    monkeypatch.setattr(module, "build_application", lambda: pytest.fail("No agent"))
    image = io.BytesIO()
    Image.new("RGB", (12, 8), "red").save(image, format="PNG")
    calls = []

    class StubVision:
        def __init__(self, cfg): pass
        def camera(self, index):
            calls.append(index)
            return image.getvalue()
        def describe(self, *args, **kwargs):
            pytest.fail("Diagnostic must never call Ollama")

    original = visual.execute_vision
    monkeypatch.setattr(visual, "execute_vision",
                        lambda options: original(options, vision_factory=StubVision))
    module.cli(["--camera-test", "2"])
    result = json.loads(capsys.readouterr().out)
    assert calls == [2]
    assert result["status"] == "frame_captured"
    assert (result["width"], result["height"]) == (12, 8)
    assert result["image_saved"] is False and result["ollama_used"] is False


def test_camera_test_failure_returns_diagnostic_json_not_image(monkeypatch, capsys):
    import nexus.main as module
    import nexus.vision.cli as visual
    from nexus.vision.local import VisionError
    monkeypatch.setattr(module, "build_application", lambda: pytest.fail("No agent"))

    class StubVision:
        def __init__(self, cfg): pass
        def camera(self, index):
            raise VisionError("A câmera está ocupada.")

    original = visual.execute_vision
    monkeypatch.setattr(visual, "execute_vision",
                        lambda options: original(options, vision_factory=StubVision))
    with pytest.raises(SystemExit) as error:
        module.cli(["--camera-test", "0"])
    assert error.value.code == 1
    result = json.loads(capsys.readouterr().out)
    assert result["status"] == "error"
    assert "ocupada" in result["message"]
    assert result["ollama_used"] is False
