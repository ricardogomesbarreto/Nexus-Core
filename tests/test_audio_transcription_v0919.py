"""Simulated offline conversion; no real media capture, network or services."""
import json
import os
import sys
import types
from types import SimpleNamespace

import pytest

from nexus.voice.audio_transcription import LocalAudioTranscriber
from nexus.voice.local import VoiceError
import nexus.voice.audio_transcription as module
from nexus.security.paths import PathSecurity


class LocalFakeModel:
    def _load_model(self):
        return object()


class FakeDecoder:
    def __init__(self, model, rate):
        assert rate == 16000
    def AcceptWaveform(self, pcm):
        return False
    def FinalResult(self):
        return json.dumps({"text": "bom dia nexus core"})


def make_reader(tmp_path):
    policy = PathSecurity()
    policy.home = tmp_path.resolve()
    policy.protected_paths = []
    return LocalAudioTranscriber(LocalFakeModel(), policy)


def test_mp3_uses_authorized_fd_and_local_decoder(tmp_path, monkeypatch):
    file = tmp_path / "aula.mp3"
    file.write_bytes(b"fake mp3 bytes")
    monkeypatch.setattr(module.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setitem(sys.modules, "vosk", types.SimpleNamespace(KaldiRecognizer=FakeDecoder))
    seen = []
    def convert(command, **opts):
        seen.append((command, opts))
        assert command[command.index("-i") + 1].startswith("/proc/self/fd/")
        fd = opts["pass_fds"][0]
        assert os.read(fd, 4) == b"fake"
        assert opts["timeout"] == 35 and opts["stderr"] is not None
        return SimpleNamespace(returncode=0, stdout=b"\x01\x00" * 16000)
    monkeypatch.setattr(module.subprocess, "run", convert)
    assert make_reader(tmp_path).transcribe(file) == "bom dia nexus core"
    assert len(seen) == 1


def test_reject_unapproved_extensions_and_missing_converter(tmp_path, monkeypatch):
    reader = make_reader(tmp_path)
    with pytest.raises(VoiceError, match="Formatos aceitos"):
        reader.transcribe(tmp_path / "payload.sh")
    monkeypatch.setattr(module.shutil, "which", lambda _: None)
    with pytest.raises(VoiceError, match="FFmpeg"):
        reader.transcribe(tmp_path / "song.mp3")


@pytest.mark.parametrize("size", [0, 32 * 1024 * 1024 + 1])
def test_audio_input_bounds_without_launch(tmp_path, monkeypatch, size):
    file = tmp_path / "recording.ogg"
    with file.open("wb") as stream:
        stream.truncate(size)
    monkeypatch.setattr(module.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr(module.subprocess, "run",
                        lambda *a, **kw: pytest.fail("FFmpeg must not start"))
    with pytest.raises(VoiceError, match="32 MiB"):
        make_reader(tmp_path).transcribe(file)


def test_symlink_rejected_before_conversion(tmp_path, monkeypatch):
    real = tmp_path / "real.flac"
    real.write_bytes(b"flac")
    link = tmp_path / "alias.flac"
    link.symlink_to(real)
    monkeypatch.setattr(module.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr(module.subprocess, "run",
                        lambda *a, **kw: pytest.fail("FFmpeg must not start"))
    with pytest.raises(VoiceError, match="autorizado"):
        make_reader(tmp_path).transcribe(link)


def test_ffmpeg_error_never_loads_vosk(tmp_path, monkeypatch):
    file = tmp_path / "broken.m4a"
    file.write_bytes(b"broken")
    monkeypatch.setattr(module.shutil, "which", lambda _: "/usr/bin/ffmpeg")
    monkeypatch.setattr(module.subprocess, "run", lambda *a, **kw:
                        SimpleNamespace(returncode=1, stdout=b""))
    with pytest.raises(VoiceError, match="inválido"):
        make_reader(tmp_path).transcribe(file)
