"""Explicit-only vision CLI, no routine application or database startup."""
import json

import pytest


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
