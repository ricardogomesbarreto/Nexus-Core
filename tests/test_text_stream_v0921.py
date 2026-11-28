"""Bounded text streaming and cancellation without a live Ollama server."""

import json
import os

import pytest

from nexus.models.contracts import ModelRequest, ModelValidationError
from nexus.models.ollama_provider import OllamaProvider
from nexus.models.ollama_transport import (
    OllamaCancelledError, OllamaInvalidJSONError, OllamaTransport,
)
from nexus.models.router import ModelRouter


class Frames:
    def __init__(self, frames):
        self.frames = iter(frames)
        self.closed = False

    def __enter__(self):
        return self

    def __exit__(self, *_):
        self.closed = True

    def readline(self, size):
        return next(self.frames, b"")[:size]


def line(content, *, done=False):
    return (json.dumps({
        "model": "tiny", "message": {"content": content},
        "done": done, "prompt_eval_count": 2, "eval_count": 1,
    }).encode() + b"\n")


def test_transport_delivers_incremental_text_and_final_metadata():
    frames = Frames([line("Olá"), line(" mundo", done=True)])
    requests = []

    def opener(request, *, timeout):
        requests.append(json.loads(request.data))
        return frames

    snapshots = []
    transport = OllamaTransport(opener=opener)
    result = transport.chat_stream(
        payload={"model": "tiny", "stream": False}, timeout=2,
        on_partial=snapshots.append, is_cancelled=lambda: False,
    )
    assert requests[0]["stream"] is True
    assert snapshots == ["Olá", "Olá mundo"]
    assert result["message"]["content"] == "Olá mundo"
    assert frames.closed


def test_transport_closes_on_cancel_before_following_token():
    frames = Frames([line("primeiro"), line("segundo", done=True)])
    cancelled = False

    def partial(_):
        nonlocal cancelled
        cancelled = True

    with pytest.raises(OllamaCancelledError):
        OllamaTransport(opener=lambda *_args, **_kwargs: frames).chat_stream(
            payload={}, timeout=2, on_partial=partial,
            is_cancelled=lambda: cancelled,
        )
    assert frames.closed


@pytest.mark.parametrize("frames", [
    [line("não concluído")],
    [b"x" * 4097 + b"\n"],
    [line("x" * 4000), line("x" * 4000), line("x" * 3000, done=True)],
])
def test_transport_rejects_incomplete_or_unbounded_stream(frames):
    response = Frames(frames)
    with pytest.raises(OllamaInvalidJSONError):
        OllamaTransport(opener=lambda *_args, **_kwargs: response).chat_stream(
            payload={}, timeout=2, on_partial=lambda _: None,
            is_cancelled=lambda: False,
        )
    assert response.closed


def test_provider_and_router_stream_text_only():
    frames = Frames([line("sim", done=True)])
    transport = OllamaTransport(opener=lambda *_args, **_kwargs: frames)
    provider = OllamaProvider(model="tiny", transport=transport)
    router = ModelRouter(providers=[provider], default_provider_id="ollama")
    seen = []
    result = router.generate_stream(
        ModelRequest(prompt="Oi"), on_partial=seen.append,
        is_cancelled=lambda: False,
    )
    assert result.content == "sim" and seen == ["sim"]
    with pytest.raises(ModelValidationError):
        router.generate_stream(ModelRequest(prompt="oi", json_mode=True),
                               on_partial=seen.append, is_cancelled=lambda: False)


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer display Linux")
def test_transcript_replaces_one_partial_turn_and_discards_it_on_cancel():
    import tkinter as tk
    from nexus.desktop.window import DesktopWindow

    root = tk.Tk()
    try:
        window = DesktopWindow.__new__(DesktopWindow)
        window.transcript = tk.Text(root)
        window._stream_start = None
        window._busy = True
        window._closing = False
        window._cancel_requested = False
        window._show_partial("primeiro")
        window._show_partial("primeiro segundo")
        assert window.transcript.get("1.0", "end").count("Nexus Core") == 1
        assert "primeiro segundo" in window.transcript.get("1.0", "end")
        window._cancel_requested = True
        window._clear_partial()
        assert "primeiro" not in window.transcript.get("1.0", "end")
    finally:
        root.destroy()


def test_planner_streams_conversation_but_not_tool_proposals(tmp_path):
    from nexus.agent import AgentPlanner
    from nexus.models.contracts import ModelResponse
    from nexus.security import AuditLogger, SecurityGate
    from nexus.tools import SystemInfoTool, ToolExecutor, ToolRegistry

    class Router:
        def __init__(self):
            self.streams = self.full = 0

        def generate_stream(self, request, *, on_partial, is_cancelled):
            assert not request.json_mode
            self.streams += 1
            on_partial("Olá")
            return ModelResponse("Olá", "tiny", True, 1, 1)

        def generate(self, request):
            assert request.json_mode
            self.full += 1
            return ModelResponse('{"type":"message","content":"Preciso do alvo."}',
                                 "tiny", True, 1, 1)

    router = Router()
    registry = ToolRegistry()
    registry.register(SystemInfoTool())
    executor = ToolExecutor(registry, SecurityGate(
        audit_logger=AuditLogger(tmp_path / "audit.log")))
    agent = AgentPlanner(router, registry, executor)
    partials = []
    assert agent.run("O que é isto?", on_partial=partials.append).content == "Olá"
    assert partials == ["Olá"] and router.streams == 1
    assert agent.run("Abra um programa específico?", on_partial=partials.append).content
    assert router.full == 1 and partials == ["Olá"]
