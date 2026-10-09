"""Áudio local: eSpeak NG para saída e Vosk/ALSA para conversa contínua."""

import io
import json
import shutil
import subprocess
import wave
from pathlib import Path
from threading import Lock
from typing import Callable

from nexus.config.settings import settings


class VoiceError(RuntimeError):
    """Falha tratável de áudio local, sem executar ações do Agent."""


class _StoppableProcess:
    def __init__(self):
        self._lock = Lock()
        self._process = None

    def _set_process(self, process):
        with self._lock:
            self._process = process

    def _clear_process(self, process):
        with self._lock:
            if self._process is process:
                self._process = None

    def stop(self) -> None:
        with self._lock:
            process = self._process
            if process is not None and process.poll() is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass


class LocalSpeaker(_StoppableProcess):
    """Síntese limitada a variantes explícitas em português brasileiro."""

    VOICES = {"Feminina": "pt-br+f3", "Masculina": "pt-br+m3"}
    MAX_SPEECH = 2400

    def speak(self, text: str, voice: str = "Feminina") -> None:
        if voice not in self.VOICES:
            raise VoiceError("Seleção de voz inválida.")
        if not isinstance(text, str) or not text.strip():
            raise VoiceError("Não há texto para falar.")
        binary = shutil.which("espeak-ng")
        if binary is None:
            raise VoiceError("Instale eSpeak NG para ouvir as respostas.")
        try:
            process = subprocess.Popen(
                [binary, "-v", self.VOICES[voice], "-b", "1", "--stdin"],
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
            )
        except OSError as exc:
            raise VoiceError("Não foi possível iniciar a síntese de voz.") from exc
        self._set_process(process)
        try:
            try:
                process.communicate(input=text[:self.MAX_SPEECH], timeout=60)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                process.communicate()
                raise VoiceError("A síntese de voz excedeu o tempo limite.") from exc
            if process.returncode != 0:
                raise VoiceError("Não foi possível reproduzir o áudio local.")
        finally:
            self._clear_process(process)


class LocalRecognizer(_StoppableProcess):
    """Escuta uma fala com detecção de pausa pelo Vosk, sem serviço remoto."""

    SAMPLE_RATE = 16000
    DURATION = 8
    STREAM_LIMIT = 30

    def __init__(self, model_path: str | Path | None = None):
        super().__init__()
        self.model_path = Path(model_path or settings.voice_model_path or (
            settings.data_dir / "voice" / "vosk-model-small-pt-0.3"
        )).expanduser()
        self._model = None

    def _load_model(self):
        if not self.model_path.is_dir():
            raise VoiceError(
                "Modelo Vosk local ausente. Configure NEXUS_VOSK_MODEL_PATH."
            )
        try:
            from vosk import Model
        except ImportError as exc:
            raise VoiceError("Instale o extra Python de voz: pip install -e '.[voice]'.") from exc
        if self._model is None:
            try:
                self._model = Model(str(self.model_path))
            except Exception as exc:
                raise VoiceError("Não foi possível abrir o modelo Vosk local.") from exc
        return self._model

    def recognize(self) -> str:
        model = self._load_model()
        binary = shutil.which("arecord")
        if binary is None:
            raise VoiceError("Instale alsa-utils para usar o microfone.")
        try:
            process = subprocess.Popen(
                [binary, "-q", "-d", str(self.DURATION), "-f", "S16_LE",
                 "-r", str(self.SAMPLE_RATE), "-c", "1", "-t", "wav"],
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
            )
        except OSError as exc:
            raise VoiceError("Não foi possível iniciar a gravação local.") from exc
        self._set_process(process)
        try:
            try:
                audio, _ = process.communicate(timeout=self.DURATION + 5)
            except subprocess.TimeoutExpired as exc:
                process.kill()
                process.communicate()
                raise VoiceError("A gravação excedeu o tempo limite.") from exc
            if process.returncode != 0:
                raise VoiceError("Não foi possível capturar áudio do microfone.")
        finally:
            self._clear_process(process)

        try:
            with wave.open(io.BytesIO(audio), "rb") as recording:
                if (recording.getnchannels(), recording.getsampwidth(),
                    recording.getframerate(), recording.getcomptype()) != (
                    1, 2, self.SAMPLE_RATE, "NONE"
                ):
                    raise VoiceError("Formato de áudio incompatível com o modelo.")
                from vosk import KaldiRecognizer

                decoder = KaldiRecognizer(model, self.SAMPLE_RATE)
                segments = []
                while frames := recording.readframes(4000):
                    if decoder.AcceptWaveform(frames):
                        segments.append(json.loads(decoder.Result()).get("text", ""))
                segments.append(json.loads(decoder.FinalResult()).get("text", ""))
        except (wave.Error, EOFError, ValueError, json.JSONDecodeError) as exc:
            raise VoiceError("Áudio ou transcrição inválidos.") from exc

        text = " ".join(part.strip() for part in segments if isinstance(part, str)).strip()
        if not text:
            raise VoiceError("Não reconheci fala. Tente novamente.")
        return text[:4000]

    def recognize_continuous(self, cancelled: Callable[[], bool] | None = None) -> str:
        """Retorna uma fala completa, ou vazio após silêncio/cancelamento.

        O processo de captura tem limite de tempo; a janela inicia outra captura
        após silêncio. O Vosk decide o fim de cada fala pelo intervalo de pausa.
        """
        cancelled = cancelled or (lambda: False)
        model = self._load_model()
        binary = shutil.which("arecord")
        if binary is None:
            raise VoiceError("Instale alsa-utils para usar o microfone.")
        if cancelled():
            return ""
        try:
            from vosk import KaldiRecognizer
            decoder = KaldiRecognizer(model, self.SAMPLE_RATE)
            process = subprocess.Popen(
                [binary, "-q", "-d", str(self.STREAM_LIMIT), "-f", "S16_LE",
                 "-r", str(self.SAMPLE_RATE), "-c", "1", "-t", "raw"],
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise VoiceError("Não foi possível iniciar a gravação local.") from exc
        self._set_process(process)
        try:
            if cancelled():
                return ""
            while not cancelled():
                frames = process.stdout.read(8000)
                if not frames:
                    break
                if decoder.AcceptWaveform(frames):
                    text = json.loads(decoder.Result()).get("text", "")
                    if isinstance(text, str) and text.strip():
                        return text.strip()[:4000]
            if cancelled():
                return ""
            if process.wait(timeout=3) != 0:
                raise VoiceError("Não foi possível capturar áudio do microfone.")
            text = json.loads(decoder.FinalResult()).get("text", "")
            return text.strip()[:4000] if isinstance(text, str) else ""
        except (ValueError, json.JSONDecodeError) as exc:
            raise VoiceError("Áudio ou transcrição inválidos.") from exc
        except subprocess.TimeoutExpired as exc:
            raise VoiceError("A gravação excedeu o tempo limite.") from exc
        finally:
            if process.poll() is None:
                try:
                    process.terminate()
                except ProcessLookupError:
                    pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=2)
            self._clear_process(process)
