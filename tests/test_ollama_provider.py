import pytest

from nexus.models.contracts import (
    ModelProtocolError,
    ModelRequest,
    ModelResponse,
    ModelValidationError,
)
from nexus.models.ollama_provider import OllamaProvider
from nexus.models.provider import ModelProvider


class FakeTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(self, *, payload, timeout):
        self.calls.append(
            {
                "payload": payload,
                "timeout": timeout,
            }
        )
        return self.response


def make_response():
    return {
        "message": {
            "content": "NEXUS_OLLAMA_OK",
        },
        "model": "qwen3:1.7b",
        "done": True,
        "prompt_eval_count": 10,
        "eval_count": 3,
    }


def test_ollama_provider_satisfies_model_provider_contract():
    provider = OllamaProvider(
        model="qwen3:1.7b",
        transport=FakeTransport(make_response()),
    )

    assert isinstance(provider, ModelProvider)
    assert provider.provider_id == "ollama"


def test_ollama_provider_generates_generic_model_response():
    transport = FakeTransport(make_response())

    provider = OllamaProvider(
        model="qwen3:1.7b",
        transport=transport,
        timeout=45.0,
    )

    response = provider.generate(
        ModelRequest(
            prompt="NEXUS_TEST",
        )
    )

    assert response == ModelResponse(
        content="NEXUS_OLLAMA_OK",
        model="qwen3:1.7b",
        done=True,
        prompt_tokens=10,
        output_tokens=3,
    )

    assert transport.calls == [
        {
            "payload": {
                "model": "qwen3:1.7b",
                "messages": [
                    {
                        "role": "user",
                        "content": "NEXUS_TEST",
                    }
                ],
                "stream": False,
                "think": False,
                "options": {
                    "num_ctx": 2048,
                    "temperature": 0.0,
                },
            },
            "timeout": 45.0,
        }
    ]


def test_ollama_provider_preserves_system_prompt_order():
    transport = FakeTransport(make_response())

    provider = OllamaProvider(
        model="qwen3:1.7b",
        transport=transport,
    )

    provider.generate(
        ModelRequest(
            prompt="Pergunta",
            system_prompt="Sistema",
            temperature=0.2,
            context_length=4096,
            think=True,
        )
    )

    payload = transport.calls[0]["payload"]

    assert payload["messages"] == [
        {
            "role": "system",
            "content": "Sistema",
        },
        {
            "role": "user",
            "content": "Pergunta",
        },
    ]

    assert payload["think"] is True
    assert payload["options"] == {
        "num_ctx": 4096,
        "temperature": 0.2,
    }


@pytest.mark.parametrize(
    "model",
    [
        "",
        " ",
        "\n",
        None,
        123,
    ],
)
def test_ollama_provider_rejects_invalid_model(model):
    with pytest.raises(ModelValidationError):
        OllamaProvider(
            model=model,
            transport=FakeTransport(make_response()),
        )


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        float("nan"),
        float("inf"),
        True,
        "120",
        None,
    ],
)
def test_ollama_provider_rejects_invalid_timeout(timeout):
    with pytest.raises(ModelValidationError):
        OllamaProvider(
            model="qwen3:1.7b",
            transport=FakeTransport(make_response()),
            timeout=timeout,
        )


def test_ollama_provider_rejects_invalid_request_type():
    provider = OllamaProvider(
        model="qwen3:1.7b",
        transport=FakeTransport(make_response()),
    )

    with pytest.raises(ModelValidationError):
        provider.generate("not-a-model-request")


@pytest.mark.parametrize(
    "response",
    [
        None,
        [],
        {},
        {"message": "invalid"},
        {
            "message": {"content": "OK"},
            "model": "qwen3:1.7b",
            "done": True,
        },
    ],
)
def test_ollama_provider_rejects_malformed_response(
    response,
):
    provider = OllamaProvider(
        model="qwen3:1.7b",
        transport=FakeTransport(response),
    )

    with pytest.raises(ModelProtocolError):
        provider.generate(
            ModelRequest(prompt="Teste")
        )


def test_ollama_provider_rejects_incomplete_response():
    response = make_response()
    response["done"] = False

    provider = OllamaProvider(
        model="qwen3:1.7b",
        transport=FakeTransport(response),
    )

    with pytest.raises(ModelProtocolError):
        provider.generate(
            ModelRequest(prompt="Teste")
        )
