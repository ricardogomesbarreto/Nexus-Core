"""Vision model isolation and simulated capture backends."""
import base64
import io
import subprocess

import pytest
from PIL import Image

from nexus.config.settings import Settings
from nexus.models.resource_budget import ResourceBudget
from nexus.vision.local import LocalVision, VisionError, VisionInputError, vision_dependencies


def image_bytes():
    output = io.BytesIO()
    Image.new("RGB", (16, 16), (120, 120, 120)).save(output, format="PNG")
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


def test_cancelled_visual_preparation_never_posts_image_to_ollama(monkeypatch):
    transport = Transport({"done": True, "message": {"content": "sem uso"}})
    service = LocalVision(Settings(), transport=transport)
    state = {"cancelled": False}

    def prepare(image, *, max_edge):
        state["cancelled"] = True
        return image

    monkeypatch.setattr(service, "_normalize_image", prepare)
    with pytest.raises(VisionError, match="Análise cancelada"):
        service.describe(image_bytes(), is_cancelled=lambda: state["cancelled"])
    assert transport.calls == []


def test_already_cancelled_visual_request_skips_model_lookup():
    class TransportWithLookup(Transport):
        def list_models(self):
            raise AssertionError("lookup must not run after cancellation")

    service = LocalVision(Settings(), transport=TransportWithLookup({}))
    with pytest.raises(VisionError, match="Análise cancelada"):
        service.describe(image_bytes(), is_cancelled=lambda: True)


def test_eco_refuses_large_model_before_normalizing_or_sending_image(monkeypatch):
    class Inventory:
        sent = False

        def list_models(self): return ["gemma3:4b"]
        def model_size(self, name): return 3 * 1024 ** 3
        def chat(self, *, payload, timeout):
            self.sent = True
            raise AssertionError("memory gate must stop inference")

    monkeypatch.setenv("NEXUS_RESOURCE_PROFILE", "eco")
    monkeypatch.setattr(ResourceBudget, "available_now_mib", staticmethod(lambda: 2048))
    transport = Inventory()
    service = LocalVision(Settings(), transport=transport)
    monkeypatch.setattr(service, "_normalize_image",
                        lambda *a, **kw: (_ for _ in ()).throw(AssertionError("decode")))
    with pytest.raises(VisionError, match="2048 MiB disponíveis") as error:
        service.describe(b"private-frame")
    assert "Nenhuma imagem foi enviada" in str(error.value)
    assert not transport.sent


def test_eco_allows_model_when_local_memory_estimate_has_headroom(monkeypatch):
    class Inventory:
        def list_models(self): return ["gemma3:4b"]
        def model_size(self, name): return 2 * 1024 ** 3
        def chat(self, *, payload, timeout):
            return {"done": True, "message": {"content": "Uma imagem."}}

    monkeypatch.setenv("NEXUS_RESOURCE_PROFILE", "eco")
    monkeypatch.setattr(ResourceBudget, "available_now_mib", staticmethod(lambda: 3072))
    assert LocalVision(Settings(), transport=Inventory()).describe(image_bytes())[
        "description"] == "Uma imagem."


def test_eco_blocks_vision_under_one_gib_without_model_metadata(monkeypatch):
    monkeypatch.setenv("NEXUS_RESOURCE_PROFILE", "eco")
    monkeypatch.setattr(ResourceBudget, "available_now_mib", staticmethod(lambda: 617))
    transport = Transport({})
    with pytest.raises(VisionError, match="abaixo de 1 GiB"):
        LocalVision(Settings(), transport=transport).describe(image_bytes())
    assert transport.calls == []


@pytest.mark.parametrize("response", [
    {}, {"done": False, "message": {"content": "unfinished"}},
    {"done": True, "message": {}},
    {"done": True, "message": {"content": ""}},
])
def test_model_response_must_be_finished_nonempty_text(response):
    with pytest.raises(VisionError):
        LocalVision(Settings(), transport=Transport(response)).describe(image_bytes())


@pytest.mark.parametrize("camera", [-1, 256, "0", True, None])
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
    service._capture = lambda args, **kwargs: calls.append(args) or image_bytes()
    monkeypatch.setattr(service, "selected_screen", lambda *, window: calls.append(
        ("portal", window)) or image_bytes())
    service.screen()
    monkeypatch.delenv("WAYLAND_DISPLAY")
    monkeypatch.setenv("DISPLAY", ":1")
    service.screen()
    service.camera(2)
    service.camera(10)
    assert calls[0] == ("portal", False)  # Tela requests a screen, not a window.
    assert calls[1] == ["/bin/import", "-window", "root", "png:-"]
    assert calls[2][-1] == "pipe:1"
    assert "/dev/video2" in calls[2]
    assert "-nostdin" in calls[2]
    assert "/dev/video10" in calls[3]


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


def test_capture_can_normalize_directly_to_eco_edge(monkeypatch):
    class Result:
        returncode = 0

    def run(argv, *, stdout, **kwargs):
        output = io.BytesIO()
        Image.new("RGB", (1800, 1200), "purple").save(output, "PNG")
        stdout.write(output.getvalue())
        return Result()

    monkeypatch.setattr("nexus.vision.local.subprocess.run", run)
    with Image.open(io.BytesIO(LocalVision._capture(["capture-test"], max_edge=768))) as out:
        assert max(out.size) <= 768


def test_camera_skips_initial_exposure_frames(monkeypatch):
    service = LocalVision(Settings())
    commands = []
    monkeypatch.setattr("nexus.vision.local.shutil.which", lambda n: "/usr/bin/ffmpeg")
    service._capture = lambda args, **kwargs: commands.append(args) or image_bytes()
    assert service.camera(0).startswith(b"\x89PNG")
    assert len(commands) == 1  # One authorized still photo, no continuous preview.
    assert commands[0][commands[0].index("-vf") + 1] == r"select=gte(n\,8)"
    assert commands[0][commands[0].index("-frames:v") + 1] == "1"


def test_black_camera_capture_is_not_sent_to_visual_model(monkeypatch):
    from PIL import Image
    blank = io.BytesIO()
    Image.new("RGB", (100, 80), (0, 0, 0)).save(blank, "PNG")
    service = LocalVision(Settings())
    monkeypatch.setattr("nexus.vision.local.shutil.which", lambda n: "/usr/bin/ffmpeg")
    service._capture = lambda args, **kwargs: blank.getvalue()
    with pytest.raises(VisionError, match="praticamente preta"):
        service.camera(0)


def test_bright_camera_frame_remains_usable():
    assert LocalVision._camera_frame_is_dark(image_bytes()) is False
