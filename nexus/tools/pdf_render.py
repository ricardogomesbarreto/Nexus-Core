"""Render one authorized PDF page to a new PNG via optional PdfCraft CLI.

Source contract checked against user's original pdfcraft-main ZIP:
pdfcraft-cli render <file.pdf> --page N --dpi 96 --out x.png
"""
from __future__ import annotations

import os
import shutil
import struct
import subprocess
import tempfile
import zlib
from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind
from nexus.tools.creative import _read_source, _write_new

_PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def _validate_png(data: bytes) -> None:
    if (len(data) < 57 or not data.startswith(_PNG_SIGNATURE)
            or data[12:16] != b"IHDR"):
        raise ValueError("O mecanismo local não gerou PNG válido.")
    offset, seen_image, seen_end = 8, False, False
    while offset < len(data):
        if len(data) - offset < 12:
            raise ValueError("PNG truncado.")
        length = struct.unpack_from(">I", data, offset)[0]
        end = offset + 12 + length
        if end > len(data):
            raise ValueError("Bloco PNG truncado.")
        kind = data[offset + 4:offset + 8]
        payload = data[offset + 8:end - 4]
        crc = struct.unpack_from(">I", data, end - 4)[0]
        if zlib.crc32(kind + payload) & 0xffffffff != crc:
            raise ValueError("Bloco PNG corrompido.")
        if offset == 8:
            if kind != b"IHDR" or length != 13:
                raise ValueError("Cabeçalho PNG inválido.")
            width, height = struct.unpack_from(">II", data, offset + 8)
            if not (0 < width <= 4096 and 0 < height <= 4096 and
                    width * height <= 8_000_000):
                raise ValueError("Prévia excede limites de pixels.")
        elif kind == b"IDAT":
            seen_image = True
        elif kind == b"IEND":
            if length != 0 or not seen_image or end != len(data):
                raise ValueError("Final PNG inválido.")
            seen_end = True
        offset = end
    if not seen_end:
        raise ValueError("PNG incompleto.")


class PdfRenderTool(NexusTool):
    name = "pdf_render_local"
    description = ("Renderiza uma única página PDF local autorizada em PNG novo "
                   "usando mecanismo local opcional.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True),
                FieldSpec("page", ValueKind.INTEGER)),
        resources=(ResourceSpec("source", "source"), ResourceSpec("output", "output")),
        outputs=(FieldSpec("path", ValueKind.STRING), FieldSpec("page", ValueKind.INTEGER)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),
                SensitiveResource("output", kwargs["output"]))

    def execute(self, source: str, output: str, page: int, **kwargs) -> ToolResult:
        if (type(page) is not int or not 1 <= page <= 5000 or
                Path(source).suffix.lower() != ".pdf" or
                Path(output).suffix.lower() != ".png"):
            return ToolResult(False, self.name, error="Origem PDF, PNG de saída ou página inválida.")
        executable = shutil.which("pdfcraft-cli")
        if executable is None:
            return ToolResult(False, self.name, error="Mecanismo local de PDF não instalado. Consulte --feature-check.")
        try:
            policy = self.path_security or PathSecurity()
            data = _read_source(policy, source, 20 * 1024 * 1024)
            if not data.startswith(b"%PDF-"):
                raise ValueError("O arquivo não tem assinatura de PDF.")
            with tempfile.TemporaryDirectory(prefix="nexus-pdf-page-") as location:
                work = Path(location)
                incoming, outgoing = work / "entrada.pdf", work / "pagina.png"
                incoming.write_bytes(data)
                status = subprocess.run(
                    [executable, "render", str(incoming), "--page", str(page),
                     "--dpi", "96", "--out", str(outgoing)],
                    cwd=location, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=90, check=False,
                )
                if status.returncode != 0:
                    raise ValueError("O mecanismo local não renderizou a página solicitada.")
                staging_policy = PathSecurity()
                staging_policy.home = work
                staging_policy.protected_paths = []
                png = _read_source(staging_policy, str(outgoing), 25 * 1024 * 1024)
                _validate_png(png)
                saved = _write_new(policy, output, png)
            return ToolResult(True, self.name, data={"path": saved, "page": page})
        except (OSError, PermissionError, ValueError, subprocess.TimeoutExpired) as exc:
            return ToolResult(False, self.name, error=f"Prévia PDF não concluída: {type(exc).__name__}.")
