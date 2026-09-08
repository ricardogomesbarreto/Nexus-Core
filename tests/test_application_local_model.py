import nexus.core.application as application_module

from nexus.config.settings import load_settings
from nexus.core.application import NexusApplication


class FakeOllamaProvider:
    provider_id = "ollama"


class FakeModelRouter:
    def __init__(self):
        self.provider = FakeOllamaProvider()
        self.resolve_calls = []

    def resolve(self, provider_id):
        self.resolve_calls.append(provider_id)

        if provider_id != "ollama":
            raise AssertionError(
                f"unexpected provider_id: {provider_id}"
            )

        return self.provider


def test_legacy_local_model_client_remains_lazy(
    monkeypatch,
):
    calls = []
    fake_router = FakeModelRouter()

    def fake_build_model_router(settings):
        calls.append(settings)
        return fake_router

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
    )

    app = NexusApplication()

    try:
        assert calls == []

        client = app.local_model_client

        assert client is fake_router.provider
        assert len(calls) == 1
    finally:
        app.database.close()


def test_legacy_local_model_client_uses_configured_settings(
    monkeypatch,
):
    configured_settings = load_settings({})
    calls = []
    fake_router = FakeModelRouter()

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
    )

    app = NexusApplication()

    try:
        client = app.local_model_client

        assert client is fake_router.provider
        assert calls == [configured_settings]
        assert fake_router.resolve_calls == [
            "ollama"
        ]
    finally:
        app.database.close()


def test_legacy_local_model_client_shares_cached_router(
    monkeypatch,
):
    calls = []
    fake_router = FakeModelRouter()

    def fake_build_model_router(settings):
        calls.append(settings)
        return fake_router

    monkeypatch.setattr(
        application_module,
        "build_model_router",
        fake_build_model_router,
    )

    app = NexusApplication()

    try:
        first = app.local_model_client
        second = app.local_model_client

        assert first is fake_router.provider
        assert second is fake_router.provider
        assert first is second
        assert len(calls) == 1
    finally:
        app.database.close()
