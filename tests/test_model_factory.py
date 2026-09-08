from types import SimpleNamespace

from nexus.models.contracts import (
    ModelRequest,
    ModelResponse,
)
from nexus.models.model_factory import (
    build_model_router,
)
from nexus.models.router import ModelRouter


class FakeTransport:
    def __init__(self, *, base_url):
        self.base_url = base_url


class FakeProvider:
    def __init__(
        self,
        *,
        model,
        transport,
        timeout,
    ):
        self.model = model
        self.transport = transport
        self.timeout = timeout
        self.requests = []

    @property
    def provider_id(self):
        return "ollama"

    def generate(self, request):
        self.requests.append(request)

        return ModelResponse(
            content="NEXUS_FACTORY_OK",
            model=self.model,
            done=True,
            prompt_tokens=1,
            output_tokens=1,
        )


def make_settings():
    return SimpleNamespace(
        local_model_name="qwen3:1.7b",
        local_model_base_url="http://127.0.0.1:11434",
        local_model_timeout=45.0,
    )


def test_build_model_router_returns_model_router():
    router = build_model_router(
        make_settings(),
        transport_factory=FakeTransport,
        provider_factory=FakeProvider,
    )

    assert isinstance(router, ModelRouter)


def test_build_model_router_composes_ollama_provider():
    router = build_model_router(
        make_settings(),
        transport_factory=FakeTransport,
        provider_factory=FakeProvider,
    )

    provider = router.resolve("ollama")

    assert isinstance(provider, FakeProvider)
    assert provider.model == "qwen3:1.7b"
    assert provider.timeout == 45.0
    assert isinstance(
        provider.transport,
        FakeTransport,
    )
    assert (
        provider.transport.base_url
        == "http://127.0.0.1:11434"
    )


def test_build_model_router_sets_ollama_as_default():
    router = build_model_router(
        make_settings(),
        transport_factory=FakeTransport,
        provider_factory=FakeProvider,
    )

    assert router.default_provider_id == "ollama"


def test_build_model_router_does_not_generate_during_build():
    router = build_model_router(
        make_settings(),
        transport_factory=FakeTransport,
        provider_factory=FakeProvider,
    )

    provider = router.resolve("ollama")

    assert provider.requests == []


def test_built_router_can_generate_through_default_provider():
    router = build_model_router(
        make_settings(),
        transport_factory=FakeTransport,
        provider_factory=FakeProvider,
    )

    request = ModelRequest(
        prompt="NEXUS_FACTORY_TEST"
    )

    response = router.generate(request)

    assert response.content == "NEXUS_FACTORY_OK"

    provider = router.resolve("ollama")
    assert provider.requests == [request]
