from nexus.models.contracts import (
    ModelRequest,
    ModelResponse,
)
from nexus.models.provider import ModelProvider


class FakeProvider:
    @property
    def provider_id(self) -> str:
        return "fake"

    def generate(
        self,
        request: ModelRequest,
    ) -> ModelResponse:
        return ModelResponse(
            content=f"response:{request.prompt}",
            model="fake-model",
            done=True,
            prompt_tokens=1,
            output_tokens=1,
        )


def test_model_provider_is_structural_runtime_contract():
    provider = FakeProvider()

    assert isinstance(provider, ModelProvider)


def test_model_provider_exposes_stable_provider_id():
    provider: ModelProvider = FakeProvider()

    assert provider.provider_id == "fake"


def test_model_provider_generate_uses_generic_contract():
    provider: ModelProvider = FakeProvider()

    request = ModelRequest(
        prompt="NEXUS_PROVIDER_TEST"
    )

    response = provider.generate(request)

    assert isinstance(response, ModelResponse)
    assert response.content == (
        "response:NEXUS_PROVIDER_TEST"
    )
    assert response.model == "fake-model"
    assert response.done is True
