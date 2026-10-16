import io
import json
import os
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
        self.stdout = io.BytesIO(audio)
        self.returncode = 0
        self.input = None
        self.terminated = False

    def communicate(self, input=None, timeout=None):
        self.input = input
        return self.audio, b""

    def poll(self):
        return self.returncode

    def wait(self, timeout=None):
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
    assert processes[0].input == "Olá."
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


def test_continuous_recognizer_returns_at_vosk_speech_endpoint(monkeypatch, tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    class FakeDecoder:
        def __init__(self, model, rate):
            assert rate == 16000

        def AcceptWaveform(self, frames):
            assert frames
            return True

        def Result(self):
            return json.dumps({"text": "olá assistente"})

    monkeypatch.setitem(sys.modules, "vosk", types.SimpleNamespace(
        Model=lambda path: object(), KaldiRecognizer=FakeDecoder,
    ))
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/arecord")
    processes = []

    def start(args, **kwargs):
        process = FakeProcess(args, audio=b"\0\0" * 4000)
        process.returncode = None
        processes.append(process)
        return process

    monkeypatch.setattr(voice_module.subprocess, "Popen", start)
    recognizer = LocalRecognizer(model_dir)
    assert recognizer.recognize_continuous() == "olá assistente"
    assert processes[0].args[-1] == "raw"
    assert processes[0].terminated


def test_continuous_recognizer_flushes_short_utterance_after_pause(monkeypatch, tmp_path):
    from array import array
    model_dir = tmp_path / "model"
    model_dir.mkdir()

    class Decoder:
        def __init__(self, model, rate):
            pass
        def AcceptWaveform(self, frames):
            return False
        def FinalResult(self):
            return json.dumps({"text": "abra a câmera"})

    monkeypatch.setitem(sys.modules, "vosk", types.SimpleNamespace(
        Model=lambda path: object(), KaldiRecognizer=Decoder))
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/arecord")
    audio = array("h", [12000] * 4000).tobytes() + b"\0" * 8000 * 12
    process = FakeProcess(["arecord"], audio=audio)
    process.returncode = None
    monkeypatch.setattr(voice_module.subprocess, "Popen", lambda *a, **k: process)
    tick = iter(i * .25 for i in range(1000))
    monkeypatch.setattr(voice_module, "monotonic", lambda: next(tick))
    assert LocalRecognizer(model_dir).recognize_continuous() == "abra a câmera"
    assert process.terminated


def test_continuous_recognizer_never_opens_mic_after_pause(monkeypatch, tmp_path):
    model_dir = tmp_path / "model"
    model_dir.mkdir()
    monkeypatch.setitem(sys.modules, "vosk", types.SimpleNamespace(Model=lambda path: object()))
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/arecord")
    monkeypatch.setattr(voice_module.subprocess, "Popen", lambda *a, **k: pytest.fail(
        "Microfone aberto após pausa"
    ))
    assert LocalRecognizer(model_dir).recognize_continuous(lambda: True) == ""


def test_pipewire_is_selected_on_active_desktop_and_can_be_overridden(monkeypatch, tmp_path):
    from pathlib import Path
    monkeypatch.setattr(Path, "is_socket", lambda path: path.name == "pipewire-0")
    monkeypatch.setenv("XDG_RUNTIME_DIR", str(tmp_path))
    monkeypatch.setattr(voice_module.shutil, "which",
                        lambda name: "/usr/bin/" + name)
    command = LocalRecognizer.capture_command()
    assert command[0] == "/usr/bin/pw-record"
    assert "--raw" in command  # Never decode AU container headers as speech samples.
    assert command[command.index("--rate") + 1] == "16000"
    assert command[command.index("--channels") + 1] == "1"
    assert command[command.index("--format") + 1] == "s16"
    assert command[-1] == "-"
    monkeypatch.setenv("NEXUS_AUDIO_INPUT", "alsa")
    assert LocalRecognizer.capture_command()[0] == "/usr/bin/arecord"


def test_audio_level_detects_signal_without_retaining_recording():
    from array import array
    assert LocalRecognizer.peak_level(b"\0" * 8000) == 0
    assert LocalRecognizer.peak_level(array("h", [5000, -5000]).tobytes()) >= 10


def test_neural_male_voice_uses_local_model_and_player(monkeypatch, tmp_path):
    model = tmp_path / "pt_BR-faber-medium.onnx"
    model.write_bytes(b"model")
    model.with_suffix(".onnx.json").write_text("{}")
    monkeypatch.setattr(LocalSpeaker, "neural_model_path", staticmethod(lambda: model))
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/" + name)
    calls = []

    class Process(FakeProcess):
        def __init__(self, args, **kwargs):
            super().__init__(args, **kwargs)
            self.returncode = None
            if args[0].endswith("piper"):
                from pathlib import Path
                Path(args[args.index("--output_file") + 1]).write_bytes(b"RIFF" + b"0" * 50)
        def communicate(self, input=None, timeout=None):
            self.returncode = 0
            return super().communicate(input=input, timeout=timeout)

    def start(args, **kwargs):
        calls.append((args, kwargs))
        return Process(args, **kwargs)

    monkeypatch.setattr(voice_module.subprocess, "Popen", start)
    LocalSpeaker().speak("Olá", "Masculina")
    assert "--model" in calls[0][0]
    assert calls[1][0][0].endswith("pw-play")


def test_female_rhvoice_is_used_when_installed(monkeypatch, tmp_path):
    monkeypatch.setattr(LocalSpeaker, "female_voice_ready", staticmethod(lambda: True))
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/" + name)
    calls = []

    class Process(FakeProcess):
        def __init__(self, args, **kwargs):
            super().__init__(args, **kwargs)
            self.returncode = None
            if args[0].endswith("RHVoice-test"):
                from pathlib import Path
                Path(args[args.index("-o") + 1]).write_bytes(b"RIFF" + b"0" * 50)
        def communicate(self, input=None, timeout=None):
            self.returncode = 0
            return super().communicate(input=input, timeout=timeout)

    def start(args, **kwargs):
        calls.append(args)
        return Process(args, **kwargs)

    monkeypatch.setattr(voice_module.subprocess, "Popen", start)
    LocalSpeaker().speak("Olá", "Feminina")
    assert calls[0][:3] == ["/usr/bin/RHVoice-test", "-p", "Leticia-F123"]
    assert calls[1][0] == "/usr/bin/pw-play"


def test_male_piper_uses_gentle_pacing_and_local_player(monkeypatch, tmp_path):
    model = tmp_path / "voice.onnx"
    model.write_bytes(b"model")
    model.with_suffix(".onnx.json").write_text("{}")
    monkeypatch.setattr(LocalSpeaker, "neural_voice_ready", classmethod(lambda cls: True))
    monkeypatch.setattr(LocalSpeaker, "neural_model_path", classmethod(lambda cls: model))
    monkeypatch.setattr(voice_module.shutil, "which", lambda name: "/usr/bin/" + name)
    commands = []

    class Process(FakeProcess):
        def __init__(self, args, **kwargs):
            super().__init__(args, **kwargs)
            self.returncode = None
            if "--output_file" in args:
                from pathlib import Path
                Path(args[args.index("--output_file") + 1]).write_bytes(b"RIFF" + b"0" * 50)
        def communicate(self, input=None, timeout=None):
            self.returncode = 0
            return super().communicate(input=input, timeout=timeout)

    monkeypatch.setattr(voice_module.subprocess, "Popen",
                        lambda args, **kw: commands.append((args, kw)) or Process(args, **kw))
    LocalSpeaker().speak("  Olá   mundo  ", "Masculina")
    assert commands[0][0][-2:] == ["--length-scale", "1.05"]
    assert commands[1][0][0] == "/usr/bin/pw-play"


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
