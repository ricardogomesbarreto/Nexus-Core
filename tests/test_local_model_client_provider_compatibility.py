import nexus.models.local_model as local_model_module

from nexus.models.contracts import (
    ModelRequest,
    ModelResponse,
)
from nexus.models.local_model import LocalModelClient


class ForbiddenDirectTransport:
    def chat(self, *, payload, timeout):
        raise AssertionError(
            "LocalModelClient não deve chamar transport.chat() diretamente"
        )


def test_local_model_client_delegates_to_ollama_provider(
    monkeypatch,
):
    construction_calls = []
    generate_calls = []

    expected_response = ModelResponse(
        content="NEXUS_COMPAT_OK",
        model="compat-model",
        done=True,
        prompt_tokens=2,
        output_tokens=1,
    )

    class FakeOllamaProvider:
        def __init__(
            self,
            *,
            model,
            transport,
            timeout,
        ):
            construction_calls.append(
                {
                    "model": model,
                    "transport": transport,
                    "timeout": timeout,
                }
            )

        @property
        def provider_id(self):
            return "ollama"

        def generate(self, request):
            generate_calls.append(request)
            return expected_response

    monkeypatch.setattr(
        local_model_module,
        "OllamaProvider",
        FakeOllamaProvider,
        raising=False,
    )

    transport = ForbiddenDirectTransport()

    client = LocalModelClient(
        model="qwen3:1.7b",
        transport=transport,
        timeout=45.0,
    )

    assert construction_calls == [
        {
            "model": "qwen3:1.7b",
            "transport": transport,
            "timeout": 45.0,
        }
    ]

    request = ModelRequest(
        prompt="NEXUS_COMPAT_TEST"
    )

    response = client.generate(request)

    assert generate_calls == [request]
    assert response is expected_response
