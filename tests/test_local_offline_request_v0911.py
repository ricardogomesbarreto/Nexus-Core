"""No-internet execution must use localhost, never replay another turn."""

import json
from urllib.request import Request

from nexus.config.settings import Settings
from nexus.models.ollama_provider import OllamaProvider
from nexus.models.ollama_transport import OllamaTransport
from nexus.models.contracts import ModelRequest


class LocalResponse:
    def __init__(self, text):
        self.payload = {
            "model": "qwen3:1.7b", "done": True, "message": {"content": text},
            "prompt_eval_count": 5, "eval_count": 12,
        }

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False

    def read(self, limit=None):
        return json.dumps(self.payload).encode("utf-8")


def test_offline_model_requests_are_unique_and_loopback_only():
    seen = []

    def offline_opener(request: Request, *, timeout: float):
        # Simulate that no external network, DNS or cloud endpoint exists.
        assert request.full_url == "http://127.0.0.1:11434/api/chat"
        content = json.loads(request.data.decode("utf-8"))
        prompt = content["messages"][-1]["content"]
        seen.append(prompt)
        return LocalResponse("Resposta local para: " + prompt)

    provider = OllamaProvider(
        model=Settings().local_model_name,
        transport=OllamaTransport(opener=offline_opener),
    )
    assert Settings().offline_mode is True
    first = provider.generate(ModelRequest(prompt="O que é um professor?"))
    second = provider.generate(ModelRequest(prompt="O que é uma escola?"))
    assert first.done and second.done
    assert first.content != second.content
    assert seen == ["O que é um professor?", "O que é uma escola?"]


def test_model_unavailable_message_is_clear_about_no_internet(tmp_path):
    from nexus.agent import AgentPlanner
    from nexus.models.contracts import ModelProviderUnavailableError
    from nexus.security import AuditLogger, SecurityGate
    from nexus.tools import ToolRegistry, ToolExecutor

    class Router:
        def generate(self, request):
            raise ModelProviderUnavailableError("network not reachable")

    registry = ToolRegistry()
    gate = SecurityGate(audit_logger=AuditLogger(tmp_path / "audit.log"))
    executor = ToolExecutor(registry, gate)
    planner = AgentPlanner(Router(), registry, executor)
    reply = planner.run("O que é uma escola?")
    assert not reply.success
    assert reply.error_code == "MODEL_ERROR"
    assert "Ollama local" in reply.error
    assert "internet não é necessária" in reply.error
    assert "network not reachable" not in reply.error
