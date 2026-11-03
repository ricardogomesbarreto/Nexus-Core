"""Transcrição de formatos comuns usando FFmpeg e Vosk locais sob autorização.

Não usa servidor, shell, microfone, modelo extra, diretórios temporários ou
persistência. Os descritores do arquivo selecionado são fixados com O_NOFOLLOW.
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

from nexus.security.paths import PathSecurity
from nexus.voice.file_transcription import LocalWavTranscriber
from nexus.voice.local import LocalRecognizer, VoiceError


class LocalAudioTranscriber:
    EXTENSIONS = frozenset({".wav", ".mp3", ".ogg", ".flac", ".m4a"})
    MAX_INPUT = 32 * 1024 * 1024
    MAX_SECONDS = 180
    PCM_RATE = 16000
    MAX_OUTPUT = MAX_SECONDS * PCM_RATE * 2

    def __init__(self, recognizer: LocalRecognizer | None = None,
                 paths: PathSecurity | None = None):
        self.recognizer = recognizer if recognizer is not None else LocalRecognizer()
        self.paths = paths if paths is not None else PathSecurity()

    def transcribe(self, path: str | Path) -> str:
        if not isinstance(path, (str, Path)) or not os.fspath(path):
            raise VoiceError("Selecione um arquivo de áudio.")
        extension = Path(path).suffix.lower()
        if extension not in self.EXTENSIONS:
            raise VoiceError("Formatos aceitos: WAV, MP3, OGG, FLAC ou M4A.")
        if extension == ".wav":
            # Keep the existing strict WAV path and its direct no-conversion mode.
            return LocalWavTranscriber(self.recognizer, self.paths).transcribe(path)
        binary = shutil.which("ffmpeg")
        if binary is None:
            raise VoiceError("Instale FFmpeg local para transcrever este formato.")
        try:
            with self.paths.open_regular_file(path) as (fd, _):
                size = os.fstat(fd).st_size
                if not 0 < size <= self.MAX_INPUT:
                    raise VoiceError("Áudio vazio ou acima de 32 MiB.")
                completed = subprocess.run(
                    [binary, "-nostdin", "-hide_banner", "-loglevel", "error",
                     "-i", f"/proc/self/fd/{fd}", "-vn", "-ac", "1",
                     "-ar", str(self.PCM_RATE), "-t", str(self.MAX_SECONDS),
                     "-f", "s16le", "-acodec", "pcm_s16le", "pipe:1"],
                    stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                    stderr=subprocess.DEVNULL, timeout=35, check=False,
                    pass_fds=(fd,),
                )
        except VoiceError:
            raise
        except (OSError, PermissionError, subprocess.SubprocessError) as exc:
            raise VoiceError("Falha ao converter áudio local autorizado.") from exc
        pcm = completed.stdout
        if (completed.returncode != 0 or not pcm or len(pcm) % 2
                or len(pcm) > self.MAX_OUTPUT):
            raise VoiceError("Áudio inválido, incompatível ou acima do limite.")
        try:
            from vosk import KaldiRecognizer
            decoder = KaldiRecognizer(self.recognizer._load_model(), self.PCM_RATE)
            parts = []
            for start in range(0, len(pcm), 8000):
                if decoder.AcceptWaveform(pcm[start:start + 8000]):
                    part = json.loads(decoder.Result()).get("text", "")
                    if isinstance(part, str):
                        parts.append(part)
            final = json.loads(decoder.FinalResult()).get("text", "")
            if isinstance(final, str):
                parts.append(final)
        except (ImportError, ValueError, json.JSONDecodeError) as exc:
            raise VoiceError("Falha ao reconhecer áudio com Vosk local.") from exc
        result = " ".join(p.strip() for p in parts if p).strip()
        if not result:
            raise VoiceError("Nenhuma fala reconhecida no arquivo.")
        return result[:8000]
