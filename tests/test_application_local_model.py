import nexus.core.application as application_module

from nexus.config.settings import load_settings
from nexus.core.application import NexusApplication


class FakeLocalModelClient:
    pass


def test_application_does_not_build_local_model_client_on_construction(
    monkeypatch,
):
    calls = []

    def fake_build_local_model_client(settings):
        calls.append(settings)
        return FakeLocalModelClient()

    monkeypatch.setattr(
        application_module,
        "build_local_model_client",
        fake_build_local_model_client,
        raising=False,
    )

    app = NexusApplication()

    try:
        assert calls == []
    finally:
        app.database.close()


def test_application_builds_local_model_client_lazily(
    monkeypatch,
):
    configured_settings = load_settings({})
    fake_client = FakeLocalModelClient()
    calls = []

    monkeypatch.setattr(
        application_module,
        "settings",
        configured_settings,
    )

    def fake_build_local_model_client(settings):
        calls.append(settings)
        return fake_client

    monkeypatch.setattr(
        application_module,
        "build_local_model_client",
        fake_build_local_model_client,
        raising=False,
    )

    app = NexusApplication()

    try:
        client = app.local_model_client

        assert client is fake_client
        assert calls == [configured_settings]
    finally:
        app.database.close()


def test_application_caches_local_model_client(
    monkeypatch,
):
    fake_client = FakeLocalModelClient()
    calls = []

    def fake_build_local_model_client(settings):
        calls.append(settings)
        return fake_client

    monkeypatch.setattr(
        application_module,
        "build_local_model_client",
        fake_build_local_model_client,
        raising=False,
    )

    app = NexusApplication()

    try:
        first = app.local_model_client
        second = app.local_model_client

        assert first is fake_client
        assert second is fake_client
        assert first is second
        assert len(calls) == 1
    finally:
        app.database.close()
