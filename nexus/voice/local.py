"""Áudio local: saída eSpeak/Piper e reconhecimento Vosk via PipeWire ou ALSA."""

from array import array
import io
import json
import os
import re
import signal
import select
import shutil
import subprocess
import sys
import tempfile
from time import monotonic
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
        self._paused = False

    def _set_process(self, process):
        with self._lock:
            self._process = process
            self._paused = False

    def _clear_process(self, process):
        with self._lock:
            if self._process is process:
                self._process = None
                self._paused = False

    def stop(self) -> None:
        with self._lock:
            process = self._process
            if process is not None and process.poll() is None:
                try:
                    if self._paused:
                        # SIGTERM may remain pending for a stopped Linux process.
                        process.send_signal(signal.SIGCONT)
                        self._paused = False
                    process.terminate()
                except (ProcessLookupError, OSError):
                    pass


class LocalSpeaker(_StoppableProcess):
    """Vozes locais PT-BR; Piper/RHVoice quando presentes, eSpeak como reserva."""

    def pause(self) -> bool:
        """Pause only the current owned Linux subprocess (never system audio)."""
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None or self._paused:
                return False
            try:
                process.send_signal(signal.SIGSTOP)
            except (ProcessLookupError, OSError, AttributeError):
                return False
            self._paused = True
            return True

    def resume(self) -> bool:
        """Resume the same owned subprocess without replaying the message."""
        with self._lock:
            process = self._process
            if process is None or process.poll() is not None or not self._paused:
                return False
            try:
                process.send_signal(signal.SIGCONT)
            except (ProcessLookupError, OSError, AttributeError):
                return False
            self._paused = False
            return True

    VOICES = {"Feminina": "pt-br+f3", "Masculina": "pt-br+m3"}
    MAX_SPEECH = 2400
    NEURAL_MODEL = "pt_BR-faber-medium"

    @classmethod
    def _spoken_text(cls, text: str) -> str:
        """Give local engines conversational punctuation without altering the chat."""
        clean = re.sub(r"\s+", " ", text[:cls.MAX_SPEECH - 1]).strip()
        if clean and clean[-1].isalnum():
            clean += "."
        return clean

    @classmethod
    def neural_model_path(cls) -> Path:
        return settings.data_dir / "voice" / "piper" / (cls.NEURAL_MODEL + ".onnx")

    @classmethod
    def neural_voice_ready(cls) -> bool:
        model = cls.neural_model_path()
        return bool(model.is_file() and model.with_suffix(".onnx.json").is_file()
                    and (Path(sys.executable).with_name("piper").is_file()
                         or shutil.which("piper")))

    @staticmethod
    def female_voice_ready() -> bool:
        return bool(shutil.which("RHVoice-test") and
                    Path("/usr/share/RHVoice/voices/Leticia-F123").is_dir())

    def _speak_natural(
        self, text: str, cancelled: Callable[[], bool] | None, *, voice: str,
        speed: float = 1.0, volume: int = 100,
    ) -> None:
        managed_binary = Path(sys.executable).with_name("piper")
        if voice == "Masculina":
            binary = (str(managed_binary) if managed_binary.is_file()
                      else shutil.which("piper"))
            model = self.neural_model_path()
            if binary is None or not model.is_file() or not model.with_suffix(".onnx.json").is_file():
                raise VoiceError("Voz neural Piper indisponível. Reinstale o assistente.")
        else:
            binary = shutil.which("RHVoice-test")
            if binary is None or not self.female_voice_ready():
                raise VoiceError("Voz feminina RHVoice indisponível.")
        player = shutil.which("pw-play") or shutil.which("aplay")
        if player is None:
            raise VoiceError("Instale PipeWire ou alsa-utils para reproduzir áudio.")
        with tempfile.TemporaryDirectory(prefix="nexus-speech-") as temp:
            wav = Path(temp) / "reply.wav"
            synth = ([binary, "--model", str(model), "--output_file", str(wav),
                      "--length-scale", "1.05"]
                     if voice == "Masculina" else
                     [binary, "-p", "Leticia-F123", "-o", str(wav)])
            playback = wav
            commands = [(synth, self._spoken_text(text))]
            if speed != 1.0 or volume != 100:
                converter = shutil.which("ffmpeg")
                if converter is None:
                    raise VoiceError(
                        "Ajuste de velocidade/volume requer FFmpeg local instalado."
                    )
                playback = Path(temp) / "adjusted.wav"
                # No shell; filters consist exclusively of validated numeric values.
                audio_filter = f"atempo={speed:.2f},volume={volume / 100:.2f}"
                commands.append((
                    [converter, "-nostdin", "-hide_banner", "-loglevel", "error",
                     "-y", "-i", str(wav), "-af", audio_filter, str(playback)],
                    None,
                ))
            commands.append((
                [player, str(playback)] if Path(player).name == "pw-play"
                else [player, "-q", str(playback)], None,
            ))
            for command, payload in commands:
                if cancelled is not None and cancelled():
                    return
                if payload is None:
                    source = (playback if command[0] == player else wav)
                    if not source.is_file() or source.stat().st_size < 44:
                        raise VoiceError("A voz neural não produziu áudio válido.")
                try:
                    process = subprocess.Popen(
                        command, stdin=subprocess.PIPE if payload is not None else subprocess.DEVNULL,
                        stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                        text=payload is not None, encoding="utf-8" if payload is not None else None,
                    )
                except OSError as exc:
                    raise VoiceError("Não foi possível iniciar a síntese ou reprodução local.") from exc
                self._set_process(process)
                try:
                    if cancelled is not None and cancelled():
                        self.stop()
                    try:
                        process.communicate(input=payload if process.poll() is None else None,
                                            timeout=60)
                    except subprocess.TimeoutExpired as exc:
                        process.kill()
                        process.communicate()
                        raise VoiceError("A voz neural excedeu o tempo limite.") from exc
                    if cancelled is not None and cancelled():
                        return
                    if process.returncode != 0:
                        raise VoiceError("A síntese ou reprodução neural falhou.")
                finally:
                    self._clear_process(process)

    def speak(
        self, text: str, voice: str = "Feminina",
        *, cancelled: Callable[[], bool] | None = None,
        speed: float = 1.0, volume: int = 100,
    ) -> None:
        if (type(speed) not in (int, float) or not 0.75 <= speed <= 1.25
                or type(volume) is not int or not 50 <= volume <= 150):
            raise VoiceError("Velocidade/volume de voz fora dos limites permitidos.")
        if voice not in self.VOICES:
            raise VoiceError("Seleção de voz inválida.")
        if not isinstance(text, str) or not text.strip():
            raise VoiceError("Não há texto para falar.")
        if cancelled is not None and cancelled():
            return
        if voice == "Masculina" and self.neural_voice_ready():
            self._speak_natural(text, cancelled, voice=voice, speed=speed, volume=volume)
            return
        if voice == "Feminina" and self.female_voice_ready():
            self._speak_natural(text, cancelled, voice=voice, speed=speed, volume=volume)
            return
        binary = shutil.which("espeak-ng")
        if binary is None:
            raise VoiceError("Instale eSpeak NG para ouvir as respostas.")
        if cancelled is not None and cancelled():
            return
        try:
            process = subprocess.Popen(
                ([binary, "-v", self.VOICES[voice], "-b", "1"]
                 + (["-s", str(round(175 * speed))] if speed != 1.0 else [])
                 + (["-a", str(volume)] if volume != 100 else [])
                 + ["--stdin"]),
                stdin=subprocess.PIPE, stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE, text=True, encoding="utf-8",
            )
        except OSError as exc:
            raise VoiceError("Não foi possível iniciar a síntese de voz.") from exc
        self._set_process(process)
        try:
            # A stop can arrive while Popen is starting, before stop() sees
            # the process. Recheck after registration and never send the text.
            if cancelled is not None and cancelled():
                self.stop()
                try:
                    process.communicate(timeout=5)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.communicate()
                return
            try:
                process.communicate(input=self._spoken_text(text), timeout=60)
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
    END_OF_SPEECH_SECONDS = 1.2
    MAX_UNDECODABLE_SECONDS = 8.0

    def __init__(self, model_path: str | Path | None = None):
        super().__init__()
        self.model_path = Path(model_path or settings.voice_model_path or (
            settings.data_dir / "voice" / "vosk-model-small-pt-0.3"
        )).expanduser()
        self._model = None
        self.audio_backend = "auto"  # Per-recognizer setting, never modifies OS audio.

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
                from vosk import SetLogLevel
                SetLogLevel(-1)
            except ImportError:
                pass  # Mocked or older Vosk; recognition still works.
            try:
                self._model = Model(str(self.model_path))
            except Exception as exc:
                raise VoiceError("Não foi possível abrir o modelo Vosk local.") from exc
        return self._model

    @classmethod
    def capture_command(cls, *, duration: int = 0, wav: bool = False,
                        backend: str | None = None) -> list[str]:
        """Use the active desktop's PipeWire default input before ALSA's default."""
        selected = backend if backend is not None else os.environ.get("NEXUS_AUDIO_INPUT", "auto")
        if selected not in ("auto", "pipewire", "alsa"):
            raise VoiceError("Entrada de áudio deve ser automática, PipeWire ou ALSA.")
        runtime = os.environ.get("XDG_RUNTIME_DIR", "")
        pipewire = shutil.which("pw-record")
        ready = bool(pipewire and runtime and Path(runtime, "pipewire-0").is_socket())
        if selected == "pipewire" and not ready:
            raise VoiceError("PipeWire não está disponível nesta sessão Ubuntu.")
        if (ready and selected != "alsa" and not wav):
            # Newer PipeWire writes an AU container to stdout by default.
            # Vosk consumes headerless signed 16-bit LE mono PCM instead.
            return [pipewire, "--raw", "--rate", str(cls.SAMPLE_RATE), "--channels", "1",
                    "--format", "s16", "-"]
        binary = shutil.which("arecord")
        if binary is None:
            raise VoiceError("Instale alsa-utils ou PipeWire para usar o microfone.")
        return [binary, "-q", "-d", str(duration or cls.STREAM_LIMIT),
                "-f", "S16_LE", "-r", str(cls.SAMPLE_RATE), "-c", "1",
                "-t", "wav" if wav else "raw"]

    @staticmethod
    def peak_level(frames: bytes) -> int:
        """Peak percentage, used only for local feedback, never retained."""
        samples = array("h")
        samples.frombytes(frames[:len(frames) // 2 * 2])
        if sys.byteorder != "little":
            samples.byteswap()
        return min(100, int(100 * max((abs(value) for value in samples), default=0) / 32768))

    def recognize(self) -> str:
        model = self._load_model()
        command = self.capture_command(duration=self.DURATION, wav=True)
        try:
            process = subprocess.Popen(
                command,
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

    def recognize_continuous(
        self, cancelled: Callable[[], bool] | None = None,
        on_audio_level: Callable[[int], None] | None = None,
    ) -> str:
        """Retorna uma fala completa, ou vazio após silêncio/cancelamento.

        O processo de captura tem limite de tempo; a janela inicia outra captura
        após silêncio. O Vosk decide o fim de cada fala pelo intervalo de pausa.
        """
        cancelled = cancelled or (lambda: False)
        model = self._load_model()
        command = (self.capture_command(backend=self.audio_backend)
                   if self.audio_backend != "auto" else self.capture_command())
        if cancelled():
            return ""
        try:
            from vosk import KaldiRecognizer
            decoder = KaldiRecognizer(model, self.SAMPLE_RATE)
            process = subprocess.Popen(
                command,
                stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
            )
        except OSError as exc:
            raise VoiceError("Não foi possível iniciar a gravação local.") from exc
        self._set_process(process)
        try:
            if cancelled():
                return ""
            deadline = monotonic() + self.STREAM_LIMIT
            next_level = 0.0
            speech_started = False
            speech_started_at = 0.0
            last_voice = 0.0
            partial_text = ""
            last_partial_change = 0.0
            # PipeWire streams have no fixed end time. Buffered .read(8000)
            # can stall while waiting for exactly 8000 bytes, ignoring pause,
            # timeout or a changed input source. A pollable Linux fd permits
            # short reads and checking cancellation every quarter-second.
            fd = None
            try:
                fd = process.stdout.fileno()
            except (AttributeError, OSError, io.UnsupportedOperation):
                pass  # Test doubles/older APIs without file descriptors.
            while not cancelled() and monotonic() < deadline:
                if fd is not None:
                    try:
                        readable, _, _ = select.select([fd], [], [], 0.25)
                        if not readable:
                            if process.poll() is not None:
                                break
                            # A quiet PipeWire stream can stop providing
                            # readable bytes after speech. Check the pause
                            # timer even when select() times out.
                            now = monotonic()
                            if speech_started and now - last_voice >= self.END_OF_SPEECH_SECONDS:
                                text = json.loads(decoder.FinalResult()).get("text", "")
                                return (text.strip() if isinstance(text, str) and text.strip()
                                        else partial_text)[:4000]
                            if partial_text and now - last_partial_change >= 2.5:
                                text = json.loads(decoder.FinalResult()).get("text", "")
                                return (text.strip() if isinstance(text, str) and text.strip()
                                        else partial_text)[:4000]
                            continue
                        frames = os.read(fd, 4096)
                    except (OSError, ValueError) as exc:
                        if cancelled():
                            return ""
                        raise VoiceError(
                            "Fluxo de áudio interrompido. Confira a entrada "
                            "PipeWire/ALSA e retome a escuta."
                        ) from exc
                else:
                    frames = process.stdout.read(8000)
                if not frames:
                    break
                now = monotonic()
                level = self.peak_level(frames)
                if on_audio_level is not None and monotonic() >= next_level:
                    on_audio_level(level)
                    # Refresh the on-screen activity frames ~4 times/second.
                    # Peak feedback is independent of Vosk word recognition.
                    next_level = monotonic() + 0.25
                if level >= 3:
                    if not speech_started:
                        speech_started_at = now
                    speech_started = True
                    last_voice = now
                if decoder.AcceptWaveform(frames):
                    text = json.loads(decoder.Result()).get("text", "")
                    if isinstance(text, str) and text.strip():
                        return text.strip()[:4000]
                partial_result = getattr(decoder, "PartialResult", None)
                if partial_result is not None:
                    partial = json.loads(partial_result()).get("partial", "")
                    if isinstance(partial, str) and partial.strip() and partial != partial_text:
                        partial_text = partial
                        last_partial_change = now
                # Some microphones and Vosk models never emit an endpoint for
                # short questions. Flush after a measured pause instead of
                # leaving the user waiting for the 30 second stream limit.
                if speech_started and now - last_voice >= self.END_OF_SPEECH_SECONDS:
                    text = json.loads(decoder.FinalResult()).get("text", "")
                    if isinstance(text, str) and text.strip():
                        return text.strip()[:4000]
                    return partial_text[:4000]
                # A noisy default input can stay above the peak threshold even
                # through pauses. A stable recognized partial is still useful.
                if partial_text and now - last_partial_change >= 2.5:
                    text = json.loads(decoder.FinalResult()).get("text", "")
                    return (text.strip() if isinstance(text, str) and text.strip()
                            else partial_text)[:4000]
                # A constant noisy input must not occupy the microphone for
                # thirty seconds when Vosk has no partial transcription.
                if (speech_started and not partial_text
                        and now - speech_started_at >= self.MAX_UNDECODABLE_SECONDS):
                    text = json.loads(decoder.FinalResult()).get("text", "")
                    return text.strip()[:4000] if isinstance(text, str) else ""
            if cancelled():
                return ""
            if process.poll() is not None and process.returncode != 0:
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
