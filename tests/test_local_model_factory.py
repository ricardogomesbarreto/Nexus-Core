from nexus.config.settings import load_settings
from nexus.models.local_model_factory import (
    build_local_model_client,
)


class FakeTransport:
    def __init__(
        self,
        *,
        base_url,
    ):
        self.base_url = base_url


def test_build_local_model_client_uses_default_settings():
    settings = load_settings({})

    client = build_local_model_client(
        settings,
        transport_factory=FakeTransport,
    )

    assert client.model == "qwen3:1.7b"
    assert client.timeout == 120.0

    assert isinstance(
        client.transport,
        FakeTransport,
    )

    assert (
        client.transport.base_url
        == "http://127.0.0.1:11434"
    )


def test_build_local_model_client_uses_configured_settings():
    settings = load_settings(
        {
            "NEXUS_LOCAL_MODEL_NAME": "qwen3:4b",
            "NEXUS_LOCAL_MODEL_BASE_URL": (
                "http://localhost:11434"
            ),
            "NEXUS_LOCAL_MODEL_TIMEOUT": "45.5",
        }
    )

    client = build_local_model_client(
        settings,
        transport_factory=FakeTransport,
    )

    assert client.model == "qwen3:4b"
    assert client.timeout == 45.5

    assert (
        client.transport.base_url
        == "http://localhost:11434"
    )
