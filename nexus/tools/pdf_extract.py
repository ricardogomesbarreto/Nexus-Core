"""Extract explicitly listed PDF pages using the optional PdfCraft CLI.

The original ZIP documents: pdfcraft-cli extract IN --pages 1,3-5 --out OUT.
Only a fresh copy under the authorized HOME is ever committed to disk.
"""

from __future__ import annotations

from pathlib import Path
import re
import shutil
import subprocess
import tempfile

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind
from nexus.tools.creative import _read_source, _write_new


def _page_selection(value: str) -> tuple[str, int]:
    """Accept at most 20 distinct page numbers, 1-based, no CLI options."""
    if type(value) is not str or not re.fullmatch(r"[1-9][0-9]{0,3}(?:-[1-9][0-9]{0,3})?(?:,[1-9][0-9]{0,3}(?:-[1-9][0-9]{0,3})?)*", value):
        raise ValueError("Lista de páginas inválida.")
    pages: set[int] = set()
    for part in value.split(","):
        first, _, last = part.partition("-")
        start, end = int(first), int(last or first)
        if end < start or end > 5000 or end - start >= 20:
            raise ValueError("Intervalo de páginas inválido.")
        numbers = set(range(start, end + 1))
        if pages.intersection(numbers) or len(pages) + len(numbers) > 20:
            raise ValueError("Páginas duplicadas ou limite excedido.")
        pages.update(numbers)
    return value, len(pages)


def _validate_pdf_copy(data: bytes) -> None:
    """Structural floor, not an independent PDF parser or fidelity check."""
    if (len(data) < 64 or not re.match(rb"^%PDF-[12]\.\d(?:\r?\n)", data[:16])
            or b"startxref" not in data[-2048:]
            or b"%%EOF" not in data[-1024:]):
        raise ValueError("PdfCraft não produziu um PDF reconhecível.")


class PdfExtractTool(NexusTool):
    name = "pdf_extract_pages_local"
    description = ("Copia páginas explícitas de um PDF local para outro PDF novo "
                   "com PdfCraft opcional; pages como 1,3-5, até 20 páginas.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True),
                FieldSpec("pages", ValueKind.STRING, nonempty=True)),
        resources=(ResourceSpec("source", "source"), ResourceSpec("output", "output")),
        outputs=(FieldSpec("path", ValueKind.STRING), FieldSpec("page_count", ValueKind.INTEGER)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),
                SensitiveResource("output", kwargs["output"]))

    def execute(self, source: str, output: str, pages: str, **kwargs) -> ToolResult:
        try:
            selection, count = _page_selection(pages)
            if (Path(source).suffix.lower() != ".pdf" or
                    Path(output).suffix.lower() != ".pdf"):
                raise ValueError("Origem e destino devem ser PDF.")
            executable = shutil.which("pdfcraft-cli")
            if executable is None:
                raise ValueError("CLI local opcional ausente: pdfcraft-cli.")
            policy = self.path_security or PathSecurity()
            data = _read_source(policy, source, 20 * 1024 * 1024)
            if not data.startswith(b"%PDF-"):
                raise ValueError("Arquivo de origem não é PDF.")
            with tempfile.TemporaryDirectory(prefix="nexus-pdf-extract-") as location:
                work = Path(location)
                incoming, outgoing = work / "entrada.pdf", work / "paginas.pdf"
                incoming.write_bytes(data)
                result = subprocess.run(
                    [executable, "extract", str(incoming), "--pages", selection,
                     "--out", str(outgoing)], cwd=location,
                    stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL, timeout=90, check=False,
                )
                if result.returncode != 0:
                    raise ValueError("PdfCraft não extraiu as páginas solicitadas.")
                staging_policy = PathSecurity()
                staging_policy.home = work
                staging_policy.protected_paths = []
                result_data = _read_source(staging_policy, str(outgoing), 25 * 1024 * 1024)
                _validate_pdf_copy(result_data)
                saved = _write_new(policy, output, result_data)
            return ToolResult(True, self.name, data={"path": saved, "page_count": count})
        except (OSError, PermissionError, ValueError, subprocess.TimeoutExpired) as exc:
            return ToolResult(False, self.name,
                              error=f"Extração de páginas não concluída: {type(exc).__name__}.")
