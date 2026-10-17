"""Low-resource desktop inference never needs network or elevated privileges."""

import base64
import io
import logging
from pathlib import Path
import subprocess

import pytest
from PIL import Image

from nexus.config.settings import Settings
from nexus.desktop.runtime_log import live_event
from nexus.models.contracts import ModelRequest
from nexus.models.model_factory import build_model_router
from nexus.models.resource_budget import ResourceBudget
from nexus.vision.local import LocalVision
from nexus.voice.speech_text import speech_from_model_text

MIB = 1024 * 1024
GIB = 1024 * MIB


def test_automatic_mode_adapts_to_6gb_notebook():
    budget = ResourceBudget.detect(
        requested="auto", total_bytes=6 * GIB + GIB // 2,
        available_bytes=617 * MIB, cores=8,
    )
    assert budget.mode == "eco"
    assert budget.num_thread == 2
    assert budget.vision_edge == 768
    assert budget.vision_context <= 1024
    assert budget.keep_alive == "0s"
    assert budget.text_options(4096, 512)["num_predict"] <= 160


def test_balanced_profile_preserves_fast_response_on_powerful_pc():
    budget = ResourceBudget.detect(
        requested="auto", total_bytes=32 * GIB,
        available_bytes=22 * GIB, cores=12,
    )
    assert budget.mode == "balanced"
    assert budget.num_thread == 4
    assert budget.vision_edge == 1536
    assert budget.keep_alive == "45s"


def test_available_memory_can_select_eco_on_large_busy_workstation():
    budget = ResourceBudget.detect(
        requested="auto", total_bytes=32 * GIB,
        available_bytes=800 * MIB, cores=24,
    )
    assert budget.mode == "eco"


@pytest.mark.parametrize("setting", ["on", "fast", "safe", "unlimited", "", "SUDO"])
def test_unknown_profile_must_fail_without_shell_execution(setting):
    with pytest.raises(ValueError, match="NEXUS_RESOURCE_PROFILE"):
        ResourceBudget.detect(
            requested=setting, total_bytes=8 * GIB, available_bytes=4 * GIB,
            cores=8,
        )


def test_explicit_profile_override_is_available_without_system_changes():
    eco = ResourceBudget.detect(
        requested="eco", total_bytes=64 * GIB,
        available_bytes=48 * GIB, cores=32,
    )
    assert eco.mode == "eco"
    assert eco.num_thread == 2


class Transport:
    def __init__(self):
        self.calls = []
    def chat(self, *, payload, timeout):
        self.calls.append((payload, timeout))
        return {
            "model": "qwen3:1.7b", "done": True,
            "message": {"content": "Uma resposta breve."},
            "prompt_eval_count": 12, "eval_count": 8,
        }


def test_factory_uses_eco_options_but_never_activates_ollama(monkeypatch):
    eco = ResourceBudget.detect(requested="eco", total_bytes=6*GIB,
                                available_bytes=700*MIB, cores=6)
    monkeypatch.setattr(ResourceBudget, "detect", lambda **kw: eco)
    transport = Transport()
    router = build_model_router(Settings(), transport_factory=lambda **kw: transport)
    assert transport.calls == []
    answer = router.generate(ModelRequest(
        prompt="Explique redes", context_length=4096,
        max_output_tokens=300,
    ))
    assert answer.content == "Uma resposta breve."
    payload, timeout = transport.calls[0]
    assert payload["model"] == "qwen3:1.7b"
    assert payload["options"]["num_ctx"] == 1024
    assert payload["options"]["num_thread"] == 2
    assert payload["options"]["num_predict"] == 160
    assert payload["keep_alive"] == "0s"
    assert "tools" not in payload
    assert timeout == 120


def test_multimodal_eco_reduces_pixels_without_persisting_frames(monkeypatch):
    eco = ResourceBudget.detect(
        requested="eco", total_bytes=6 * GIB,
        available_bytes=700 * MIB, cores=8,
    )
    monkeypatch.setattr(ResourceBudget, "detect", lambda **kw: eco)
    class VisionTransport:
        def __init__(self): self.calls = []
        def chat(self, *, payload, timeout):
            self.calls.append(payload)
            return {"done": True, "message": {"content": "Uma paisagem simples."}}
    transport = VisionTransport()
    out = io.BytesIO()
    Image.new("RGB", (1800, 1100), "purple").save(out, "PNG")
    vision = LocalVision(Settings(), transport=transport)
    assert vision.describe(out.getvalue())["description"]
    payload = transport.calls[0]
    encoded = base64.b64decode(payload["messages"][0]["images"][0])
    with Image.open(io.BytesIO(encoded)) as image:
        assert max(image.size) <= 768
        assert not image.info
    assert payload["keep_alive"] == "0s"
    assert payload["options"]["num_thread"] == 2
    assert payload["options"]["num_predict"] == 144
    assert payload["options"]["num_ctx"] == 1024


def test_speech_budget_keeps_full_text_for_chat():
    original = "A resposta é importante. " * 130
    rendered = speech_from_model_text(original, max_characters=450)
    assert len(rendered) < 550
    assert rendered.endswith("Consulte o restante na conversa.")
    assert len(original) > len(rendered)
    with pytest.raises(ValueError):
        speech_from_model_text("Oi", max_characters=3)


def test_resource_telemetry_logs_only_bounded_numbers(caplog):
    caplog.set_level(logging.INFO, logger="nexus.desktop_runtime")
    live_event("recurso", "pronto", profile="eco", threads=2,
               memory_mib=617)
    live_event("teste", "iniciado", source="voz")
    live_event("teste", "recebido", source="voz")
    live_event("teste", "concluido", source="voz")
    assert "evento=recurso estado=pronto perfil=eco threads=2 ram_disponivel_mib=617" in caplog.text
    assert "evento=teste estado=concluido origem=voz" in caplog.text
    assert "password" not in caplog.text
    with pytest.raises(ValueError):
        live_event("recurso", "pronto", memory_mib="123password")


def test_session_script_has_syntax_and_avoids_autoenable():
    root = Path(__file__).resolve().parents[1]
    script = root / "scripts" / "nexus_core_session.sh"
    result = subprocess.run(["bash", "-n", str(script)], capture_output=True, text=True)
    assert result.returncode == 0
    source = script.read_text()
    assert "systemctl enable" not in source
    assert "ollama pull" not in source
    assert "pg_lsclusters" in source
    assert "--desktop" in source


@pytest.mark.skipif(not __import__("os").environ.get("DISPLAY"), reason="Requer display Xvfb")
def test_gui_test_panel_never_claims_unobserved_success(monkeypatch, caplog):
    import tkinter as tk
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow
    import time

    class App:
        agent = object()
        closed = False
        def shutdown(self): self.closed = True
    class Recognition:
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
        window = DesktopWindow(
            root, App(), confirmation, recognizer=Recognition(),
            speaker=Speaker(),
        )
        caplog.set_level(logging.INFO, logger="nexus.desktop_runtime")
        window._show_test_panel()
        root.update()
        assert window.test_button.cget("text") == "Testar funções"
        assert "evento=teste estado=solicitado" in caplog.text
        assert "evento=teste estado=concluido" not in caplog.text
        window._start_voice_diagnostic()
        root.update()
        assert window._test_voice_turns_remaining == 2
        assert "evento=teste estado=iniciado origem=voz" in caplog.text
        assert "evento=teste estado=concluido origem=voz" not in caplog.text
        window._close()
    finally:
        confirmation.close()
        try: root.destroy()
        except tk.TclError: pass
