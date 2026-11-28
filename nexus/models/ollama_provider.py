import math
from time import monotonic, sleep
from collections.abc import Mapping

from nexus.models.contracts import (
    ModelProtocolError,
    ModelProviderError,
    ModelProviderTimeoutError,
    ModelProviderUnavailableError,
    ModelProviderResourceError,
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
    OllamaCancelledError,
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
        self._compact_expiry = 0.0

    @property
    def provider_id(self) -> str:
        return "ollama"

    def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        return self._generate(request)

    def generate_stream(self, request: ModelRequest, *, on_partial,
                        is_cancelled) -> ModelResponse:
        """Stream only plain conversational replies; caller decides eligibility."""
        if request.json_mode:
            raise ModelValidationError("Streaming não aceita propostas de ferramentas.")
        return self._generate(request, on_partial=on_partial, is_cancelled=is_cancelled)

    def _compact_keep_alive(self, budget, *, streaming, is_cancelled):
        size_query = getattr(self.transport, "model_size", None)
        if not callable(size_query):
            if budget.text_memory_low():
                raise ModelProviderResourceError("Memória livre insuficiente para iniciar o modelo local.")
            return "0s"
        try:
            size = size_query(self.model)
        except OllamaTransportError as exc:
            raise ModelProviderResourceError(
                "Não foi possível verificar o tamanho do modelo local."
            ) from exc
        if type(size) is not int or size <= 0:
            raise ModelProviderResourceError("Tamanho do modelo inválido.")
        size_mib = (size + 1024**2 - 1) // 1024**2
        required = max(1024, size_mib + 512)
        # The previous turn may still own its short lease. Recheck on the
        # worker, never discount resident weights or bypass the cold-load guard.
        deadline = min(self._compact_expiry, monotonic() + 5)
        while True:
            if is_cancelled and is_cancelled():
                raise ModelProviderError("Solicitação cancelada.")
            available = budget.available_now_mib()
            if available is not None and available >= required:
                return "4s" if streaming and available >= size_mib + 1536 else "0s"
            remaining = deadline - monotonic()
            if available is None or remaining <= 0:
                raise ModelProviderResourceError(
                    "O modelo local não cabe com segurança na memória disponível "
                    "para o perfil de 4 GB. Libere RAM ou configure um modelo menor."
                )
            sleep(min(0.1, remaining))

    def _generate(self, request: ModelRequest, *, on_partial=None,
                  is_cancelled=None) -> ModelResponse:
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
        if request.json_mode:
            payload["format"] = request.response_schema or "json"
        if request.max_output_tokens is not None:
            payload["options"]["num_predict"] = request.max_output_tokens
        budget = getattr(self, "resource_budget", None)
        if budget is not None:
            if budget.compact:
                payload["keep_alive"] = self._compact_keep_alive(
                    budget, streaming=on_partial is not None, is_cancelled=is_cancelled,
                )
            else:
                if budget.text_memory_low():
                    raise ModelProviderResourceError("Memória livre insuficiente para iniciar o modelo local.")
                payload["keep_alive"] = budget.text_keep_alive()
            # Bounded to avoid thermal load and simultaneous large models.
            payload["options"].update(budget.text_options(
                request.context_length, request.max_output_tokens,
            ))

        try:
            if on_partial is None:
                raw_response = self.transport.chat(
                    payload=payload, timeout=request.timeout_seconds or self.timeout,
                )
            else:
                raw_response = self.transport.chat_stream(
                    payload=payload, timeout=request.timeout_seconds or self.timeout,
                    on_partial=on_partial, is_cancelled=is_cancelled,
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

        except (OllamaCancelledError, OllamaTransportError) as exc:
            raise ModelProviderError(
                "falha no transporte do provider Ollama"
            ) from exc

        finally:
            if payload.get("keep_alive") == "4s":
                self._compact_expiry = monotonic() + 5

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
