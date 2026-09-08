from dataclasses import FrozenInstanceError

import pytest

from nexus.models.contracts import (
    ModelProtocolError,
    ModelRequest,
    ModelResponse,
    ModelValidationError,
)


def test_model_error_hierarchy_is_explicit():
    assert issubclass(ModelValidationError, ValueError)
    assert issubclass(ModelProtocolError, RuntimeError)


def test_model_request_has_safe_defaults_and_is_immutable():
    request = ModelRequest(
        prompt="Explique o Nexus Core."
    )

    assert request.prompt == "Explique o Nexus Core."
    assert request.system_prompt is None
    assert request.temperature == 0.0
    assert request.context_length == 2048
    assert request.think is False

    with pytest.raises(FrozenInstanceError):
        request.prompt = "alterado"


def test_model_request_preserves_prompt_content():
    request = ModelRequest(
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
        None,
        123,
        True,
        {},
    ],
)
def test_model_request_rejects_invalid_prompt(prompt):
    with pytest.raises(ModelValidationError):
        ModelRequest(prompt=prompt)


@pytest.mark.parametrize(
    "system_prompt",
    [
        "",
        " ",
        "\n",
        "\t",
        123,
        True,
    ],
)
def test_model_request_rejects_invalid_system_prompt(
    system_prompt,
):
    with pytest.raises(ModelValidationError):
        ModelRequest(
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
        True,
        False,
        "0.5",
        None,
    ],
)
def test_model_request_rejects_invalid_temperature(
    temperature,
):
    with pytest.raises(ModelValidationError):
        ModelRequest(
            prompt="Teste",
            temperature=temperature,
        )


@pytest.mark.parametrize(
    "context_length",
    [
        0,
        -1,
        True,
        False,
        2048.0,
        "2048",
        None,
    ],
)
def test_model_request_rejects_invalid_context_length(
    context_length,
):
    with pytest.raises(ModelValidationError):
        ModelRequest(
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
def test_model_request_rejects_non_boolean_think(think):
    with pytest.raises(ModelValidationError):
        ModelRequest(
            prompt="Teste",
            think=think,
        )


def test_model_response_is_typed_and_immutable():
    response = ModelResponse(
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
    ("field", "value"),
    [
        ("content", ""),
        ("content", " "),
        ("content", None),
        ("model", ""),
        ("model", " "),
        ("model", None),
        ("done", 1),
        ("done", "true"),
        ("prompt_tokens", -1),
        ("prompt_tokens", True),
        ("prompt_tokens", 1.0),
        ("output_tokens", -1),
        ("output_tokens", False),
        ("output_tokens", "1"),
    ],
)
def test_model_response_rejects_invalid_fields(
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

    with pytest.raises(ModelValidationError):
        ModelResponse(**values)
