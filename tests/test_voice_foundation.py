"""Activation phrase and no-capture diagnostics for local voice."""
import pytest

from nexus.voice.wake import extract_utterance
from nexus.voice import diagnostics


@pytest.mark.parametrize("utterance,expected", [
    ("Nexus, qual é a hora?", "qual é a hora"),
    ("nexus explique redes", "explique redes"),
    ("Ei Nexus, tudo bem?", "tudo bem"),
    ("olá nexus: Abra a conversa", "Abra a conversa"),
    ("Hey NEXUS - faça a pergunta", "faça a pergunta"),
    ("  NeXuS! cancelar?  ", "cancelar"),
    ("Nexus", None),
    ("ei nexus", None),
    ("Não mande o Nexus abrir nada", None),
    ("explica, nexus", None),
    ("supernexus executar", None),
    ("NexusCore pergunta", None),
    ("", None),
])
def test_optional_wake_gate_requires_anchored_activation(utterance, expected):
    assert extract_utterance(utterance, require_wake=True) == expected


def test_free_conversation_mode_remains_backward_compatible():
    assert extract_utterance("Qual é a hora?", require_wake=False) == "Qual é a hora?"
    assert extract_utterance("Nexus, qual é a hora?", require_wake=False) == "Nexus, qual é a hora?"


@pytest.mark.parametrize("bad", [None, "", "   ", "a\x00b", "x" * 4001])
def test_invalid_transcripts_are_not_forwarded(bad):
    assert extract_utterance(bad, require_wake=False) is None
    assert extract_utterance(bad, require_wake=True) is None


def test_diagnostics_never_calls_microphone_or_speaker(monkeypatch, tmp_path):
    model = tmp_path / "model"
    model.mkdir()
    monkeypatch.setattr(diagnostics.shutil, "which",
                        lambda name: "/usr/bin/" + name)
    monkeypatch.setattr(diagnostics.importlib.util, "find_spec",
                        lambda name: object())
    checks = diagnostics.inspect_voice(model)
    assert checks["recognition_ready_to_try"] is True
    assert checks["speech_ready_to_try"] is True
    assert checks["microphone_tested"] is False
    assert checks["speaker_tested"] is False
    assert checks["checks"] == {
        "alsa_arecord": True, "vosk_python": True,
        "vosk_local_model": True, "espeak_ng": True,
    }


def test_diagnostics_reports_missing_dependencies_without_recording(monkeypatch, tmp_path):
    monkeypatch.setattr(diagnostics.shutil, "which", lambda name: None)
    monkeypatch.setattr(diagnostics.importlib.util, "find_spec", lambda name: None)
    checks = diagnostics.inspect_voice(tmp_path / "missing")
    assert not checks["recognition_ready_to_try"]
    assert not checks["speech_ready_to_try"]
    assert not any(checks["checks"].values())
