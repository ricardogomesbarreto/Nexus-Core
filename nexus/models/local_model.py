from nexus.models.contracts import (
    ModelError,
    ModelProtocolError,
    ModelRequest,
    ModelResponse,
    ModelValidationError,
)
from nexus.models.ollama_provider import OllamaProvider
from nexus.models.ollama_transport import (
    OllamaTransportError,
)


# Compatibility aliases preserved from Nexus Core v0.3.0.
LocalModelValidationError = ModelValidationError
LocalModelProtocolError = ModelProtocolError
LocalModelRequest = ModelRequest
LocalModelResponse = ModelResponse


class LocalModelClient:
    """
    Compatibility facade preserved from Nexus Core v0.3.0.

    New code should use the provider abstraction introduced
    in v0.3.1. Ollama-specific behavior is implemented only
    by OllamaProvider.
    """

    def __init__(
        self,
        *,
        model: str,
        transport,
        timeout: float = 120.0,
    ) -> None:
        self._provider = OllamaProvider(
            model=model,
            transport=transport,
            timeout=timeout,
        )

        # Preserve the observable v0.3.0 client attributes.
        self.model = model
        self.transport = transport
        self.timeout = timeout

    def generate(
        self,
        request: LocalModelRequest,
    ) -> LocalModelResponse:
        try:
            return self._provider.generate(request)

        except ModelError as exc:
            cause = exc.__cause__

            if isinstance(
                cause,
                OllamaTransportError,
            ):
                raise cause from None

            raise
