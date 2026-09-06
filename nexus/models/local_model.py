import math
from collections.abc import Mapping
from dataclasses import dataclass


class LocalModelValidationError(ValueError):
    """
    Erro de validação do contrato da camada de modelo local.
    """


class LocalModelProtocolError(RuntimeError):
    """
    Resposta do backend incompatível com o protocolo esperado.
    """


def _validate_non_blank_text(
    field_name: str,
    value: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise LocalModelValidationError(
            f"{field_name} deve ser texto não vazio"
        )


def _validate_boolean(
    field_name: str,
    value: bool,
) -> None:
    if type(value) is not bool:
        raise LocalModelValidationError(
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
        raise LocalModelValidationError(
            f"{field_name} deve ser um número finito "
            "maior ou igual a zero"
        )


def _validate_positive_number(
    field_name: str,
    value: float,
) -> None:
    if (
        isinstance(value, bool)
        or not isinstance(value, (int, float))
        or not math.isfinite(value)
        or value <= 0
    ):
        raise LocalModelValidationError(
            f"{field_name} deve ser um número finito "
            "maior que zero"
        )


def _validate_positive_integer(
    field_name: str,
    value: int,
) -> None:
    if (
        type(value) is not int
        or value < 1
    ):
        raise LocalModelValidationError(
            f"{field_name} deve ser um inteiro maior "
            "ou igual a 1"
        )


def _validate_non_negative_integer(
    field_name: str,
    value: int,
) -> None:
    if (
        type(value) is not int
        or value < 0
    ):
        raise LocalModelValidationError(
            f"{field_name} deve ser um inteiro maior "
            "ou igual a zero"
        )


@dataclass(frozen=True)
class LocalModelRequest:
    """
    Requisição imutável para um modelo local.
    """

    prompt: str
    system_prompt: str | None = None
    temperature: float = 0.0
    context_length: int = 2048
    think: bool = False

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


@dataclass(frozen=True)
class LocalModelResponse:
    """
    Resposta imutável produzida por um modelo local.
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


class LocalModelClient:
    """
    Orquestra requisições para um modelo local através
    de um transporte injetado.
    """

    def __init__(
        self,
        *,
        model: str,
        transport,
        timeout: float = 120.0,
    ) -> None:
        _validate_non_blank_text(
            "model",
            model,
        )

        _validate_positive_number(
            "timeout",
            timeout,
        )

        self.model = model
        self.transport = transport
        self.timeout = timeout

    def generate(
        self,
        request: LocalModelRequest,
    ) -> LocalModelResponse:
        if not isinstance(request, LocalModelRequest):
            raise LocalModelValidationError(
                "request deve ser LocalModelRequest"
            )

        messages = []

        if request.system_prompt is not None:
            messages.append(
                {
                    "role": "system",
                    "content": request.system_prompt,
                }
            )

        messages.append(
            {
                "role": "user",
                "content": request.prompt,
            }
        )

        payload = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "think": request.think,
            "options": {
                "num_ctx": request.context_length,
                "temperature": request.temperature,
            },
        }

        raw_response = self.transport.chat(
            payload=payload,
            timeout=self.timeout,
        )

        return self._parse_response(
            raw_response
        )

    @staticmethod
    def _parse_response(
        raw_response,
    ) -> LocalModelResponse:
        if not isinstance(raw_response, Mapping):
            raise LocalModelProtocolError(
                "backend retornou uma resposta inválida"
            )

        try:
            message = raw_response["message"]

            if not isinstance(message, Mapping):
                raise LocalModelProtocolError(
                    "backend retornou message inválido"
                )

            response = LocalModelResponse(
                content=message["content"],
                model=raw_response["model"],
                done=raw_response["done"],
                prompt_tokens=(
                    raw_response["prompt_eval_count"]
                ),
                output_tokens=(
                    raw_response["eval_count"]
                ),
            )

            if response.done is not True:
                raise LocalModelProtocolError(
                    "backend retornou resposta incompleta "
                    "para requisição não-streaming"
                )
        except LocalModelProtocolError:
            raise
        except (
            KeyError,
            TypeError,
            LocalModelValidationError,
        ) as exc:
            raise LocalModelProtocolError(
                "backend retornou uma resposta "
                "incompatível com o protocolo esperado"
            ) from exc

        return response
