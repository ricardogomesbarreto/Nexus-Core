"""Combine exactly two authorized PDFs using the optional PdfCraft CLI.

Contract verified in the original ZIP: pdfcraft-cli combine A B --out NEW.
The CLI sees private copies; only a fresh output is written to the user's HOME.
"""

from __future__ import annotations

from pathlib import Path
import shutil
import subprocess
import tempfile

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind
from nexus.tools.creative import _read_source, _write_new
from nexus.tools.pdf_extract import _validate_pdf_copy


class PdfCombineTool(NexusTool):
    name = "pdf_combine_local"
    description = ("Junta dois PDFs locais, na ordem informada, em um PDF novo "
                   "com mecanismo local opcional; preserva os originais.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source_a", ValueKind.STRING, nonempty=True),
                FieldSpec("source_b", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True)),
        resources=(ResourceSpec("source_a", "source_a"),
                   ResourceSpec("source_b", "source_b"),
                   ResourceSpec("output", "output")),
        outputs=(FieldSpec("path", ValueKind.STRING),),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source_a", kwargs["source_a"]),
                SensitiveResource("source_b", kwargs["source_b"]),
                SensitiveResource("output", kwargs["output"]))

    def execute(self, source_a: str, source_b: str, output: str, **kwargs) -> ToolResult:
        try:
            if any(Path(p).suffix.lower() != ".pdf" for p in (source_a, source_b, output)):
                raise ValueError("Origens e destino devem ser PDFs.")
            if source_a == source_b:
                raise ValueError("Informe dois arquivos distintos.")
            executable = shutil.which("pdfcraft-cli")
            if executable is None:
                return ToolResult(False, self.name,
                                  error="Mecanismo local de PDF não instalado. Consulte --feature-check.")
            policy = self.path_security or PathSecurity()
            first = _read_source(policy, source_a, 10 * 1024 * 1024)
            second = _read_source(policy, source_b, 10 * 1024 * 1024)
            _validate_pdf_copy(first)
            _validate_pdf_copy(second)
            with tempfile.TemporaryDirectory(prefix="nexus-pdf-combine-") as location:
                work = Path(location)
                a, b, result = work / "primeiro.pdf", work / "segundo.pdf", work / "combinado.pdf"
                a.write_bytes(first)
                b.write_bytes(second)
                status = subprocess.run(
                    [executable, "combine", str(a), str(b), "--out", str(result)],
                    cwd=location, stdin=subprocess.DEVNULL,
                    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                    timeout=90, check=False,
                )
                if status.returncode:
                    raise ValueError("O mecanismo local não juntou os documentos.")
                staging_policy = PathSecurity()
                staging_policy.home = work
                staging_policy.protected_paths = []
                combined = _read_source(staging_policy, str(result), 25 * 1024 * 1024)
                _validate_pdf_copy(combined)
                saved = _write_new(policy, output, combined)
            return ToolResult(True, self.name, data={"path": saved})
        except (OSError, PermissionError, ValueError, subprocess.TimeoutExpired) as exc:
            return ToolResult(False, self.name,
                              error=f"Junção de PDFs não concluída: {type(exc).__name__}.")
