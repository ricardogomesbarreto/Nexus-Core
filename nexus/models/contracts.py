import math
from dataclasses import dataclass
from typing import Any


class ModelError(Exception):
    """
    Erro base da Model Layer do Nexus Core.
    """


class ModelValidationError(
    ModelError,
    ValueError,
):
    """
    Erro de validação do contrato genérico de modelo.
    """


class ModelProtocolError(
    ModelError,
    RuntimeError,
):
    """
    Resposta de provider incompatível com o protocolo
    esperado pelo Nexus Core.
    """


class ModelProviderError(
    ModelError,
    RuntimeError,
):
    """
    Erro genérico durante operação de um ModelProvider.
    """


class ModelProviderUnavailableError(
    ModelProviderError,
):
    """
    Provider configurado não está disponível.
    """


class ModelProviderTimeoutError(
    ModelProviderError,
):
    """
    Operação do provider excedeu o timeout permitido.
    """


class ModelProviderResourceError(ModelProviderError):
    """Local memory pressure makes loading the model unsafe."""


def _validate_non_blank_text(
    field_name: str,
    value: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ModelValidationError(
            f"{field_name} deve ser texto não vazio"
        )


def _validate_boolean(
    field_name: str,
    value: bool,
) -> None:
    if type(value) is not bool:
        raise ModelValidationError(
            f"{field_name} deve ser booleano"
        )


def _validate_non_negative_number(
    field_name: str,
    value: float,
) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value < 0
    ):
        raise ModelValidationError(
            f"{field_name} deve ser um número finito "
            "maior ou igual a zero"
        )


def _validate_positive_integer(
    field_name: str,
    value: int,
) -> None:
    if type(value) is not int or value < 1:
        raise ModelValidationError(
            f"{field_name} deve ser um inteiro maior "
            "ou igual a 1"
        )


def _validate_non_negative_integer(
    field_name: str,
    value: int,
) -> None:
    if type(value) is not int or value < 0:
        raise ModelValidationError(
            f"{field_name} deve ser um inteiro maior "
            "ou igual a zero"
        )


@dataclass(frozen=True)
class ModelRequest:
    """
    Requisição imutável e provider-agnostic para um modelo.
    """

    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.0
    context_length: int = 2048
    think: bool = False
    json_mode: bool = False
    response_schema: dict[str, Any] | None = None
    max_output_tokens: int | None = None
    timeout_seconds: float | None = None

    def __post_init__(self) -> None:
        _validate_non_blank_text(
            "prompt",
            self.prompt,
        )

        if self.system_prompt is not None:
            _validate_non_blank_text(
                "system_prompt",
                self.system_prompt,
            )

        _validate_non_negative_number(
            "temperature",
            self.temperature,
        )

        _validate_positive_integer(
            "context_length",
            self.context_length,
        )

        _validate_boolean(
            "think",
            self.think,
        )
        _validate_boolean(
            "json_mode",
            self.json_mode,
        )
        if self.response_schema is not None:
            if not self.json_mode or type(self.response_schema) is not dict:
                raise ModelValidationError("response_schema requer json_mode e um objeto")
        if self.max_output_tokens is not None:
            _validate_positive_integer("max_output_tokens", self.max_output_tokens)
        if self.timeout_seconds is not None:
            if (isinstance(self.timeout_seconds, bool) or
                    not isinstance(self.timeout_seconds, (int, float)) or
                    not math.isfinite(self.timeout_seconds) or self.timeout_seconds <= 0):
                raise ModelValidationError("timeout_seconds deve ser positivo e finito")


@dataclass(frozen=True)
class ModelResponse:
    """
    Resposta imutável e provider-agnostic produzida
    por um modelo.
    """

    content: str
    model: str
    done: bool
    prompt_tokens: int
    output_tokens: int

    def __post_init__(self) -> None:
        _validate_non_blank_text(
            "content",
            self.content,
        )

        _validate_non_blank_text(
            "model",
            self.model,
        )

        _validate_boolean(
            "done",
            self.done,
        )

        _validate_non_negative_integer(
            "prompt_tokens",
            self.prompt_tokens,
        )

        _validate_non_negative_integer(
            "output_tokens",
            self.output_tokens,
        )
