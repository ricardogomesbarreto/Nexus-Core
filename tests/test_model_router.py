import pytest

from nexus.models.contracts import (
    ModelRequest,
    ModelResponse,
)
from nexus.models.router import (
    DuplicateModelProviderError,
    ModelRouter,
    UnknownModelProviderError,
)


class FakeProvider:
    def __init__(
        self,
        provider_id,
        response_content,
    ):
        self._provider_id = provider_id
        self.response_content = response_content
        self.requests = []

    @property
    def provider_id(self):
        return self._provider_id

    def generate(self, request):
        self.requests.append(request)

        return ModelResponse(
            content=self.response_content,
            model=f"{self.provider_id}-model",
            done=True,
            prompt_tokens=1,
            output_tokens=1,
        )


class FailingProvider:
    @property
    def provider_id(self):
        return "failing"

    def generate(self, request):
        raise RuntimeError("provider failure")


def test_model_router_uses_default_provider():
    local = FakeProvider(
        "ollama",
        "LOCAL_RESPONSE",
    )

    alternate = FakeProvider(
        "alternate",
        "ALTERNATE_RESPONSE",
    )

    router = ModelRouter(
        providers=[
            local,
            alternate,
        ],
        default_provider_id="ollama",
    )

    request = ModelRequest(
        prompt="NEXUS_ROUTER_DEFAULT"
    )

    response = router.generate(request)

    assert response.content == "LOCAL_RESPONSE"
    assert local.requests == [request]
    assert alternate.requests == []


def test_model_router_supports_explicit_provider_selection():
    local = FakeProvider(
        "ollama",
        "LOCAL_RESPONSE",
    )

    alternate = FakeProvider(
        "alternate",
        "ALTERNATE_RESPONSE",
    )

    router = ModelRouter(
        providers=[
            local,
            alternate,
        ],
        default_provider_id="ollama",
    )

    request = ModelRequest(
        prompt="NEXUS_ROUTER_EXPLICIT"
    )

    response = router.generate(
        request,
        provider_id="alternate",
    )

    assert response.content == "ALTERNATE_RESPONSE"
    assert local.requests == []
    assert alternate.requests == [request]


def test_model_router_resolves_provider_by_id():
    local = FakeProvider(
        "ollama",
        "LOCAL_RESPONSE",
    )

    router = ModelRouter(
        providers=[local],
        default_provider_id="ollama",
    )

    assert router.resolve("ollama") is local


def test_model_router_rejects_unknown_explicit_provider():
    router = ModelRouter(
        providers=[
            FakeProvider(
                "ollama",
                "LOCAL_RESPONSE",
            )
        ],
        default_provider_id="ollama",
    )

    with pytest.raises(
        UnknownModelProviderError
    ):
        router.generate(
            ModelRequest(prompt="Teste"),
            provider_id="missing",
        )


def test_model_router_rejects_unknown_default_provider():
    with pytest.raises(
        UnknownModelProviderError
    ):
        ModelRouter(
            providers=[
                FakeProvider(
                    "ollama",
                    "LOCAL_RESPONSE",
                )
            ],
            default_provider_id="missing",
        )


def test_model_router_rejects_duplicate_provider_ids():
    with pytest.raises(
        DuplicateModelProviderError
    ):
        ModelRouter(
            providers=[
                FakeProvider(
                    "ollama",
                    "FIRST",
                ),
                FakeProvider(
                    "ollama",
                    "SECOND",
                ),
            ],
            default_provider_id="ollama",
        )


def test_model_router_does_not_fallback_on_provider_failure():
    fallback = FakeProvider(
        "fallback",
        "MUST_NOT_RUN",
    )

    router = ModelRouter(
        providers=[
            FailingProvider(),
            fallback,
        ],
        default_provider_id="failing",
    )

    request = ModelRequest(
        prompt="NEXUS_NO_FALLBACK"
    )

    with pytest.raises(
        RuntimeError,
        match="provider failure",
    ):
        router.generate(request)

    assert fallback.requests == []


def test_model_router_construction_does_not_generate():
    provider = FakeProvider(
        "ollama",
        "UNUSED",
    )

    ModelRouter(
        providers=[provider],
        default_provider_id="ollama",
    )

    assert provider.requests == []


