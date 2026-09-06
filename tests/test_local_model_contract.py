from dataclasses import FrozenInstanceError

import pytest

from nexus.models.local_model import (
    LocalModelRequest,
    LocalModelResponse,
    LocalModelValidationError,
)


def test_local_model_request_has_safe_defaults():
    request = LocalModelRequest(
        prompt="Explique o Nexus Core."
    )

    assert request.prompt == "Explique o Nexus Core."
    assert request.system_prompt is None
    assert request.temperature == 0.0
    assert request.context_length == 2048
    assert request.think is False


def test_local_model_request_preserves_prompt_content():
    request = LocalModelRequest(
        prompt="  texto com espaços intencionais  "
    )

    assert (
        request.prompt
        == "  texto com espaços intencionais  "
    )


@pytest.mark.parametrize(
    "prompt",
    [
        "",
        " ",
        "\n",
        "\t",
        " \n\t ",
    ],
)
def test_local_model_request_rejects_blank_prompt(
    prompt,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(prompt=prompt)


def test_local_model_request_is_immutable():
    request = LocalModelRequest(
        prompt="Teste"
    )

    with pytest.raises(FrozenInstanceError):
        request.prompt = "alterado"


def test_local_model_response_is_typed_and_immutable():
    response = LocalModelResponse(
        content="NEXUS_OK",
        model="qwen3:1.7b",
        done=True,
        prompt_tokens=12,
        output_tokens=3,
    )

    assert response.content == "NEXUS_OK"
    assert response.model == "qwen3:1.7b"
    assert response.done is True
    assert response.prompt_tokens == 12
    assert response.output_tokens == 3

    with pytest.raises(FrozenInstanceError):
        response.content = "alterado"


@pytest.mark.parametrize(
    "system_prompt",
    [
        "",
        " ",
        "\n",
        "\t",
    ],
)
def test_local_model_request_rejects_blank_system_prompt(
    system_prompt,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(
            prompt="Teste",
            system_prompt=system_prompt,
        )


@pytest.mark.parametrize(
    "temperature",
    [
        -0.1,
        float("nan"),
        float("inf"),
        float("-inf"),
    ],
)
def test_local_model_request_rejects_invalid_temperature(
    temperature,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(
            prompt="Teste",
            temperature=temperature,
        )


@pytest.mark.parametrize(
    "context_length",
    [
        0,
        -1,
        -2048,
    ],
)
def test_local_model_request_rejects_invalid_context_length(
    context_length,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(
            prompt="Teste",
            context_length=context_length,
        )


@pytest.mark.parametrize(
    "think",
    [
        0,
        1,
        "false",
        None,
    ],
)
def test_local_model_request_rejects_non_boolean_think(
    think,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(
            prompt="Teste",
            think=think,
        )


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("content", ""),
        ("content", " "),
        ("model", ""),
        ("model", " "),
    ],
)
def test_local_model_response_rejects_blank_text_fields(
    field,
    value,
):
    values = {
        "content": "NEXUS_OK",
        "model": "qwen3:1.7b",
        "done": True,
        "prompt_tokens": 10,
        "output_tokens": 2,
    }

    values[field] = value

    with pytest.raises(LocalModelValidationError):
        LocalModelResponse(**values)


@pytest.mark.parametrize(
    "done",
    [
        0,
        1,
        "true",
        None,
    ],
)
def test_local_model_response_rejects_non_boolean_done(
    done,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelResponse(
            content="NEXUS_OK",
            model="qwen3:1.7b",
            done=done,
            prompt_tokens=10,
            output_tokens=2,
        )


@pytest.mark.parametrize(
    ("prompt_tokens", "output_tokens"),
    [
        (-1, 0),
        (0, -1),
        (-10, -20),
    ],
)
def test_local_model_response_rejects_negative_token_counts(
    prompt_tokens,
    output_tokens,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelResponse(
            content="NEXUS_OK",
            model="qwen3:1.7b",
            done=True,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
        )


@pytest.mark.parametrize(
    "prompt",
    [
        None,
        123,
        True,
        {},
    ],
)
def test_local_model_request_rejects_non_string_prompt(
    prompt,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(prompt=prompt)


@pytest.mark.parametrize(
    "temperature",
    [
        True,
        False,
        "0.5",
        None,
    ],
)
def test_local_model_request_rejects_invalid_temperature_type(
    temperature,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(
            prompt="Teste",
            temperature=temperature,
        )


@pytest.mark.parametrize(
    "context_length",
    [
        True,
        False,
        2048.0,
        "2048",
        None,
    ],
)
def test_local_model_request_rejects_non_integer_context_length(
    context_length,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelRequest(
            prompt="Teste",
            context_length=context_length,
        )


@pytest.mark.parametrize(
    ("prompt_tokens", "output_tokens"),
    [
        (True, 0),
        (0, False),
        (1.0, 0),
        (0, 1.0),
        ("1", 0),
        (0, "1"),
    ],
)
def test_local_model_response_rejects_invalid_token_count_types(
    prompt_tokens,
    output_tokens,
):
    with pytest.raises(LocalModelValidationError):
        LocalModelResponse(
            content="NEXUS_OK",
            model="qwen3:1.7b",
            done=True,
            prompt_tokens=prompt_tokens,
            output_tokens=output_tokens,
        )
