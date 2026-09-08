from nexus.models.ollama_provider import OllamaProvider
from nexus.models.ollama_transport import OllamaTransport
from nexus.models.router import ModelRouter


def build_model_router(
    settings,
    *,
    transport_factory=OllamaTransport,
    provider_factory=OllamaProvider,
) -> ModelRouter:
    """
    Compõe a Model Layer provider-agnostic do Nexus Core.

    A construção é puramente estrutural: nenhum acesso ao
    backend ou inferência ocorre nesta etapa.
    """

    transport = transport_factory(
        base_url=settings.local_model_base_url,
    )

    provider = provider_factory(
        model=settings.local_model_name,
        transport=transport,
        timeout=settings.local_model_timeout,
    )

    return ModelRouter(
        providers=[provider],
        default_provider_id="ollama",
    )
