"""Optional consent-gated JSON metadata from official Craft CLI commands.

Verified against user-supplied original ZIP sources: PhotoCraft, WordCraft
and PdfCraft all provide a 'info <file>' command with JSON on stdout.
Do not disclose document strings, paths, contents, layer or author names.
"""
from __future__ import annotations

import json
import shutil
import subprocess
import tempfile
from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind
from nexus.tools.creative import _read_source

_MAX_JSON_BYTES = 512 * 1024
_INPUT_LIMIT = 20 * 1024 * 1024
_FIELDS = {
    "image": ("width", "height", "depth", "channels", "layers"),
    "document": ("pages", "pageCount", "page_count", "words", "wordCount", "paragraphs", "characters"),
    "pdf": ("pages", "bookmarks", "annotations", "fields", "links", "layers",
            "attachments", "transitions", "encrypted", "tagged", "javascript"),
}
_ALLOWED_EXT = {
    "image": frozenset({".png", ".jpg", ".jpeg", ".webp", ".psd", ".pcraft", ".tif", ".tiff"}),
    "document": frozenset({".docx", ".odt", ".rtf", ".md", ".txt"}),
    "pdf": frozenset({".pdf"}),
}
_BIN = {"image": "photocraft-cli", "document": "wordcraft-cli", "pdf": "pdfcraft-cli"}


def _safe_summary(kind: str, output: bytes) -> str:
    """Allow only bounded numeric and boolean fields, never free text."""
    if not output or len(output) > _MAX_JSON_BYTES:
        raise ValueError("Resposta JSON ausente ou excessiva.")
    document = json.loads(output.decode("utf-8"))
    if type(document) is not dict:
        raise ValueError("Resposta do CLI não é objeto JSON.")
    detail = []
    for key in _FIELDS[kind]:
        value = document.get(key)
        if type(value) is bool:
            detail.append(f"{key}={'sim' if value else 'não'}")
        elif type(value) is int and 0 <= value <= 100_000_000:
            detail.append(f"{key}={value}")
        elif key == "layers" and type(value) is list and len(value) <= 100_000:
            detail.append(f"{key}={len(value)}")
    if not detail:
        raise ValueError("O CLI não retornou campos de metadados reconhecidos.")
    return "; ".join(detail) + ". Conteúdo textual e nomes privados foram omitidos."


class CraftInspectTool(NexusTool):
    name = "craft_inspect_local"
    description = ("Consulta somente metadados de imagem, documento ou PDF "
                   "por CLI Craft local opcional; sem exibir conteúdo privado.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),
                FieldSpec("kind", ValueKind.STRING, nonempty=True)),
        resources=(ResourceSpec("source", "source"),),
        outputs=(FieldSpec("kind", ValueKind.STRING),
                 FieldSpec("summary", ValueKind.STRING)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),)

    def execute(self, source: str, kind: str, **kwargs) -> ToolResult:
        if kind not in _ALLOWED_EXT or Path(source).suffix.lower() not in _ALLOWED_EXT[kind]:
            return ToolResult(False, self.name, error="Tipo de inspeção Craft não suportado.")
        executable = shutil.which(_BIN[kind])
        if executable is None:
            return ToolResult(False, self.name, error=f"CLI opcional ausente: {_BIN[kind]}.")
        try:
            content = _read_source(self.path_security or PathSecurity(), source, _INPUT_LIMIT)
            # The private temporary source copy protects the original file.
            # Third-party CLI code still runs with user privileges, NOT sandboxed.
            with tempfile.TemporaryDirectory(prefix="nexus-craft-info-") as location:
                work = Path(location)
                incoming = work / ("entrada" + Path(source).suffix.lower())
                incoming.write_bytes(content)
                with tempfile.TemporaryFile() as result_stream:
                    status = subprocess.run(
                        [executable, "info", str(incoming)],
                        cwd=location, stdin=subprocess.DEVNULL,
                        stdout=result_stream, stderr=subprocess.DEVNULL,
                        timeout=45, check=False,
                    )
                    if status.returncode != 0:
                        raise ValueError("Consulta de metadados recusada pelo CLI.")
                    if result_stream.tell() > _MAX_JSON_BYTES:
                        raise ValueError("Saída maior que o limite de metadados.")
                    result_stream.seek(0)
                    summary = _safe_summary(kind, result_stream.read(_MAX_JSON_BYTES + 1))
            return ToolResult(True, self.name, data={"kind": kind, "summary": summary})
        except (OSError, PermissionError, ValueError, UnicodeError,
                subprocess.TimeoutExpired) as exc:
            return ToolResult(False, self.name,
                              error=f"Metadados indisponíveis: {type(exc).__name__}.")
