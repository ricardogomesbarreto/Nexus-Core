import json
from urllib.error import HTTPError, URLError

import pytest

from nexus.models.ollama_transport import (
    OllamaHTTPError,
    OllamaInvalidJSONError,
    OllamaTimeoutError,
    OllamaTransport,
    OllamaUnavailableError,
)


class FakeResponse:
    def __init__(
        self,
        body,
        *,
        status=200,
    ):
        self.body = body
        self.status = status

    def read(self):
        return self.body

    def __enter__(self):
        return self

    def __exit__(
        self,
        exc_type,
        exc_value,
        traceback,
    ):
        return False


class FakeOpener:
    def __init__(
        self,
        *,
        response=None,
        error=None,
    ):
        self.response = response
        self.error = error
        self.calls = []

    def __call__(
        self,
        request,
        *,
        timeout,
    ):
        self.calls.append(
            {
                "request": request,
                "timeout": timeout,
            }
        )

        if self.error is not None:
            raise self.error

        return self.response


def test_ollama_transport_posts_chat_payload():
    opener = FakeOpener(
        response=FakeResponse(
            json.dumps(
                {
                    "model": "qwen3:1.7b",
                    "done": True,
                    "message": {
                        "content": "NEXUS_OK",
                    },
                    "prompt_eval_count": 10,
                    "eval_count": 2,
                }
            ).encode("utf-8")
        )
    )

    transport = OllamaTransport(
        opener=opener
    )

    payload = {
        "model": "qwen3:1.7b",
        "messages": [
            {
                "role": "user",
                "content": "Teste",
            }
        ],
        "stream": False,
    }

    response = transport.chat(
        payload=payload,
        timeout=30.0,
    )

    assert response["model"] == "qwen3:1.7b"
    assert response["message"]["content"] == "NEXUS_OK"

    call = opener.calls[0]
    request = call["request"]

    assert call["timeout"] == 30.0

    assert (
        request.full_url
        == "http://127.0.0.1:11434/api/chat"
    )

    assert request.get_method() == "POST"

    assert json.loads(
        request.data.decode("utf-8")
    ) == payload

    assert (
        request.headers["Content-type"]
        == "application/json"
    )


def test_ollama_transport_maps_connection_failure():
    opener = FakeOpener(
        error=URLError(
            ConnectionRefusedError(
                "connection refused"
            )
        )
    )

    transport = OllamaTransport(
        opener=opener
    )

    with pytest.raises(
        OllamaUnavailableError
    ):
        transport.chat(
            payload={"model": "test"},
            timeout=10.0,
        )


def test_ollama_transport_maps_timeout():
    opener = FakeOpener(
        error=TimeoutError(
            "request timed out"
        )
    )

    transport = OllamaTransport(
        opener=opener
    )

    with pytest.raises(
        OllamaTimeoutError
    ):
        transport.chat(
            payload={"model": "test"},
            timeout=10.0,
        )


def test_ollama_transport_maps_http_error():
    opener = FakeOpener(
        error=HTTPError(
            url="http://127.0.0.1:11434/api/chat",
            code=404,
            msg="Not Found",
            hdrs=None,
            fp=None,
        )
    )

    transport = OllamaTransport(
        opener=opener
    )

    with pytest.raises(
        OllamaHTTPError
    ):
        transport.chat(
            payload={"model": "missing"},
            timeout=10.0,
        )


def test_ollama_transport_rejects_invalid_json():
    opener = FakeOpener(
        response=FakeResponse(
            b"not-json"
        )
    )

    transport = OllamaTransport(
        opener=opener
    )

    with pytest.raises(
        OllamaInvalidJSONError
    ):
        transport.chat(
            payload={"model": "test"},
            timeout=10.0,
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "",
        " ",
        "\n",
        "\t",
    ],
)
def test_ollama_transport_rejects_blank_base_url(
    base_url,
):
    with pytest.raises(ValueError):
        OllamaTransport(
            base_url=base_url,
        )


def test_ollama_transport_maps_timeout_wrapped_by_urlerror():
    opener = FakeOpener(
        error=URLError(
            TimeoutError(
                "request timed out"
            )
        )
    )

    transport = OllamaTransport(
        opener=opener
    )

    with pytest.raises(
        OllamaTimeoutError
    ):
        transport.chat(
            payload={"model": "test"},
            timeout=10.0,
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "https://127.0.0.1:11434",
        "http://example.com:11434",
        "http://192.168.1.10:11434",
        "http://10.0.0.25:11434",
        "ftp://127.0.0.1:11434",
        "http://user:password@127.0.0.1:11434",
        "http://127.0.0.1:11434/custom",
        "http://127.0.0.1:11434?token=value",
        "http://127.0.0.1:11434#fragment",
    ],
)
def test_ollama_transport_rejects_non_local_or_unsafe_base_url(
    base_url,
):
    with pytest.raises(ValueError):
        OllamaTransport(
            base_url=base_url,
        )


@pytest.mark.parametrize(
    "base_url",
    [
        "http://127.0.0.1:11434",
        "http://127.0.0.1:11434/",
        "http://localhost:11434",
        "http://[::1]:11434",
    ],
)
def test_ollama_transport_accepts_loopback_base_url(
    base_url,
):
    transport = OllamaTransport(
        base_url=base_url,
    )

    assert transport.base_url
