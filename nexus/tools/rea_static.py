"""Optional, bounded offline REA static analysis of explicitly selected artifacts.

Does not run the target or install REA. The installed REA CLI itself is
third-party host code, NOT a sandbox. Only documented static inspection
commands can be invoked, after the normal SecurityGate confirmation.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind
from nexus.tools.creative import _bounded_stdout, _read_source

MAX_SOURCE_BYTES = 16 * 1024 * 1024
MAX_JSON_BYTES = 1024 * 1024

MODES = {
    "go": ("inspect-go-binary", frozenset({".elf", ".so", ".bin", ".exe"})),
    "rust": ("inspect-rust-binary", frozenset({".elf", ".so", ".bin", ".exe"})),
    "dotnet": ("inspect-managed-artifact", frozenset({".dll", ".exe"})),
    "electron": ("analyze-javascript-application", frozenset({".asar"})),
}


class ReaStaticTool(NexusTool):
    name = "rea_static_local"
    description = (
        "Analisa estaticamente artefato local via CLI REA opcional: Go, Rust, "
        ".NET ou pacote Electron ASAR; sem executar o alvo nem usar MCP."
    )
    risk_level = RiskLevel.MEDIUM
    path_security = None

    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(
            FieldSpec("source", ValueKind.STRING, nonempty=True),
            FieldSpec("mode", ValueKind.STRING, nonempty=True),
        ),
        resources=(ResourceSpec("source", "source"),),
        outputs=(
            FieldSpec("mode", ValueKind.STRING),
            FieldSpec("format", ValueKind.STRING),
            FieldSpec("summary", ValueKind.STRING),
        ),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),)

    def execute(self, source: str, mode: str, **kwargs) -> ToolResult:
        try:
            if mode not in MODES:
                raise ValueError("Modo não suportado; use go, rust, dotnet ou electron.")
            command, extensions = MODES[mode]
            suffix = Path(source).suffix.lower()
            if suffix not in extensions:
                raise ValueError("Extensão de artefato incompatível com o modo.")
            executable = shutil.which("rea")
            if not executable or not Path(executable).is_absolute():
                return ToolResult(
                    False, self.name,
                    error="REA opcional não instalado. Instale e verifique o CLI separadamente, sem npx automático.",
                )
            policy = self.path_security or PathSecurity()
            content = _read_source(policy, source, MAX_SOURCE_BYTES)
            if not content:
                raise ValueError("Artefato vazio.")
            with tempfile.TemporaryDirectory(prefix="nexus-rea-") as directory:
                work = Path(directory)
                # The target cannot be executed directly: a private copy is
                # supplied only as the argument of an allowlisted static command.
                sample = work / ("artefato" + suffix)
                fd = os.open(sample, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW, 0o600)
                with os.fdopen(fd, "wb") as output:
                    output.write(content)
                destination = work / "analysis.json"
                # REA must be installed and ready already. No npm/npx,
                # setup, Ghidra provider, decompilation, runtime tracing,
                # network capture or arbitrary CLI arguments.
                _bounded_stdout(
                    [executable, command, str(sample), "--json"],
                    destination, directory, timeout=45,
                )
                if destination.stat().st_size > MAX_JSON_BYTES:
                    raise ValueError("Relatório REA grande demais.")
                report = json.loads(destination.read_text(encoding="utf-8"))
            if not isinstance(report, (dict, list)):
                raise ValueError("Relatório REA inválido.")
            # Never include raw strings, embedded source or target paths in a
            # chat summary. Full report intentionally discarded when exiting.
            if isinstance(report, dict):
                fields = sorted(str(k) for k in report if isinstance(k, str))
                summary = "Análise estática concluída. Campos de evidência: " + (
                    ", ".join(fields[:20]) or "nenhum"
                )
                if len(fields) > 20:
                    summary += f"; mais {len(fields) - 20} campos."
            else:
                summary = f"Análise estática concluída. Entradas no relatório: {len(report)}."
            return ToolResult(True, self.name, data={
                "mode": mode,
                "format": suffix.lstrip("."),
                "summary": summary[:1000],
            })
        except (OSError, UnicodeError, ValueError, json.JSONDecodeError) as exc:
            return ToolResult(
                False, self.name,
                error=f"Análise REA não concluída: {type(exc).__name__}.",
            )
        except __import__("subprocess").TimeoutExpired:
            return ToolResult(
                False, self.name,
                error="Análise REA excedeu o limite de tempo de 45 segundos.",
            )
