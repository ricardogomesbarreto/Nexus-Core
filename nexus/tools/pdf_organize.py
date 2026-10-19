"""Rotate or move PDF pages into a fresh file after one explicit approval.

The optional local PDF executable receives a private source copy. Its output
is checked and committed under the same path policy used by other Nexus tools.
"""

from __future__ import annotations

from pathlib import Path
import os
import shutil
import subprocess
import tempfile

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind
from nexus.tools.creative import _read_source, _write_new
from nexus.tools.pdf_extract import _page_selection, _validate_pdf_copy


class PdfOrganizeTool(NexusTool):
    name = "pdf_organize_local"
    description = ("Gira páginas em 90, 180 ou 270 graus ou move uma página "
                   "para outra posição em um PDF novo; preserva o original.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True),
                FieldSpec("operation", ValueKind.STRING, nonempty=True),
                FieldSpec("pages", ValueKind.STRING, nonempty=True),
                FieldSpec("value", ValueKind.INTEGER)),
        resources=(ResourceSpec("source", "source"), ResourceSpec("output", "output")),
        outputs=(FieldSpec("path", ValueKind.STRING),),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),
                SensitiveResource("output", kwargs["output"]))

    def execute(self, source: str, output: str, operation: str,
                pages: str, value: int, **kwargs) -> ToolResult:
        try:
            selection, count = _page_selection(pages)
            if operation == "rotate":
                if value not in (90, 180, 270):
                    raise ValueError("Ângulo inválido.")
                argument = ("--rotate", f"{selection}:{value}")
            elif operation == "move":
                if count != 1 or "-" in selection or "," in selection or not 1 <= value <= 5000:
                    raise ValueError("Mover exige uma página e uma posição válida.")
                argument = ("--move", f"{selection}:{value}")
            else:
                raise ValueError("Operação não suportada.")
            if Path(source).suffix.lower() != ".pdf" or Path(output).suffix.lower() != ".pdf":
                raise ValueError("Origem e destino devem ser PDFs.")
            executable = shutil.which("pdfcraft-cli")
            if executable is None:
                return ToolResult(False, self.name,
                                  error="Mecanismo local de PDF não instalado. Consulte --feature-check.")
            policy = self.path_security or PathSecurity()
            target, _ = policy._components(output)
            with policy.open_directory(target.parent) as (directory_fd, _):
                try:
                    os.stat(target.name, dir_fd=directory_fd, follow_symlinks=False)
                except FileNotFoundError:
                    pass
                else:
                    raise FileExistsError("Arquivo de saída já existe.")
            original = _read_source(policy, source, 20 * 1024 * 1024)
            _validate_pdf_copy(original)
            with tempfile.TemporaryDirectory(prefix="nexus-pdf-pages-") as location:
                work = Path(location)
                incoming, outgoing = work / "entrada.pdf", work / "resultado.pdf"
                incoming.write_bytes(original)
                status = subprocess.run(
                    [executable, "edit", str(incoming), "--out", str(outgoing), *argument],
                    cwd=location, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=90, check=False,
                )
                if status.returncode:
                    raise ValueError("O mecanismo local não organizou as páginas.")
                staging_policy = PathSecurity()
                staging_policy.home = work
                staging_policy.protected_paths = []
                result = _read_source(staging_policy, str(outgoing), 25 * 1024 * 1024)
                _validate_pdf_copy(result)
                saved = _write_new(policy, output, result)
            return ToolResult(True, self.name, data={"path": saved})
        except (OSError, PermissionError, ValueError, subprocess.TimeoutExpired) as exc:
            return ToolResult(False, self.name,
                              error=f"Organização do PDF não concluída: {type(exc).__name__}.")
