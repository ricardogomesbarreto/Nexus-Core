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
    if type(provider) is OllamaProvider:
        # Keep custom/legacy provider factory signatures fully compatible.
        # The budget is a pure, local hardware query with no inference.
        from nexus.models.resource_budget import ResourceBudget
        provider.resource_budget = ResourceBudget.detect()

    return ModelRouter(
        providers=[provider],
        default_provider_id="ollama",
    )
