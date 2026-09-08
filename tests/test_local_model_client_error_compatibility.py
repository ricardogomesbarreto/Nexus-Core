import pytest

from nexus.models.local_model import (
    LocalModelClient,
    LocalModelRequest,
)
from nexus.models.ollama_transport import (
    OllamaHTTPError,
    OllamaInvalidJSONError,
    OllamaTimeoutError,
    OllamaUnavailableError,
)


class RaisingTransport:
    def __init__(self, error):
        self.error = error

    def chat(self, *, payload, timeout):
        raise self.error


@pytest.mark.parametrize(
    "backend_error",
    [
        OllamaUnavailableError(
            "legacy unavailable"
        ),
        OllamaTimeoutError(
            "legacy timeout"
        ),
        OllamaHTTPError(
            "legacy http"
        ),
        OllamaInvalidJSONError(
            "legacy invalid json"
        ),
    ],
)
def test_legacy_client_preserves_transport_error_surface(
    backend_error,
):
    client = LocalModelClient(
        model="qwen3:1.7b",
        transport=RaisingTransport(
            backend_error
        ),
        timeout=30.0,
    )

    with pytest.raises(
        type(backend_error)
    ) as exc_info:
        client.generate(
            LocalModelRequest(
                prompt="NEXUS_LEGACY_ERROR_COMPAT"
            )
        )

    assert exc_info.value is backend_error
