import math
from collections.abc import Mapping

from nexus.models.contracts import (
    ModelProtocolError,
    ModelProviderError,
    ModelProviderTimeoutError,
    ModelProviderUnavailableError,
    ModelRequest,
    ModelResponse,
    ModelValidationError,
)
from nexus.models.ollama_transport import (
    OllamaHTTPError,
    OllamaInvalidJSONError,
    OllamaTimeoutError,
    OllamaTransportError,
    OllamaUnavailableError,
)


def _validate_non_blank_text(
    field_name: str,
    value: str,
) -> None:
    if not isinstance(value, str) or not value.strip():
        raise ModelValidationError(
            f"{field_name} deve ser texto não vazio"
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
        raise ModelValidationError(
            f"{field_name} deve ser um número finito "
            "maior que zero"
        )


class OllamaProvider:
    """
    Provider de modelos do Nexus Core para o runtime
    local Ollama.

    Traduz o contrato genérico do Nexus para o protocolo
    Ollama e converte a resposta do backend para
    ModelResponse.
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

    @property
    def provider_id(self) -> str:
        return "ollama"

    def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        if not isinstance(request, ModelRequest):
            raise ModelValidationError(
                "request deve ser ModelRequest"
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

        try:
            raw_response = self.transport.chat(
                payload=payload,
                timeout=self.timeout,
            )

        except OllamaUnavailableError as exc:
            raise ModelProviderUnavailableError(
                "provider Ollama indisponível"
            ) from exc

        except OllamaTimeoutError as exc:
            raise ModelProviderTimeoutError(
                "provider Ollama excedeu o timeout"
            ) from exc

        except OllamaInvalidJSONError as exc:
            raise ModelProtocolError(
                "provider Ollama retornou protocolo inválido"
            ) from exc

        except OllamaHTTPError as exc:
            raise ModelProviderError(
                "provider Ollama retornou erro HTTP"
            ) from exc

        except OllamaTransportError as exc:
            raise ModelProviderError(
                "falha no transporte do provider Ollama"
            ) from exc

        return self._parse_response(
            raw_response
        )

    @staticmethod
    def _parse_response(
        raw_response,
    ) -> ModelResponse:
        if not isinstance(raw_response, Mapping):
            raise ModelProtocolError(
                "provider retornou uma resposta inválida"
            )

        try:
            message = raw_response["message"]

            if not isinstance(message, Mapping):
                raise ModelProtocolError(
                    "provider retornou message inválido"
                )

            response = ModelResponse(
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
                raise ModelProtocolError(
                    "provider retornou resposta incompleta "
                    "para requisição não-streaming"
                )

        except ModelProtocolError:
            raise

        except (
            KeyError,
            TypeError,
            ModelValidationError,
        ) as exc:
            raise ModelProtocolError(
                "provider retornou uma resposta "
                "incompatível com o protocolo esperado"
            ) from exc

        return response
