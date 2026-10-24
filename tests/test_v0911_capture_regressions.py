"""Regression coverage for Ubuntu PipeWire, image files and V4L2 camera nodes."""

import io
from pathlib import Path

import pytest
from PIL import Image

from nexus.config.settings import Settings
from nexus.vision.local import LocalVision, VisionError, VisionInputError
import nexus.vision.local as vision_module


@pytest.mark.parametrize("format_name", ["PNG", "JPEG", "WEBP", "BMP", "GIF", "TIFF"])
def test_common_raster_formats_are_safely_normalized(format_name):
    output = io.BytesIO()
    Image.new("RGB", (12, 8), (20, 60, 90)).save(output, format=format_name)
    result = LocalVision._normalize_image(output.getvalue())
    assert result.startswith(b"\x89PNG\r\n\x1a\n")
    with Image.open(io.BytesIO(result)) as image:
        assert image.format == "PNG"
        assert image.mode == "RGB"
        assert image.size == (12, 8)
        assert not image.getexif()


def test_raster_file_extension_policy_handles_jfif_and_uppercase():
    assert ".jfif" in LocalVision.FILE_SUFFIXES
    assert ".bmp" in LocalVision.FILE_SUFFIXES
    assert ".tiff" in LocalVision.FILE_SUFFIXES
    assert ".gif" in LocalVision.FILE_SUFFIXES
    assert ".avif" in LocalVision.FILE_SUFFIXES
    assert ".PNG".lower() in LocalVision.FILE_SUFFIXES


def test_image_decoding_rejects_unknown_payload_even_if_picker_allows_all_files():
    with pytest.raises(VisionInputError):
        LocalVision._normalize_image(b"not an image")


@pytest.mark.parametrize("device_caps,expected", [
    (0x00000001, True),       # V4L2_CAP_VIDEO_CAPTURE
    (0x00001000, True),       # V4L2_CAP_VIDEO_CAPTURE_MPLANE
    (0x00800000, False),      # V4L2_CAP_META_CAPTURE (not a webcam stream)
    (0, False),
])
def test_v4l2_querycap_excludes_metadata_only_nodes(monkeypatch, device_caps, expected):
    def fake_ioctl(fd, command, capability, mutate_flag):
        assert command == 0x80685600  # VIDIOC_QUERYCAP
        capability[84:88] = (0x80000000).to_bytes(4, "little")  # DEVICE_CAPS
        capability[88:92] = device_caps.to_bytes(4, "little")
        return 0

    monkeypatch.setattr(vision_module.fcntl, "ioctl", fake_ioctl)
    # /dev/null is a character device but not a camera; mock the ioctl only.
    assert LocalVision._camera_supports_capture(Path("/dev/null")) is expected


def test_camera_inventory_filters_metadata_nodes(monkeypatch):
    monkeypatch.setattr(vision_module.glob, "glob", lambda pattern: [
        "/dev/video0", "/dev/video1", "/dev/video10", "/dev/video99",
        "/dev/video256", "/dev/video-other"
    ])
    monkeypatch.setattr(LocalVision, "_camera_supports_capture", staticmethod(
        lambda path: path.name in {"video0", "video10", "video256"}
    ))
    cameras = LocalVision.cameras()
    assert [index for index, _ in cameras] == [0, 10]


def test_camera_failure_explains_device_and_action_without_raw_ffmpeg_output(monkeypatch):
    monkeypatch.setattr(vision_module.shutil, "which", lambda name: "/usr/bin/ffmpeg")

    def fail_capture(command, **kwargs):
        raise VisionError("Não foi possível capturar imagem local.")

    monkeypatch.setattr(LocalVision, "_capture", staticmethod(fail_capture))
    with pytest.raises(VisionError, match="câmera 1.*permissões"):
        LocalVision(Settings()).camera(1)
