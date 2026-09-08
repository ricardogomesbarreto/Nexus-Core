import pytest

from nexus.models.contracts import (
    ModelProtocolError,
    ModelProviderError,
    ModelProviderTimeoutError,
    ModelProviderUnavailableError,
    ModelRequest,
)
from nexus.models.ollama_provider import OllamaProvider
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


def make_provider(error):
    return OllamaProvider(
        model="qwen3:1.7b",
        transport=RaisingTransport(error),
        timeout=30.0,
    )


def make_request():
    return ModelRequest(
        prompt="NEXUS_ERROR_MAPPING"
    )


def test_ollama_unavailable_maps_to_generic_provider_unavailable():
    backend_error = OllamaUnavailableError(
        "ollama unavailable"
    )

    provider = make_provider(backend_error)

    with pytest.raises(
        ModelProviderUnavailableError
    ) as exc_info:
        provider.generate(make_request())

    assert exc_info.value.__cause__ is backend_error


def test_ollama_timeout_maps_to_generic_provider_timeout():
    backend_error = OllamaTimeoutError(
        "ollama timeout"
    )

    provider = make_provider(backend_error)

    with pytest.raises(
        ModelProviderTimeoutError
    ) as exc_info:
        provider.generate(make_request())

    assert exc_info.value.__cause__ is backend_error


def test_ollama_http_error_maps_to_generic_provider_error():
    backend_error = OllamaHTTPError(
        "ollama http error"
    )

    provider = make_provider(backend_error)

    with pytest.raises(
        ModelProviderError
    ) as exc_info:
        provider.generate(make_request())

    assert type(exc_info.value) is ModelProviderError
    assert exc_info.value.__cause__ is backend_error


def test_ollama_invalid_json_maps_to_generic_protocol_error():
    backend_error = OllamaInvalidJSONError(
        "ollama invalid json"
    )

    provider = make_provider(backend_error)

    with pytest.raises(
        ModelProtocolError
    ) as exc_info:
        provider.generate(make_request())

    assert exc_info.value.__cause__ is backend_error


@pytest.mark.parametrize(
    (
        "backend_error",
        "backend_error_type",
    ),
    [
        (
            OllamaUnavailableError(
                "unavailable"
            ),
            OllamaUnavailableError,
        ),
        (
            OllamaTimeoutError(
                "timeout"
            ),
            OllamaTimeoutError,
        ),
        (
            OllamaHTTPError(
                "http"
            ),
            OllamaHTTPError,
        ),
        (
            OllamaInvalidJSONError(
                "json"
            ),
            OllamaInvalidJSONError,
        ),
    ],
)
def test_ollama_transport_errors_do_not_escape_provider_boundary(
    backend_error,
    backend_error_type,
):
    provider = make_provider(
        backend_error
    )

    try:
        provider.generate(
            make_request()
        )
    except backend_error_type:
        pytest.fail(
            "erro específico do transporte Ollama "
            "escapou da fronteira do provider"
        )
    except Exception:
        pass
    else:
        pytest.fail(
            "provider deveria propagar erro genérico"
        )
