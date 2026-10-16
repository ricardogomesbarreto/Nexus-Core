"""Audio diagnosis distinguishes no input from Vosk no transcription."""

import json

import pytest

import nexus.main as main_module
import nexus.voice as voice_module


@pytest.mark.parametrize("peak,spoken,expected", [
    (0, "", "no_transcript"),
    (12, "", "no_transcript"),
    (86, "olá nexus", "transcribed"),
])
def test_recognition_cli_exposes_input_peak_and_backend(monkeypatch, capsys, peak, spoken, expected):
    class Recognizer:
        STREAM_LIMIT = 30
        def __init__(self):
            pass
        def recognize_continuous(self, cancelled=None, on_audio_level=None):
            on_audio_level(peak)
            return spoken
        def capture_command(self, **kwargs):
            return ["/usr/bin/pw-record", "--raw", "-"]

    monkeypatch.setattr(voice_module, "LocalRecognizer", Recognizer)
    main_module.cli(["--recognition-test"])
    result = json.loads(capsys.readouterr().out)
    assert result["recognition_tested"] is True
    assert result["status"] == expected
    assert result["peak_percent"] == peak
    assert result["backend"] == "pipewire"
    assert result["level_samples"] == 1
    assert result["diagnosis"]
    assert result["transcript"] == spoken


def test_recognition_cli_distinguishes_no_samples(monkeypatch, capsys):
    class Recognizer:
        def __init__(self):
            pass
        def recognize_continuous(self, cancelled=None, on_audio_level=None):
            return ""
        def capture_command(self, **kwargs):
            return ["/usr/bin/arecord"]

    monkeypatch.setattr(voice_module, "LocalRecognizer", Recognizer)
    main_module.cli(["--recognition-test"])
    result = json.loads(capsys.readouterr().out)
    assert result["backend"] == "alsa"
    assert result["peak_percent"] == 0
    assert result["level_samples"] == 0
    assert "não forneceu amostras" in result["diagnosis"]
