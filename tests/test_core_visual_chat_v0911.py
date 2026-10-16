"""Regressions for local vision readiness, GUI submission and honest previews."""

import io
import json
import os
import time
from datetime import datetime

import pytest
from PIL import Image

from nexus.config.settings import Settings
from nexus.desktop.local_replies import local_conversation_answer
from nexus.vision.local import LocalVision, VisionError


def image_bytes():
    image = Image.new("RGB", (24, 20), (150, 20, 70))
    out = io.BytesIO()
    image.save(out, "PNG")
    return out.getvalue()


class InstalledModels:
    def __init__(self, names):
        self.names = names
        self.requests = []

    def list_models(self):
        return list(self.names)

    def chat(self, *, payload, timeout):
        self.requests.append(payload)
        return {"done": True, "message": {"content": "Uma imagem vermelha."}}


def test_visual_inference_refuses_text_only_ollama_with_install_hint():
    transport = InstalledModels(["qwen3:1.7b"])
    vision = LocalVision(Settings(), transport=transport)
    with pytest.raises(VisionError, match="ollama pull gemma3:4b"):
        vision.describe(image_bytes())
    assert transport.requests == []


def test_visual_inference_selects_installed_multimodal_model():
    transport = InstalledModels(["qwen3:1.7b", "llava:7b"])
    vision = LocalVision(Settings(), transport=transport)
    result = vision.describe(image_bytes())
    assert result["model"] == "llava:7b"
    assert result["description"] == "Uma imagem vermelha."
    assert transport.requests[0]["model"] == "llava:7b"
    assert transport.requests[0]["messages"][0]["images"]


def test_explicit_visual_model_must_be_present(monkeypatch):
    monkeypatch.setenv("NEXUS_VISION_MODEL", "gemma3:4b")
    transport = InstalledModels(["llava:7b"])
    with pytest.raises(VisionError, match="não está instalado"):
        LocalVision(Settings(), transport=transport).describe(image_bytes())
    assert transport.requests == []


def test_ollama_installed_model_list_is_loopback_only():
    from nexus.models.ollama_transport import OllamaTransport

    calls = []
    class Response:
        def __enter__(self): return self
        def __exit__(self, *args): return False
        def read(self, maximum):
            assert maximum <= 512 * 1024 + 1
            return json.dumps({"models": [{"name": "gemma3:4b"}, {"name": "qwen3:1.7b"}]}).encode()

    def opener(request, *, timeout):
        calls.append((request.full_url, request.get_method(), timeout))
        return Response()

    transport = OllamaTransport(opener=opener)
    assert transport.list_models() == ["gemma3:4b", "qwen3:1.7b"]
    assert calls == [("http://127.0.0.1:11434/api/tags", "GET", 5.0)]


def test_strict_local_time_and_date_do_not_guess():
    fixed = datetime(2026, 10, 16, 18, 42)
    assert local_conversation_answer("Que horas são?", now=fixed) == (
        "Agora são 18:42, no horário local deste computador."
    )
    assert local_conversation_answer("Qual é a data de hoje?", now=fixed) == (
        "Hoje é 16/10/2026, conforme a data deste computador."
    )
    assert local_conversation_answer("Me mostre os arquivos", now=fixed) is None


def test_capabilities_reply_is_local_and_does_not_claim_unimplemented_actions():
    answer = local_conversation_answer("O que você pode fazer?")
    assert "Ollama local" in answer
    assert "com autorização" in answer
    assert "criar pastas por comando ainda não estão disponíveis" in answer
    assert local_conversation_answer("O que você pode fazer no meu navegador?") is None


def test_chat_local_time_does_not_contact_ollama_or_system_info():
    from nexus.desktop.conversation import ChatSession
    class Agent:
        def run(self, *args, **kwargs):
            pytest.fail("Time query must be resolved locally")
    result = ChatSession(Agent()).ask("Que horas são?")
    assert result.outcome.success
    assert "horário local" in result.text


def test_pretty_system_info_without_raw_json():
    from nexus.agent import AgentOutcome
    from nexus.desktop.conversation import ChatSession
    from nexus.tools import ToolResult
    result = ChatSession._describe(AgentOutcome(
        True, tool_result=ToolResult(True, "system_info", data={
            "system": "Linux", "release": "6.14", "machine": "x86_64",
            "python": "3.12.3",
        })
    ))
    assert "Sistema operacional: Linux" in result
    assert "Arquitetura: x86_64" in result
    assert '"system"' not in result


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_enter_submits_and_shift_enter_inserts_newline():
    import tkinter as tk
    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        def __init__(self):
            self.agent = self
            self.asked = []
            self.closed = False
        def run(self, prompt, **kwargs):
            self.asked.append(prompt)
            return AgentOutcome(True, content="Resposta amigável.")
        def shutdown(self):
            self.closed = True
    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled(): time.sleep(.01)
            return ""
        def stop(self): pass
    class Speaker:
        def speak(self, text, voice): pass
        def stop(self): pass

    root = tk.Tk()
    app = App()
    confirmation = DesktopConfirmation()
    try:
        window = DesktopWindow(root, app, confirmation,
                               recognizer=Recognizer(), speaker=Speaker())
        window.speech_enabled.set(False)
        root.update()
        window.input.insert("1.0", "Olá Nexus")
        window.input.focus_force()
        root.update()
        window.input.event_generate("<Shift-Return>")
        root.update()
        assert "\n" in window.input.get("1.0", "end-1c")
        assert app.asked == []
        window.input.delete("1.0", "end")
        window.input.insert("1.0", "Preciso de ideias")
        window.input.event_generate("<Return>")
        deadline = time.monotonic() + 5
        while (window._busy or not app.asked) and time.monotonic() < deadline:
            root.update()
            time.sleep(.01)
        assert len(app.asked) == 1
        assert "Preciso de ideias" in app.asked[0]
        assert "Resposta amigável." in window.transcript.get("1.0", "end")
        window._close()
        deadline = time.monotonic() + 5
        while not app.closed and time.monotonic() < deadline:
            root.update()
            time.sleep(.01)
        assert app.closed
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_authorized_image_preview_shows_source_and_real_pixels():
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        agent = object()
        def shutdown(self): pass
    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled(): time.sleep(.01)
            return ""
        def stop(self): pass
    class Speaker:
        def speak(self, text, voice): pass
        def stop(self): pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    try:
        window = DesktopWindow(root, App(), confirmation,
                               recognizer=Recognizer(), speaker=Speaker())
        window.speech_enabled.set(False)
        for source, title in (("file", "imagem importada"),
                              ("camera", "foto da câmera"),
                              ("screen", "tela capturada")):
            window._show_camera_frame(image_bytes(), source)
            root.update()
            assert window._camera_preview is not None
            assert title in window._camera_preview.title()
        window._close()
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass
