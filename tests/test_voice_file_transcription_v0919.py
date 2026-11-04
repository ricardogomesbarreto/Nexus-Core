"""Validação da transcrição de WAV offline e sem abrir dispositivo."""
from contextlib import contextmanager
import io
import json
import os
from pathlib import Path
import sys
import types
import wave

import pytest

from nexus.voice.file_transcription import LocalWavTranscriber
from nexus.voice.local import VoiceError


class FakePaths:
    @contextmanager
    def open_regular_file(self, path):
        fd = os.open(path, os.O_RDONLY | os.O_NOFOLLOW)
        try:
            yield fd, Path(path)
        finally:
            os.close(fd)


class FakeRecognizer:
    def _load_model(self):
        return object()


class Decoder:
    def __init__(self, model, rate):
        assert rate == 16000
    def AcceptWaveform(self, chunk):
        return False
    def Result(self):
        return json.dumps({"text": ""})
    def FinalResult(self):
        return json.dumps({"text": "olá nexus core"})


def wav_file(path, *, rate=16000, channels=1, seconds=1):
    with wave.open(str(path), "wb") as out:
        out.setnchannels(channels)
        out.setsampwidth(2)
        out.setframerate(rate)
        out.writeframes(b"\x00\x00" * channels * rate * seconds)


def test_wav_local_no_microphone_or_network(tmp_path, monkeypatch):
    monkeypatch.setitem(sys.modules, "vosk", types.SimpleNamespace(KaldiRecognizer=Decoder))
    path = tmp_path / "fala.wav"
    wav_file(path)
    recognizer = LocalWavTranscriber(FakeRecognizer(), FakePaths())
    assert recognizer.transcribe(path) == "olá nexus core"


@pytest.mark.parametrize("rate,channels", [(8000, 1), (16000, 2)])
def test_bad_format_rejected_before_model_load(tmp_path, rate, channels):
    path = tmp_path / "bad.wav"
    wav_file(path, rate=rate, channels=channels)
    class RefuseModel:
        def _load_model(self):
            pytest.fail("Modelo não deve ser carregado para formato inválido")
    with pytest.raises(VoiceError, match="PCM mono"):
        LocalWavTranscriber(RefuseModel(), FakePaths()).transcribe(path)


def test_disallowed_type_and_large_file(tmp_path):
    wav = tmp_path / "audio.wav"
    wav.write_bytes(b"0" * (16 * 1024 * 1024 + 1))
    reader = LocalWavTranscriber(FakeRecognizer(), FakePaths())
    with pytest.raises(VoiceError, match="16 MiB"):
        reader.transcribe(wav)
    with pytest.raises(VoiceError, match="somente"):
        reader.transcribe(tmp_path / "other.mp3")


def test_long_duration_rejected(tmp_path):
    wav = tmp_path / "long.wav"
    wav_file(wav, seconds=181)
    with pytest.raises(VoiceError, match="180"):
        LocalWavTranscriber(FakeRecognizer(), FakePaths()).transcribe(wav)
