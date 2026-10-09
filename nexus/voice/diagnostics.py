"""Local, non-recording voice readiness checks for Linux."""
import importlib.util
import shutil
from pathlib import Path

from nexus.config.settings import settings


def inspect_voice(model_path: str | Path | None = None) -> dict:
    """Only tests local dependency visibility. Never opens microphone/audio."""
    model = Path(model_path or settings.voice_model_path or (
        settings.data_dir / "voice" / "vosk-model-small-pt-0.3"
    )).expanduser()
    stt_binary = shutil.which("arecord")
    tts_binary = shutil.which("espeak-ng")
    try:
        vosk_installed = importlib.util.find_spec("vosk") is not None
    except (ImportError, ValueError):
        vosk_installed = False
    ready_input = bool(stt_binary and vosk_installed and model.is_dir())
    ready_output = bool(tts_binary)
    return {
        "mode": "offline",
        "microphone_tested": False,
        "speaker_tested": False,
        "recognition_ready_to_try": ready_input,
        "speech_ready_to_try": ready_output,
        "checks": {
            "alsa_arecord": bool(stt_binary),
            "vosk_python": vosk_installed,
            "vosk_local_model": model.is_dir(),
            "espeak_ng": ready_output,
        },
        "notice": (
            "Diagnóstico não abre microfone ou alto-falante. "
            "Prontidão real depende de hardware e permissões no Linux."
        ),
    }
