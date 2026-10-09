"""Vision bounds and local-image privacy tests."""
import io

import pytest
from PIL import Image, PngImagePlugin

from nexus.config.settings import Settings
from nexus.security.paths import PathSecurity
from nexus.vision.local import LocalVision, VisionInputError, VisionError


def sample(width=32, height=32, metadata=False):
    output = io.BytesIO()
    info = PngImagePlugin.PngInfo()
    if metadata:
        info.add_text("Comment", "private-location-data")
    Image.new("RGB", (width, height), (20, 60, 90)).save(
        output, format="PNG", pnginfo=info
    )
    return output.getvalue()


def make_vision(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    policy = PathSecurity()
    policy.home = home.resolve()
    policy.protected_paths = [home / ".ssh"]
    return LocalVision(Settings(), path_security=policy), home


def test_sanitizes_metadata_and_reencodes_png():
    data = LocalVision._normalize_image(sample(metadata=True))
    assert b"private-location-data" not in data
    with Image.open(io.BytesIO(data)) as image:
        assert image.format == "PNG"
        assert image.size == (32, 32)
        assert image.info == {}


@pytest.mark.parametrize("data", [b"", b"invalid", b"\xff\xfe", b"x" * (6 * 1024 * 1024 + 1)])
def test_invalid_images_rejected(data):
    with pytest.raises(VisionInputError):
        LocalVision._normalize_image(data)


def test_maximum_dimension_denied():
    with pytest.raises(VisionInputError):
        LocalVision._normalize_image(sample(width=4097, height=1))


def test_file_inside_home_allowed_and_outside_denied(tmp_path):
    service, home = make_vision(tmp_path)
    allowed = home / "picture.png"
    allowed.write_bytes(sample())
    assert service.image_from_file(allowed).startswith(b"\x89PNG")
    outside = tmp_path / "outside.png"
    outside.write_bytes(sample())
    with pytest.raises(VisionInputError):
        service.image_from_file(outside)
    sensitive = home / ".ssh"
    sensitive.mkdir()
    (sensitive / "private.png").write_bytes(sample())
    with pytest.raises(VisionInputError):
        service.image_from_file(sensitive / "private.png")
    symlink = home / "shortcut.png"
    symlink.symlink_to(allowed)
    with pytest.raises(VisionInputError):
        service.image_from_file(symlink)


def test_file_swap_to_symlink_is_blocked(tmp_path):
    service, home = make_vision(tmp_path)
    target = home / "photo.png"
    target.write_bytes(sample())
    outside = tmp_path / "private.png"
    outside.write_bytes(sample())
    actual = service.path_security.open_regular_file

    def race(path):
        target.unlink()
        target.symlink_to(outside)
        return actual(path)

    service.path_security.open_regular_file = race
    with pytest.raises(VisionInputError):
        service.image_from_file(target)


@pytest.mark.parametrize("prompt", ["", "  ", "a\x00b", "x" * 2001])
def test_invalid_prompt_is_rejected(prompt):
    with pytest.raises(VisionInputError):
        LocalVision.validate_question(prompt)


@pytest.mark.parametrize("name", ["", " model", "a\nb", "/invalid", "x" * 130])
def test_model_identifier_is_bounded(name):
    with pytest.raises(VisionInputError):
        LocalVision.validate_model(name)


def test_local_vision_rejects_missing_image_format(tmp_path):
    service, home = make_vision(tmp_path)
    invalid = home / "notes.txt"
    invalid.write_bytes(sample())
    with pytest.raises(VisionInputError):
        service.image_from_file(invalid)
