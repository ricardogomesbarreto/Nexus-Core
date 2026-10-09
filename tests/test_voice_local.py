import io
import json
import subprocess
import sys
import types
import wave

import pytest

from nexus.voice import LocalRecognizer, LocalSpeaker, VoiceError
import nexus.voice.local as voice_module


class FakeProcess:
    def __init__(self, args, *, audio=b"", **kwargs):
        self.args = args
        self.audio = audio
        self.returncode = 0
        self.input = None
        self.terminated = False

    def communicate(self, input=None, timeout=None):
        self.input = input
        return self.audio, b""

    def poll(self):
        return self.returncode

    def terminate(self):
        self.terminated = True

    def kill(self):
        self.terminated = True


def wav_bytes():
    output = io.BytesIO()
    with wave.open(output, "wb") as recording:
        recording.setnchannels(1)
        recording.setsampwidth(2)
        recording.setframerate(16000)
        recording.writeframes(b"\0\0" * 16000)
    return output.getvalue()


def test_speaker_selects_female_or_male_without_shell(monkeypatch):
    processes = []
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/espeak-ng")

    def start(args, **kwargs):
        process = FakeProcess(args, **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(voice_module.subprocess, "Popen", start)
    speaker = LocalSpeaker()
    speaker.speak("Olá", "Feminina")
    speaker.speak("Oi", "Masculina")
    assert processes[0].args == [
        "/usr/bin/espeak-ng", "-v", "pt-br+f3", "-b", "1", "--stdin"
    ]
    assert processes[0].input == "Olá"
    assert processes[1].args[2] == "pt-br+m3"


def test_speaker_fails_closed_on_invalid_voice_or_missing_binary(monkeypatch):
    speaker = LocalSpeaker()
    with pytest.raises(VoiceError, match="inválida"):
        speaker.speak("Oi", "arbitrária")
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: None)
    with pytest.raises(VoiceError, match="eSpeak"):
        speaker.speak("Oi", "Feminina")


def test_speaker_limits_input_size(monkeypatch):
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "espeak-ng")
    process = FakeProcess([])
    monkeypatch.setattr(voice_module.subprocess, "Popen", lambda *a, **k: process)
    LocalSpeaker().speak("a" * 10000)
    assert len(process.input) == LocalSpeaker.MAX_SPEECH


def test_recognizer_reads_local_wav_and_vosk_result(monkeypatch, tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    models = []

    class FakeModel:
        def __init__(self, path):
            models.append(path)

    class FakeDecoder:
        def __init__(self, model, rate):
            assert rate == 16000

        def AcceptWaveform(self, frames):
            return False

        def FinalResult(self):
            return json.dumps({"text": "qual é a hora"})

    monkeypatch.setitem(
        sys.modules, "vosk",
        types.SimpleNamespace(Model=FakeModel, KaldiRecognizer=FakeDecoder),
    )
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/arecord")
    processes = []

    def start(args, **kwargs):
        process = FakeProcess(args, audio=wav_bytes(), **kwargs)
        processes.append(process)
        return process

    monkeypatch.setattr(voice_module.subprocess, "Popen", start)
    recognizer = LocalRecognizer(model_dir)
    assert recognizer.recognize() == "qual é a hora"
    assert models == [str(model_dir)]
    assert processes[0].args[:5] == ["/usr/bin/arecord", "-q", "-d", "8", "-f"]
    assert processes[0].args[-1] == "wav"


def test_recognizer_requires_local_model_before_microphone(monkeypatch, tmp_path):
    monkeypatch.setattr(
        voice_module.subprocess, "Popen",
        lambda *a, **k: pytest.fail("microfone não deve ser aberto"),
    )
    with pytest.raises(VoiceError, match="Modelo Vosk local ausente"):
        LocalRecognizer(tmp_path / "missing").recognize()


def test_recognizer_rejects_invalid_wav(monkeypatch, tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    monkeypatch.setitem(
        sys.modules, "vosk",
        types.SimpleNamespace(Model=lambda path: object()),
    )
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "arecord")
    monkeypatch.setattr(
        voice_module.subprocess, "Popen",
        lambda args, **kwargs: FakeProcess(args, audio=b"invalid", **kwargs),
    )
    with pytest.raises(VoiceError, match="Áudio ou transcrição inválidos"):
        LocalRecognizer(model_dir).recognize()


@pytest.mark.parametrize("voice", ("pt-br+f3", "pt-br+m3"))
def test_real_espeak_variants_generate_local_wave_when_installed(voice):
    binary = voice_module.shutil.which("espeak-ng")
    if binary is None:
        pytest.skip("eSpeak NG não está instalado neste ambiente")
    result = subprocess.run(
        [binary, "-v", voice, "--stdout", "Olá"],
        capture_output=True, timeout=10, check=False,
    )
    assert result.returncode == 0
    assert result.stdout.startswith(b"RIFF")


def test_real_female_and_male_variants_produce_distinct_audio():
    binary = voice_module.shutil.which("espeak-ng")
    if binary is None:
        pytest.skip("eSpeak NG não está instalado neste ambiente")
    female = subprocess.run(
        [binary, "-v", "pt-br+f3", "--stdout", "Olá, como vai?"],
        capture_output=True, timeout=10, check=True,
    )
    male = subprocess.run(
        [binary, "-v", "pt-br+m3", "--stdout", "Olá, como vai?"],
        capture_output=True, timeout=10, check=True,
    )
    assert female.stdout != male.stdout
