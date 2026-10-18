"""Read a generated local image for a bounded, Nexus-owned desktop preview."""

import io
import os
import warnings
from pathlib import Path

from nexus.security.paths import PathSecurity


MAX_PREVIEW_BYTES = 25 * 1024 * 1024
MAX_PREVIEW_PIXELS = 8_000_000
PREVIEW_SIZE = (720, 480)
PREVIEW_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})


def load_image_preview(path: str, policy: PathSecurity):
    """Return an oriented thumbnail without trusting the extension or symlinks.

    The file is opened through the same anchored home policy as local tools.
    The caller owns the returned in-memory Pillow image; no file is written.
    """
    from PIL import Image, ImageOps

    if Path(path).suffix.lower() not in PREVIEW_EXTENSIONS:
        raise ValueError("Formato de prévia não suportado.")
    with policy.open_regular_file(path) as (fd, _):
        if os.fstat(fd).st_size > MAX_PREVIEW_BYTES:
            raise ValueError("Imagem muito grande para a prévia.")
        content = bytearray()
        while len(content) <= MAX_PREVIEW_BYTES:
            part = os.read(fd, min(65536, MAX_PREVIEW_BYTES + 1 - len(content)))
            if not part:
                break
            content.extend(part)
        if len(content) > MAX_PREVIEW_BYTES:
            raise ValueError("Imagem muito grande para a prévia.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(content)) as raw:
                if (raw.format not in {"PNG", "JPEG", "WEBP"} or
                        raw.width > 4096 or raw.height > 4096 or
                        raw.width * raw.height > MAX_PREVIEW_PIXELS):
                    raise ValueError("Dimensões inválidas para a prévia.")
                raw.load()
                oriented = ImageOps.exif_transpose(raw)
                image = oriented.convert("RGBA" if "A" in oriented.getbands() or
                                         "transparency" in oriented.info else "RGB")
    except (Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise ValueError("Dimensões inválidas para a prévia.") from exc
    image.thumbnail(PREVIEW_SIZE, Image.Resampling.LANCZOS)
    # The preview needs pixels only; never retain source metadata in the UI.
    clean = Image.new(image.mode, image.size)
    clean.paste(image)
    return clean
