"""Bounded, private color summary of an authorized local photo."""

from __future__ import annotations

import io
from pathlib import Path
import warnings

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind
from nexus.tools.creative import _read_source


class ImageColorsTool(NexusTool):
    name = "image_colors_local"
    description = ("Analisa cores e luminosidade de uma foto local autorizada, "
                   "sem criar arquivos, enviar dados ou manter a imagem em memória.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),),
        resources=(ResourceSpec("source", "source"),),
        outputs=(FieldSpec("width", ValueKind.INTEGER), FieldSpec("height", ValueKind.INTEGER),
                 FieldSpec("brightness", ValueKind.INTEGER), FieldSpec("dark_percent", ValueKind.INTEGER),
                 FieldSpec("light_percent", ValueKind.INTEGER)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),)

    def execute(self, source: str, **kwargs) -> ToolResult:
        try:
            from PIL import Image, ImageOps, ImageStat, UnidentifiedImageError
        except ImportError:
            return ToolResult(False, self.name, error="Análise de cores indisponível: Pillow não instalado.")
        try:
            if Path(source).suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
                raise ValueError("Formato de imagem não suportado.")
            policy = self.path_security or PathSecurity()
            data = _read_source(policy, source, 12 * 1024 * 1024)
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as picture:
                    if (picture.format not in {"PNG", "JPEG", "WEBP"}
                            or picture.width > 4096 or picture.height > 4096
                            or picture.width * picture.height > 8_000_000):
                        raise ValueError("Imagem excede o limite local.")
                    picture.load()
                    width, height = picture.size
                    # Use the image's grayscale histogram; no pixels, filenames,
                    # metadata or histogram buckets leave this local action.
                    gray = ImageOps.grayscale(picture.convert("RGB"))
                    histogram = gray.histogram()
                    mean = ImageStat.Stat(gray).mean[0]
                    pixels = width * height
                    result = {"width": width, "height": height,
                              "brightness": round(mean),
                              "dark_percent": round(100 * sum(histogram[:64]) / pixels),
                              "light_percent": round(100 * sum(histogram[192:]) / pixels)}
            return ToolResult(True, self.name, data=result)
        except (OSError, PermissionError, ValueError, Image.DecompressionBombWarning,
                UnidentifiedImageError, Image.DecompressionBombError) as exc:
            return ToolResult(False, self.name,
                              error=f"Análise de cores não concluída: {type(exc).__name__}.")
