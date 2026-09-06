import math

import pytest

from nexus.models.local_model import (
    LocalModelClient,
    LocalModelProtocolError,
    LocalModelRequest,
    LocalModelResponse,
    LocalModelValidationError,
)


class FakeLocalModelTransport:
    def __init__(self, response):
        self.response = response
        self.calls = []

    def chat(
        self,
        *,
        payload,
        timeout,
    ):
        self.calls.append(
            {
                "payload": payload,
                "timeout": timeout,
            }
        )

        return self.response


def test_local_model_client_generates_typed_response():
    transport = FakeLocalModelTransport(
        {
            "model": "qwen3:1.7b",
            "done": True,
            "message": {
                "content": "NEXUS_OK",
            },
            "prompt_eval_count": 12,
            "eval_count": 3,
        }
    )

    client = LocalModelClient(
        model="qwen3:1.7b",
        transport=transport,
        timeout=120.0,
    )

    request = LocalModelRequest(
        prompt="Responda NEXUS_OK."
    )

    response = client.generate(request)

    assert response == LocalModelResponse(
        content="NEXUS_OK",
        model="qwen3:1.7b",
        done=True,
        prompt_tokens=12,
        output_tokens=3,
    )

    assert transport.calls == [
        {
            "payload": {
                "model": "qwen3:1.7b",
                "messages": [
                    {
                        "role": "user",
                        "content": "Responda NEXUS_OK.",
                    }
                ],
                "stream": False,
                "think": False,
                "options": {
                    "num_ctx": 2048,
                    "temperature": 0.0,
                },
            },
            "timeout": 120.0,
        }
    ]


def test_local_model_client_places_system_prompt_before_user_prompt():
    transport = FakeLocalModelTransport(
        {
            "model": "qwen3:1.7b",
            "done": True,
            "message": {
                "content": "Resposta",
            },
            "prompt_eval_count": 20,
            "eval_count": 4,
        }
    )

    client = LocalModelClient(
        model="qwen3:1.7b",
        transport=transport,
        timeout=30.0,
    )

    request = LocalModelRequest(
        prompt="Pergunta",
        system_prompt="Você é o Nexus.",
        temperature=0.25,
        context_length=1024,
        think=True,
    )

    client.generate(request)

    call = transport.calls[0]

    assert call["timeout"] == 30.0

    assert call["payload"] == {
        "model": "qwen3:1.7b",
        "messages": [
            {
                "role": "system",
                "content": "Você é o Nexus.",
            },
            {
                "role": "user",
                "content": "Pergunta",
            },
        ],
        "stream": False,
        "think": True,
        "options": {
            "num_ctx": 1024,
            "temperature": 0.25,
        },
    }


@pytest.mark.parametrize(
    "model",
    [
        "",
        " ",
        "\n",
        "\t",
    ],
)
def test_local_model_client_rejects_blank_model(
    model,
):
    transport = FakeLocalModelTransport({})

    with pytest.raises(LocalModelValidationError):
        LocalModelClient(
            model=model,
            transport=transport,
        )


@pytest.mark.parametrize(
    "timeout",
    [
        0,
        -1,
        -0.1,
        math.nan,
        math.inf,
        -math.inf,
    ],
)
def test_local_model_client_rejects_invalid_timeout(
    timeout,
):
    transport = FakeLocalModelTransport({})

    with pytest.raises(LocalModelValidationError):
        LocalModelClient(
            model="qwen3:1.7b",
            transport=transport,
            timeout=timeout,
        )


@pytest.mark.parametrize(
    "raw_response",
    [
        None,
        [],
        {},
        {
            "model": "qwen3:1.7b",
        },
        {
            "model": "qwen3:1.7b",
            "done": True,
            "message": {},
            "prompt_eval_count": 10,
            "eval_count": 2,
        },
        {
            "model": "qwen3:1.7b",
            "done": True,
            "message": {
                "content": "NEXUS_OK",
            },
            "prompt_eval_count": 10,
        },
    ],
)
def test_local_model_client_rejects_malformed_backend_response(
    raw_response,
):
    transport = FakeLocalModelTransport(
        raw_response
    )

    client = LocalModelClient(
        model="qwen3:1.7b",
        transport=transport,
    )

    request = LocalModelRequest(
        prompt="Teste"
    )

    with pytest.raises(LocalModelProtocolError):
        client.generate(request)


@pytest.mark.parametrize(
    "invalid_request",
    [
        None,
        "prompt",
        {},
        object(),
    ],
)
def test_local_model_client_rejects_invalid_request_type(
    invalid_request,
):
    transport = FakeLocalModelTransport({})

    client = LocalModelClient(
        model="qwen3:1.7b",
        transport=transport,
    )

    with pytest.raises(LocalModelValidationError):
        client.generate(invalid_request)

    assert transport.calls == []


def test_local_model_client_rejects_incomplete_non_stream_response():
    transport = FakeLocalModelTransport(
        {
            "model": "qwen3:1.7b",
            "done": False,
            "message": {
                "content": "Resposta parcial",
            },
            "prompt_eval_count": 10,
            "eval_count": 2,
        }
    )

    client = LocalModelClient(
        model="qwen3:1.7b",
        transport=transport,
    )

    request = LocalModelRequest(
        prompt="Teste"
    )

    with pytest.raises(LocalModelProtocolError):
        client.generate(request)
