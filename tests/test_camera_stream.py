"""A webcam preview reads only bounded frames and stops on request."""

import os
import io
import time

import pytest

from nexus.vision.camera_stream import CameraStream
from nexus.vision.local import VisionInputError
import nexus.vision.camera_stream as camera_module


@pytest.mark.parametrize("index", [-1, 256, True, "0"])
def test_invalid_camera_never_opens_a_process(index):
    with pytest.raises(VisionInputError):
        CameraStream(index)


def test_live_stream_keeps_only_latest_frame_and_stops(monkeypatch):
    read_fd, write_fd = os.pipe()

    class Process:
        def __init__(self):
            self.stdout = os.fdopen(read_fd, "rb", buffering=0)
            self.stopped = False
        def poll(self): return 0 if self.stopped else None
        def terminate(self): self.stopped = True
        def wait(self, timeout=None): return 0
        def kill(self): self.stopped = True

    process = Process()
    commands = []
    monkeypatch.setattr(camera_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")
    monkeypatch.setattr(camera_module.subprocess, "Popen",
                        lambda args, **kwargs: commands.append(args) or process)
    stream = CameraStream(10)
    stream.start()
    try:
        assert "/dev/video10" in commands[0]
        assert "pipe:1" in commands[0]
        os.write(write_fd, b"junk\xff")
        time.sleep(0.05)
        os.write(write_fd, b"\xd8first\xff\xd9\xff\xd8last\xff\xd9")
        deadline = time.monotonic() + 2
        while stream.latest()[0] < 2 and time.monotonic() < deadline:
            time.sleep(0.01)
        assert stream.latest() == (2, b"\xff\xd8last\xff\xd9", None)
    finally:
        stream.stop()
        os.close(write_fd)
    assert process.stopped
    assert stream.latest()[1] is None


@pytest.mark.parametrize("diagnostic,expected", [
    (b"Device or resource busy", "uso por outro aplicativo"),
    (b"Permission denied", "Acesso à câmera negado"),
    (b"Invalid argument", "formato de vídeo"),
])
def test_ffmpeg_error_is_reported_without_exposing_stderr(diagnostic, expected):
    stream = CameraStream(0)
    stream._diagnostics = io.BytesIO(diagnostic)
    assert expected in stream._exit_error()
    assert diagnostic.decode() not in stream._exit_error()


def test_stalled_camera_never_presents_an_old_frame_as_live(monkeypatch):
    stream = CameraStream(0)
    stream._sequence = 3
    stream._frame = b"old-private-frame"
    stream._frame_at = 100.0
    monkeypatch.setattr(camera_module, "monotonic", lambda: 105.0)
    assert stream.latest() == (3, b"old-private-frame", None)
    sequence, frame, error = stream.latest(max_age=3.0)
    assert sequence == 3 and frame is None
    assert "não enviou uma imagem recente" in error
    stream._frame_at = 104.0
    assert stream.latest(max_age=3.0) == (3, b"old-private-frame", None)
