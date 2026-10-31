"""Transcrição sob demanda de WAV PCM por Vosk local, sem captura do microfone.

Lê apenas um arquivo escolhido explicitamente pelo usuário e autorizado
por descritor Linux (O_NOFOLLOW). Não persiste áudio/transcrição nem inicia
servidores, download ou serviços adicionais.
"""
from __future__ import annotations

import json
import os
import wave
from pathlib import Path

from nexus.security.paths import PathSecurity
from nexus.voice.local import LocalRecognizer, VoiceError


class LocalWavTranscriber:
    MAX_BYTES = 16 * 1024 * 1024
    MAX_SECONDS = 180
    MAX_TEXT = 8000

    def __init__(self, recognizer: LocalRecognizer | None = None,
                 paths: PathSecurity | None = None):
        self.recognizer = recognizer if recognizer is not None else LocalRecognizer()
        self.paths = paths if paths is not None else PathSecurity()

    def transcribe(self, path: str | Path) -> str:
        if not isinstance(path, (str, Path)) or not os.fspath(path):
            raise VoiceError("Selecione um arquivo WAV local válido.")
        if Path(path).suffix.lower() != ".wav":
            raise VoiceError("Aceitos somente arquivos WAV.")
        try:
            with self.paths.open_regular_file(path) as (fd, _):
                size = os.fstat(fd).st_size
                if size < 44 or size > self.MAX_BYTES:
                    raise VoiceError("Arquivo WAV vazio ou acima de 16 MiB.")
                with os.fdopen(os.dup(fd), "rb") as audio:
                    with wave.open(audio, "rb") as wav:
                        if (wav.getnchannels(), wav.getsampwidth(),
                            wav.getframerate(), wav.getcomptype()) != (
                                1, 2, 16000, "NONE"):
                            raise VoiceError(
                                "WAV deve ser PCM mono, 16-bit, 16 kHz."
                            )
                        frames = wav.getnframes()
                        if frames < 1 or frames > self.MAX_SECONDS * 16000:
                            raise VoiceError("O áudio deve durar no máximo 180 segundos.")
                        # Só carrega o Vosk depois da validação física do arquivo.
                        from vosk import KaldiRecognizer
                        model = self.recognizer._load_model()
                        decoder = KaldiRecognizer(model, 16000)
                        segments = []
                        while chunk := wav.readframes(4000):
                            if decoder.AcceptWaveform(chunk):
                                part = json.loads(decoder.Result()).get("text", "")
                                if isinstance(part, str):
                                    segments.append(part)
                        last = json.loads(decoder.FinalResult()).get("text", "")
                        if isinstance(last, str):
                            segments.append(last)
        except VoiceError:
            raise
        except (OSError, PermissionError, wave.Error, EOFError, ValueError,
                json.JSONDecodeError) as exc:
            raise VoiceError(
                "Não foi possível transcrever o WAV local autorizado."
            ) from exc
        answer = " ".join(" ".join(parts.split()) for parts in segments if parts).strip()
        if not answer:
            raise VoiceError("Nenhuma fala reconhecida no arquivo.")
        return answer[:self.MAX_TEXT]