class IncompleteProvider:
    @property
    def provider_id(self):
        return "incomplete"


class InvalidIdProvider:
    def __init__(self, provider_id):
        self._provider_id = provider_id

    @property
    def provider_id(self):
        return self._provider_id

    def generate(self, request):
        return ModelResponse(
            content="INVALID_ID_PROVIDER",
            model="invalid-id-model",
            done=True,
            prompt_tokens=1,
            output_tokens=1,
        )


def test_model_router_rejects_object_without_provider_contract():
    from nexus.models.router import InvalidModelProviderError

    with pytest.raises(
        InvalidModelProviderError
    ):
        ModelRouter(
            providers=[IncompleteProvider()],
            default_provider_id="incomplete",
        )


@pytest.mark.parametrize(
    "provider_id",
    [
        "",
        " ",
        "\n",
        None,
        123,
        True,
    ],
)
def test_model_router_rejects_invalid_registered_provider_id(
    provider_id,
):
    from nexus.models.router import InvalidModelProviderIdError

    with pytest.raises(
        InvalidModelProviderIdError
    ):
        ModelRouter(
            providers=[
                InvalidIdProvider(provider_id)
            ],
            default_provider_id="ollama",
        )


@pytest.mark.parametrize(
    "default_provider_id",
    [
        "",
        " ",
        "\n",
        None,
        123,
        True,
    ],
)
def test_model_router_rejects_invalid_default_provider_id(
    default_provider_id,
):
    from nexus.models.router import InvalidModelProviderIdError

    with pytest.raises(
        InvalidModelProviderIdError
    ):
        ModelRouter(
            providers=[
                FakeProvider(
                    "ollama",
                    "LOCAL_RESPONSE",
                )
            ],
            default_provider_id=default_provider_id,
        )


@pytest.mark.parametrize(
    "provider_id",
    [
        "",
        " ",
        "\n",
        123,
        True,
    ],
)
def test_model_router_resolve_rejects_invalid_provider_id(
    provider_id,
):
    from nexus.models.router import InvalidModelProviderIdError

    router = ModelRouter(
        providers=[
            FakeProvider(
                "ollama",
                "LOCAL_RESPONSE",
            )
        ],
        default_provider_id="ollama",
    )

    with pytest.raises(
        InvalidModelProviderIdError
    ):
        router.resolve(provider_id)


@pytest.mark.parametrize(
    "provider_id",
    [
        "",
        " ",
        "\n",
        123,
        True,
    ],
)
def test_model_router_generate_rejects_invalid_explicit_provider_id(
    provider_id,
):
    from nexus.models.router import InvalidModelProviderIdError

    router = ModelRouter(
        providers=[
            FakeProvider(
                "ollama",
                "LOCAL_RESPONSE",
            )
        ],
        default_provider_id="ollama",
    )

    with pytest.raises(
        InvalidModelProviderIdError
    ):
        router.generate(
            ModelRequest(prompt="Teste"),
            provider_id=provider_id,
        )


class InvalidResponseProvider:
    def __init__(self):
        self.requests = []

    @property
    def provider_id(self):
        return "invalid-response"

    def generate(self, request):
        self.requests.append(request)
        return "not-a-model-response"


@pytest.mark.parametrize(
    "invalid_request",
    [
        None,
        "prompt",
        123,
        True,
        {},
    ],
)
def test_model_router_rejects_invalid_request_before_provider_call(
    invalid_request,
):
    from nexus.models.contracts import ModelValidationError

    provider = FakeProvider(
        "ollama",
        "MUST_NOT_RUN",
    )

    router = ModelRouter(
        providers=[provider],
        default_provider_id="ollama",
    )

    with pytest.raises(ModelValidationError):
        router.generate(invalid_request)

    assert provider.requests == []


def test_model_router_rejects_invalid_provider_response():
    from nexus.models.contracts import ModelProtocolError

    provider = InvalidResponseProvider()

    router = ModelRouter(
        providers=[provider],
        default_provider_id="invalid-response",
    )

    request = ModelRequest(
        prompt="NEXUS_RESPONSE_BOUNDARY"
    )

    with pytest.raises(ModelProtocolError):
        router.generate(request)

    assert provider.requests == [request]
