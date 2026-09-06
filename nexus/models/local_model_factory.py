from nexus.models.local_model import (
    LocalModelClient,
)
from nexus.models.ollama_transport import (
    OllamaTransport,
)


def build_local_model_client(
    settings,
    *,
    transport_factory=OllamaTransport,
) -> LocalModelClient:
    transport = transport_factory(
        base_url=settings.local_model_base_url,
    )

    return LocalModelClient(
        model=settings.local_model_name,
        transport=transport,
        timeout=settings.local_model_timeout,
    )
