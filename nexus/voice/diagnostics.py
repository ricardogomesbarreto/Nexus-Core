"""Local, non-recording voice readiness checks for Linux."""
import importlib.util
import os
import shutil
import subprocess
from pathlib import Path

from nexus.config.settings import settings
from nexus.voice.local import LocalRecognizer, LocalSpeaker, VoiceError


def inspect_voice(model_path: str | Path | None = None) -> dict:
    """Only tests local dependency visibility. Never opens microphone/audio."""
    model = Path(model_path or settings.voice_model_path or (
        settings.data_dir / "voice" / "vosk-model-small-pt-0.3"
    )).expanduser()
    stt_binary = shutil.which("arecord")
    runtime = os.environ.get("XDG_RUNTIME_DIR", "")
    pipewire_ready = bool(shutil.which("pw-record") and runtime and
                          Path(runtime, "pipewire-0").is_socket())
    selected = os.environ.get("NEXUS_AUDIO_INPUT", "auto")
    input_binary_ready = (bool(stt_binary) if selected == "alsa" else
                          pipewire_ready if selected == "pipewire" else
                          bool(stt_binary or pipewire_ready) if selected == "auto" else False)
    tts_binary = shutil.which("espeak-ng")
    try:
        vosk_installed = importlib.util.find_spec("vosk") is not None
    except (ImportError, ValueError):
        vosk_installed = False
    ready_input = bool(input_binary_ready and vosk_installed and model.is_dir())
    ready_output = bool(tts_binary)
    return {
        "mode": "offline",
        "microphone_tested": False,
        "speaker_tested": False,
        "recognition_ready_to_try": ready_input,
        "speech_ready_to_try": ready_output,
        "neural_masculine_ready_to_try": LocalSpeaker.neural_voice_ready(),
        "rhvoice_feminine_ready_to_try": LocalSpeaker.female_voice_ready(),
        "checks": {
            "alsa_arecord": bool(stt_binary),
            "pipewire_pw_record": pipewire_ready,
            "vosk_python": vosk_installed,
            "vosk_local_model": model.is_dir(),
            "espeak_ng": ready_output,
        },
        "notice": (
            "Diagnóstico não abre microfone ou alto-falante. "
            "Prontidão real depende de hardware e permissões no Linux."
        ),
    }


def test_microphone() -> dict:
    """Explicit opt-in: record three seconds, report only peak, discard PCM."""
    try:
        command = LocalRecognizer.capture_command(duration=3)
    except VoiceError:
        return {"microphone_tested": False, "status": "recorder_unavailable"}
    backend = "pipewire" if Path(command[0]).name == "pw-record" else "alsa"
    process = None
    timed_out = False
    try:
        process = subprocess.Popen(command, stdout=subprocess.PIPE,
                                   stderr=subprocess.DEVNULL)
        try:
            audio, _ = process.communicate(timeout=4)
        except subprocess.TimeoutExpired:
            timed_out = True
            process.terminate()
            try:
                audio, _ = process.communicate(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                audio, _ = process.communicate()
        if not audio or (process.returncode != 0 and not timed_out):
            return {"microphone_tested": True, "backend": backend,
                    "status": "capture_failed", "signal_detected": False}
        peak = LocalRecognizer.peak_level(audio)
        clipped = LocalRecognizer.clipped_percent(audio)
        clipping = clipped >= 5
        return {"microphone_tested": True, "backend": backend,
                "status": "signal_detected" if peak >= 2 else "no_signal",
                "signal_detected": peak >= 2, "peak_percent": peak,
                "clipped_percent": clipped, "clipping_suspected": clipping,
                "notice": ("Gravação descartada; possível saturação: reduza o ganho de entrada e repita o teste."
                           if clipping else
                           "Gravação descartada; confira a entrada/volume do microfone se não houver sinal.")}
    except OSError:
        return {"microphone_tested": False, "backend": backend,
                "status": "capture_failed", "signal_detected": False}
    finally:
        if process is not None and process.poll() is None:
            process.kill()
            process.communicate()
