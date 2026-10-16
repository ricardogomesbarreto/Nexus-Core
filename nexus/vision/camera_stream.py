"""Bounded, in-memory V4L2 preview. Frames are never written to disk."""

import os
import select
import shutil
import subprocess
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
        self._sequence = 0
        self._error: str | None = None

    def start(self) -> None:
        if self._process is not None or self._stop.is_set():
            raise VisionError("A câmera já foi iniciada ou encerrada.")
        binary = shutil.which("ffmpeg")
        if binary is None:
            raise VisionError("Transmissão da câmera exige FFmpeg.")
        try:
            self._process = subprocess.Popen(
                [binary, "-hide_banner", "-loglevel", "error", "-nostdin",
                 "-f", "video4linux2", "-i", f"/dev/video{self.index}",
                 "-vf", "fps=5,scale=640:-2", "-f", "image2pipe",
                 "-vcodec", "mjpeg", "pipe:1"],
                stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, bufsize=0,
            )
        except OSError as exc:
            raise VisionError("Não foi possível iniciar a câmera local.") from exc
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
                while buffer:
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
                            self._frame = frame
                            self._sequence += 1
                        frame_deadline = monotonic() + 12
            if not self._stop.is_set():
                with self._lock:
                    if self._error is None:
                        self._error = "A transmissão da câmera parou. Confira o dispositivo e as permissões."
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

    def latest(self) -> tuple[int, bytes | None, str | None]:
        with self._lock:
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
