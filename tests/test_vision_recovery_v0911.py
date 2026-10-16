"""Regression tests: distinguish local Ollama failures without leaking images."""

import io
import pytest
from PIL import Image

from nexus.config.settings import Settings
from nexus.models.ollama_transport import (
    OllamaHTTPError, OllamaTimeoutError, OllamaUnavailableError,
    OllamaTransport,
)
from nexus.vision.local import LocalVision, VisionError


def picture(width=80, height=60, format="PNG"):
    output = io.BytesIO()
    Image.new("RGB", (width, height), (120, 50, 85)).save(output, format)
    return output.getvalue()


class StubTransport:
    def __init__(self, exc):
        self.exc = exc
        self.requests = []

    def chat(self, *, payload, timeout):
        self.requests.append((payload, timeout))
        raise self.exc


@pytest.mark.parametrize("error,fragment", [
    (OllamaHTTPError("HTTP 500", status_code=500), "falta de recursos"),
    (OllamaHTTPError("HTTP 400", status_code=400), "rejeitou a requisição"),
    (OllamaHTTPError("HTTP 404", status_code=404), "não foi encontrado"),
    (OllamaHTTPError("HTTP 503", status_code=503), "falta de recursos"),
    (OllamaTimeoutError("timeout"), "excedeu o tempo"),
    (OllamaUnavailableError("offline"), "127.0.0.1:11434"),
])
def test_visual_errors_offer_specific_offline_diagnostics(error, fragment):
    transport = StubTransport(error)
    vision = LocalVision(Settings(local_model_timeout=41), transport=transport)
    with pytest.raises(VisionError, match=fragment) as raised:
        vision.describe(picture())
    assert "120, 50, 85" not in str(raised.value)
    assert len(transport.requests) == 1
    payload, timeout = transport.requests[0]
    assert timeout == 41
    assert payload["stream"] is False
    assert payload["options"]["num_ctx"] <= 2048
    assert payload["options"]["num_predict"] <= 320


def test_vision_normalization_downscales_large_images_and_strips_metadata():
    normalized = LocalVision._normalize_image(picture(2048, 1400, "PNG"))
    with Image.open(io.BytesIO(normalized)) as output:
        assert max(output.size) <= LocalVision.MODEL_IMAGE_EDGE
        assert output.info == {}
    assert len(normalized) < 6 * 1024 * 1024


def test_small_png_stays_png_for_existing_workflows():
    assert LocalVision._normalize_image(picture())[:8] == b"\x89PNG\r\n\x1a\n"


def test_transport_http_status_is_available_as_numeric_metadata():
    from urllib.error import HTTPError

    def fail(request, *, timeout):
        raise HTTPError(
            "http://127.0.0.1:11434/api/chat", 500,
            "Internal Server Error", None, None,
        )

    transport = OllamaTransport(opener=fail)
    with pytest.raises(OllamaHTTPError) as failure:
        transport.chat(payload={"model": "gemma3:4b"}, timeout=4)
    assert failure.value.status_code == 500
    assert "http://127" not in str(failure.value)
