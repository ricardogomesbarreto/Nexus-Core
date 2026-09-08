from typing import Protocol, runtime_checkable

from nexus.models.contracts import (
    ModelRequest,
    ModelResponse,
)


@runtime_checkable
class ModelProvider(Protocol):
    """
    Contrato estrutural provider-agnostic para
    providers de modelos do Nexus Core.
    """

    @property
    def provider_id(self) -> str:
        ...

    def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        ...
