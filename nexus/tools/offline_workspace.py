"""Local offline productivity actions inspired by independently installed knowledge suites.

NEXUS CORE remains a native Linux desktop process. These actions neither
start containers nor contact remote services. Never copy another product's UI.
"""
from __future__ import annotations

import base64
import binascii
import codecs
import hashlib
import os
import shutil
import urllib.parse
from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind


class LocalNoteTool(NexusTool):
    """Create one brand-new private markdown note after SecurityGate consent."""

    name = "local_note_create"
    description = "Cria uma nova nota Markdown UTF-8 no local escolhido, sem substituir arquivos."
    risk_level = RiskLevel.MEDIUM
    path_security = None
    MAX_NOTE_BYTES = 64 * 1024
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("output", ValueKind.STRING, nonempty=True),
                FieldSpec("content", ValueKind.STRING, nonempty=True)),
        resources=(ResourceSpec("output", "output"),),
        outputs=(FieldSpec("path", ValueKind.STRING),
                 FieldSpec("bytes", ValueKind.INTEGER)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("output", kwargs["output"]),)

    def execute(self, output: str, content: str, **kwargs) -> ToolResult:
        data = content.encode("utf-8")
        if not data or len(data) > self.MAX_NOTE_BYTES or "\x00" in content:
            return ToolResult(False, self.name, error="Nota vazia, binária ou acima de 64 KiB.")
        if Path(output).suffix.lower() != ".md":
            return ToolResult(False, self.name, error="Notas locais exigem arquivo .md.")
        policy = self.path_security or PathSecurity()
        try:
            raw, _ = policy._components(output)
            if raw.name in (".", ".."):
                raise ValueError("Destino inválido.")
            with policy.open_directory(raw.parent) as (fd, _):
                created = os.open(
                    raw.name,
                    os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                    0o600, dir_fd=fd,
                )
                try:
                    with os.fdopen(created, "wb", closefd=False) as stream:
                        stream.write(data)
                        stream.flush()
                        os.fsync(stream.fileno())
                finally:
                    os.close(created)
            return ToolResult(True, self.name, data={"path": str(raw), "bytes": len(data)})
        except FileExistsError:
            return ToolResult(False, self.name, error="O arquivo já existe; nada foi alterado.")
        except (OSError, PermissionError, ValueError) as exc:
            return ToolResult(False, self.name, error=f"Nota não criada: {type(exc).__name__}.")


def _transform(operation: str, value: str) -> str:
    """Deterministic text transforms: no shell, uploads, secrets or network."""
    if type(value) is not str or len(value.encode("utf-8")) > 8192 or "\x00" in value:
        raise ValueError("Texto inválido ou acima de 8 KiB.")
    if operation == "sha256":
        result = hashlib.sha256(value.encode("utf-8")).hexdigest()
    elif operation == "base64_encode":
        result = base64.b64encode(value.encode("utf-8")).decode("ascii")
    elif operation == "base64_decode":
        result = base64.b64decode(value, validate=True).decode("utf-8")
    elif operation == "hex_encode":
        result = value.encode("utf-8").hex()
    elif operation == "hex_decode":
        result = bytes.fromhex(value).decode("utf-8")
    elif operation == "url_encode":
        result = urllib.parse.quote(value, safe="")
    elif operation == "url_decode":
        # Strict percent-encoding; do not silently accept truncated data.
        import re
        if re.search(r"%(?![0-9a-fA-F]{2})", value):
            raise ValueError("Percent-encoding inválido.")
        result = urllib.parse.unquote(value, encoding="utf-8", errors="strict")
    elif operation == "rot13":
        result = codecs.encode(value, "rot_13")
    else:
        raise ValueError("Transformação não permitida.")
    if len(result.encode("utf-8")) > 32768:
        raise ValueError("Resultado acima de 32 KiB.")
    return result


class LocalDataTool(NexusTool):
    name = "local_data_transform"
    description = ("Transforma texto localmente: SHA-256, Base64, hexadecimal, "
                   "percent-encoding URL e ROT13; não é criptografia.")
    risk_level = RiskLevel.SAFE
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("operation", ValueKind.STRING, nonempty=True),
                FieldSpec("value", ValueKind.STRING)),
        resources=(),
        outputs=(FieldSpec("operation", ValueKind.STRING),
                 FieldSpec("result", ValueKind.STRING)),
    )

    def sensitive_resources(self, **kwargs):
        return ()

    def execute(self, operation: str, value: str, **kwargs):
        try:
            result = _transform(operation, value)
            return ToolResult(True, self.name,
                              data={"operation": operation, "result": result})
        except (UnicodeError, ValueError, binascii.Error, LookupError):
            return ToolResult(False, self.name,
                              error="Transformação inválida ou dados incompatíveis.")


# Passive detection only. An installed binary is NOT a running/approved service.
# Do not probe HTTP ports, docker socket or start / enable dependencies here.
_PASSIVE = (
    ("biblioteca_offline", "kiwix-serve"),
    ("cursos_offline", "kolibri"),
    ("mapas_offline", "pmtiles"),
    ("catalogo_apps", "docker"),
)


def offline_capabilities(*, which=None) -> list[dict[str, str]]:
    probe = which if which is not None else shutil.which
    catalog = [
        {"capability": "notas_markdown", "status": "local_integrada"},
        {"capability": "ferramentas_dados", "status": "local_integrada"},
        {"capability": "conversa_local", "status": "integrada_requer_modelo"},
        {"capability": "pesquisa_documental", "status": "texto_postgresql_sem_vetor"},
        {"capability": "diagnostico_sistema", "status": "integrado_sem_ranking"},
    ]
    for capability, binary in _PASSIVE:
        catalog.append({
            "capability": capability,
            "status": "opcional_detectado_nao_iniciado" if probe(binary) else "opcional_ausente",
        })
    # The attached server uses several independent services; no integration
    # may be inferred just because one binary appears on PATH.
    catalog.append({"capability": "busca_semantica_vetorial", "status": "planejada_nao_integrada"})
    return catalog
