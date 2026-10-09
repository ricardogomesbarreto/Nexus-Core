import nexus.core.application as application_module

from nexus.config.settings import load_settings
from nexus.core.application import NexusApplication
from tests.fakes import FakeDatabase


class FakeOllamaProvider:
    provider_id = "ollama"


class FakeModelRouter:
    def __init__(self):
        self.ollama_provider = FakeOllamaProvider()
        self.resolve_calls = []

    def resolve(self, provider_id):
        self.resolve_calls.append(provider_id)

        if provider_id != "ollama":
            raise AssertionError(
                f"unexpected provider_id: {provider_id}"
            )

        return self.ollama_provider


def test_application_does_not_build_model_router_on_construction(
    monkeypatch,
):
    calls = []

    def fake_build_model_router(settings):
        calls.append(settings)
        return FakeModelRouter()

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
        raising=False,
    )

    app = NexusApplication(
        database=FakeDatabase(),
    )

    try:
        assert calls == []
        assert app._model_router is None
    finally:
        app.database.close()


def test_application_builds_model_router_lazily(
    monkeypatch,
):
    configured_settings = load_settings({})
    fake_router = FakeModelRouter()
    calls = []

    monkeypatch.setattr(
        application_module,
        "settings",
        configured_settings,
    )

    def fake_build_model_router(settings):
        calls.append(settings)
        return fake_router

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
        raising=False,
    )

    app = NexusApplication(
        database=FakeDatabase(),
    )

    try:
        router = app.model_router

        assert router is fake_router
        assert calls == [configured_settings]
    finally:
        app.database.close()


def test_application_caches_model_router(
    monkeypatch,
):
    fake_router = FakeModelRouter()
    calls = []

    def fake_build_model_router(settings):
        calls.append(settings)
        return fake_router

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
        raising=False,
    )

    app = NexusApplication(
        database=FakeDatabase(),
    )

    try:
        first = app.model_router
        second = app.model_router

        assert first is fake_router
        assert second is fake_router
        assert first is second
        assert len(calls) == 1
    finally:
        app.database.close()


def test_application_builds_agent_lazily_with_shared_executor(monkeypatch):
    fake_router = FakeModelRouter()
    monkeypatch.setattr(
        application_module,
        "build_model_router",
        lambda settings: fake_router,
    )
    app = NexusApplication(database=FakeDatabase())
    try:
        assert app._agent is None
        assert app._model_router is None
        agent = app.agent
        assert agent is app.agent
        assert agent.model_router is fake_router
        assert agent.registry is app.tool_registry
        assert agent.executor is app.tool_executor
        assert app.tool_registry.list_tools() == [
            "list_directory", "read_file", "system_info", "terminal_sandbox"
        ]
    finally:
        app.database.close()


def test_legacy_local_model_client_uses_registered_ollama_provider(
    monkeypatch,
):
    fake_router = FakeModelRouter()

    def fake_build_model_router(settings):
        return fake_router

    def forbidden_legacy_factory(settings):
        raise AssertionError(
            "legacy local model factory must not be used"
        )

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
        raising=False,
    )

    monkeypatch.setattr(
        application_module,
        "build_local_model_client",
        forbidden_legacy_factory,
        raising=False,
    )

    app = NexusApplication(
        database=FakeDatabase(),
    )

    try:
        client = app.local_model_client

        assert client is fake_router.ollama_provider
        assert fake_router.resolve_calls == ["ollama"]
    finally:
        app.database.close()


def test_legacy_and_new_model_access_share_same_composition(
    monkeypatch,
):
    fake_router = FakeModelRouter()
    calls = []

    def fake_build_model_router(settings):
        calls.append(settings)
        return fake_router

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
        raising=False,
    )

    app = NexusApplication(
        database=FakeDatabase(),
    )

    try:
        router = app.model_router
        legacy_client = app.local_model_client

        assert router is fake_router
        assert legacy_client is router.resolve("ollama")
        assert len(calls) == 1
    finally:
        app.database.close()
