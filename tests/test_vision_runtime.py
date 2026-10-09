"""Vision model isolation and simulated capture backends."""
import base64
import io
import subprocess

import pytest
from PIL import Image

from nexus.config.settings import Settings
from nexus.vision.local import LocalVision, VisionError, VisionInputError, vision_dependencies


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (16, 16)).save(output, format="PNG")
    return output.getvalue()


class Transport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(self, *, payload, timeout):
        self.calls.append((payload, timeout))
        return self.response


def test_multimodal_local_payload_never_invokes_agent_tools():
    transport = Transport({"done": True, "message": {"content": "Uma tela simples."}})
    service = LocalVision(Settings(local_model_timeout=23.0), transport=transport)
    result = service.describe(image_bytes(), question="Descreva", model="gemma3:4b")
    assert result == {"model": "gemma3:4b", "description": "Uma tela simples."}
    payload, timeout = transport.calls[0]
    assert timeout == 23.0
    assert payload["stream"] is False
    assert "tools" not in payload
    assert payload["messages"][0]["content"] == "Descreva"
    image = base64.b64decode(payload["messages"][0]["images"][0])
    assert image.startswith(b"\x89PNG")


@pytest.mark.parametrize("response", [
    {}, {"done": False, "message": {"content": "unfinished"}},
    {"done": True, "message": {}},
    {"done": True, "message": {"content": ""}},
])
def test_model_response_must_be_finished_nonempty_text(response):
    with pytest.raises(VisionError):
        LocalVision(Settings(), transport=Transport(response)).describe(image_bytes())


@pytest.mark.parametrize("camera", [-1, 10, "0", True, None])
def test_invalid_camera_index_fails_before_hardware(monkeypatch, camera):
    monkeypatch.setattr("nexus.vision.local.shutil.which", lambda n: None)
    with pytest.raises(VisionInputError):
        LocalVision(Settings()).camera(camera)


def test_missing_graphical_session_fails_closed(monkeypatch):
    monkeypatch.delenv("DISPLAY", raising=False)
    monkeypatch.delenv("WAYLAND_DISPLAY", raising=False)
    with pytest.raises(VisionError):
        LocalVision(Settings()).screen()


def test_capture_backends_use_fixed_arguments(monkeypatch):
    service = LocalVision(Settings())
    calls = []
    monkeypatch.setattr("nexus.vision.local.shutil.which", lambda n: "/bin/" + n)
    monkeypatch.setenv("WAYLAND_DISPLAY", "wayland-0")
    service._capture = lambda args: calls.append(args) or image_bytes()
    service.screen()
    monkeypatch.delenv("WAYLAND_DISPLAY")
    monkeypatch.setenv("DISPLAY", ":1")
    service.screen()
    service.camera(2)
    assert calls[0] == ["/bin/grim", "-"]
    assert calls[1] == ["/bin/import", "-window", "root", "png:-"]
    assert calls[2][-1] == "pipe:1"
    assert "/dev/video2" in calls[2]
    assert "-nostdin" in calls[2]


def test_capture_output_is_bounded(monkeypatch):
    class Result:
        returncode = 0

    def run(argv, *, stdout, **kwargs):
        stdout.write(b"x" * (LocalVision.MAX_INPUT_BYTES + 1))
        return Result()

    monkeypatch.setattr("nexus.vision.local.subprocess.run", run)
    with pytest.raises(VisionInputError):
        LocalVision._capture(["fake-capture"])


def test_capture_timeout_is_sanitized(monkeypatch):
    def run(argv, **kwargs):
        raise subprocess.TimeoutExpired(argv, 1)

    monkeypatch.setattr("nexus.vision.local.subprocess.run", run)
    with pytest.raises(VisionError, match="tempo limite"):
        LocalVision._capture(["fake-capture"])


def test_capability_probe_does_not_use_hardware(monkeypatch):
    monkeypatch.setattr("nexus.vision.local.shutil.which", lambda n: None)
    monkeypatch.setattr("importlib.util.find_spec", lambda n: None)
    result = vision_dependencies()
    assert result["camera_capture_tested"] is False
    assert result["screen_capture_tested"] is False
    assert not any(result["checks"].values())


def test_capture_applies_os_file_size_limit(monkeypatch):
    options = {}
    class Result:
        returncode = 0

    def run(argv, *, stdout, preexec_fn=None, **kwargs):
        options["preexec_fn"] = preexec_fn
        stdout.write(image_bytes())
        return Result()

    monkeypatch.setattr("nexus.vision.local.subprocess.run", run)
    assert LocalVision._capture(["capture-test"]).startswith(b"\x89PNG")
    assert options["preexec_fn"] == LocalVision._limit_capture_output
