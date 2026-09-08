from nexus.models.contracts import (
    ModelError,
    ModelProtocolError,
    ModelRequest,
    ModelResponse,
    ModelValidationError,
)
from nexus.models.provider import ModelProvider


class ModelRoutingError(
    ModelError,
    RuntimeError,
):
    """
    Erro base da camada de roteamento de modelos.
    """


class InvalidModelProviderError(ModelRoutingError):
    """
    Objeto registrado não satisfaz o contrato ModelProvider.
    """


class InvalidModelProviderIdError(ModelRoutingError):
    """
    Identificador de provider possui tipo ou valor inválido.
    """


class UnknownModelProviderError(ModelRoutingError):
    """
    Provider solicitado não está registrado no router.
    """


class DuplicateModelProviderError(ModelRoutingError):
    """
    Dois providers tentaram registrar o mesmo provider_id.
    """


def _validate_provider_id(
    provider_id,
) -> str:
    if (
        not isinstance(provider_id, str)
        or not provider_id.strip()
    ):
        raise InvalidModelProviderIdError(
            "provider_id deve ser texto não vazio"
        )

    return provider_id


class ModelRouter:
    """
    Roteador determinístico de ModelProvider.

    Não realiza descoberta dinâmica, fallback automático,
    heurísticas ou seleção baseada em IA.
    """

    def __init__(
        self,
        *,
        providers: list[ModelProvider],
        default_provider_id: str,
    ) -> None:
        self._providers: dict[str, ModelProvider] = {}

        for provider in providers:
            if not isinstance(
                provider,
                ModelProvider,
            ):
                raise InvalidModelProviderError(
                    "provider não satisfaz ModelProvider"
                )

            provider_id = _validate_provider_id(
                provider.provider_id
            )

            if provider_id in self._providers:
                raise DuplicateModelProviderError(
                    "provider duplicado: "
                    f"{provider_id}"
                )

            self._providers[provider_id] = provider

        validated_default_provider_id = (
            _validate_provider_id(
                default_provider_id
            )
        )

        if (
            validated_default_provider_id
            not in self._providers
        ):
            raise UnknownModelProviderError(
                "provider padrão não registrado: "
                f"{validated_default_provider_id}"
            )

        self._default_provider_id = (
            validated_default_provider_id
        )

    @property
    def default_provider_id(self) -> str:
        return self._default_provider_id

    def resolve(
        self,
        provider_id: str,
    ) -> ModelProvider:
        validated_provider_id = (
            _validate_provider_id(provider_id)
        )

        try:
            return self._providers[
                validated_provider_id
            ]
        except KeyError as exc:
            raise UnknownModelProviderError(
                "provider não registrado: "
                f"{validated_provider_id}"
            ) from exc

    def generate(
        self,
        request: ModelRequest,
        *,
        provider_id: str | None = None,
    ) -> ModelResponse:
        if not isinstance(
            request,
            ModelRequest,
        ):
            raise ModelValidationError(
                "request deve ser ModelRequest"
            )

        selected_provider_id = (
            self._default_provider_id
            if provider_id is None
            else provider_id
        )

        provider = self.resolve(
            selected_provider_id
        )

        response = provider.generate(request)

        if not isinstance(
            response,
            ModelResponse,
        ):
            raise ModelProtocolError(
                "provider retornou objeto diferente "
                "de ModelResponse"
            )

        return response
