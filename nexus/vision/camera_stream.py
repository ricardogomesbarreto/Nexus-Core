"""Bounded, in-memory V4L2 preview. Frames are never written to disk."""

import os
import select
import shutil
import subprocess
import tempfile
from threading import Event, Lock, Thread
from time import monotonic

from nexus.vision.local import LocalVision, VisionError, VisionInputError


class CameraStream:
    """Keep only the newest JPEG from one explicitly authorized webcam."""

    MAX_FRAME_BYTES = 2 * 1024 * 1024

    def __init__(self, index: int):
        if type(index) is not int or not 0 <= index <= LocalVision.MAX_CAMERA_INDEX:
            raise VisionInputError("Índice de câmera inválido.")
        self.index = index
        self._stop = Event()
        self._lock = Lock()
        self._process = None
        self._thread = None
        self._frame: bytes | None = None
        self._frame_at = 0.0
        self._sequence = 0
        self._error: str | None = None
        self._diagnostics = None

    def start(self) -> None:
        if self._process is not None or self._stop.is_set():
            raise VisionError("A câmera já foi iniciada ou encerrada.")
        binary = shutil.which("ffmpeg")
        if binary is None:
            raise VisionError("Transmissão da câmera exige FFmpeg.")
        try:
            # An anonymous file avoids both a blocked stderr pipe and losing
            # FFmpeg's reason when a webcam refuses the requested stream.
            self._diagnostics = tempfile.TemporaryFile(mode="w+b")
            self._process = subprocess.Popen(
                [binary, "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-f", "video4linux2", "-i", f"/dev/video{self.index}",
                 "-vf", "fps=5,scale=640:-2", "-f", "image2pipe",
                 "-vcodec", "mjpeg", "pipe:1"],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=self._diagnostics, bufsize=0,
            )
        except OSError as exc:
            if self._diagnostics is not None:
                self._diagnostics.close()
            raise VisionError("Não foi possível iniciar a câmera local. Confira FFmpeg e permissões.") from exc
        self._thread = Thread(target=self._read_frames, name="nexus-camera", daemon=True)
        self._thread.start()

    def _read_frames(self) -> None:
        process = self._process
        buffer = bytearray()
        frame_deadline = monotonic() + 12
        try:
            fd = process.stdout.fileno()
            while not self._stop.is_set():
                if monotonic() > frame_deadline:
                    with self._lock:
                        self._error = "A câmera não enviou quadros por 12 segundos. Confira o dispositivo."
                    break
                readable, _, _ = select.select([fd], [], [], 0.25)
                if not readable:
                    if process.poll() is not None:
                        break
                    continue
                chunk = os.read(fd, 32768)
                if not chunk:
                    break
                buffer.extend(chunk)
                while buffer and not self._stop.is_set():
                    start = buffer.find(b"\xff\xd8")
                    if start < 0:
                        # The start marker may straddle two OS reads.
                        tail = buffer[-1:] if buffer[-1] == 0xff else b""
                        buffer.clear()
                        buffer.extend(tail)
                        break
                    if start:
                        del buffer[:start]
                    end = buffer.find(b"\xff\xd9", 2)
                    if end < 0:
                        if len(buffer) > self.MAX_FRAME_BYTES:
                            buffer.clear()
                        break
                    frame = bytes(buffer[:end + 2])
                    del buffer[:end + 2]
                    if len(frame) <= self.MAX_FRAME_BYTES:
                        with self._lock:
                            # stop() may return while this worker is still
                            # unwinding. Never publish a private frame then.
                            if self._stop.is_set():
                                break
                            self._frame = frame
                            self._frame_at = monotonic()
                            self._sequence += 1
                        frame_deadline = monotonic() + 12
            if not self._stop.is_set():
                with self._lock:
                    if self._error is None:
                        self._error = self._exit_error()
        except (OSError, ValueError):
            if not self._stop.is_set():
                with self._lock:
                    self._error = "Falha ao ler a câmera local. Confira se ela está em uso."
        finally:
            if process.poll() is None:
                process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait(timeout=2)
            process.stdout.close()
            if self._diagnostics is not None:
                self._diagnostics.close()

    def _exit_error(self) -> str:
        self._diagnostics.seek(0)
        message = self._diagnostics.read(8192).decode("utf-8", "replace").lower()
        if "permission denied" in message:
            return "Acesso à câmera negado. Confira as permissões de /dev/video e a sessão do usuário."
        if "device or resource busy" in message:
            return "A câmera está em uso por outro aplicativo. Feche-o e tente novamente."
        if "no such file" in message:
            return "A câmera foi desconectada ou o dispositivo /dev/video não está disponível."
        if "invalid argument" in message or "not supported" in message:
            return "O formato de vídeo da câmera não é compatível com a captura atual. Confira os formatos V4L2."
        return "A transmissão da câmera parou. Confira o dispositivo, formato e permissões."

    def latest(self, *, max_age: float | None = None) -> tuple[int, bytes | None, str | None]:
        with self._lock:
            if self._stop.is_set():
                return self._sequence, None, None
            if self._error is not None:
                return self._sequence, self._frame, self._error
            if (max_age is not None and self._frame is not None
                    and monotonic() - self._frame_at > max_age):
                return (self._sequence, None,
                        "A câmera não enviou uma imagem recente. Aguarde o vídeo atualizar "
                        "ou desligue e ligue a câmera.")
            return self._sequence, self._frame, self._error

    def stop(self) -> None:
        self._stop.set()
        process = self._process
        if process is not None and process.poll() is None:
            try:
                process.terminate()
            except ProcessLookupError:
                pass
        if self._thread is not None:
            self._thread.join(timeout=0.3)
        with self._lock:
            self._frame = None
            self._frame_at = 0.0
