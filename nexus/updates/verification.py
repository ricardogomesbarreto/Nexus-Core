"""NEXUS CORE v0.8.7: verify an isolated Ubuntu venv before activation.

This pre-activation smoke gate does NOT open the desktop, model, camera,
microphone, PostgreSQL session, or update server. It executes only pip check,
--version and the passive --platform-check from the *new* Python interpreter.
A successful probe is not an end-to-end application or hardware certification.
"""
import json
from pathlib import Path
import re
import subprocess


class RuntimeVerificationError(RuntimeError):
    """Safe error without potentially sensitive process output."""


def validate_version_output(output: str | bytes, expected: str) -> None:
    """Fail closed on a mismatched package version."""
    try:
        value = output.decode("utf-8", errors="strict") if isinstance(output, bytes) else output
        if type(value) is not str or value.strip() != "Nexus Core " + expected:
            raise RuntimeVerificationError("Versão Python instalada divergente.")
    except UnicodeError as exc:
        raise RuntimeVerificationError("Saída inválida do executável.") from exc


def validate_platform_report(output: str | bytes) -> None:
    """Enforce a recognized Ubuntu/Fedora version and required runtime capabilities."""
    try:
        text = output.decode("utf-8", errors="strict") if isinstance(output, bytes) else output
        if type(text) is not str or len(text) > 12_000:
            raise RuntimeVerificationError("Diagnóstico de instalação inválido.")
        result = json.loads(text)
    except (ValueError, UnicodeError) as exc:
        raise RuntimeVerificationError("Diagnóstico de instalação inválido.") from exc
    if type(result) is not dict:
        raise RuntimeVerificationError("Diagnóstico de instalação inválido.")
    distro, release = result.get("distro"), result.get("version_id")
    supported = (
        (distro == "ubuntu" and result.get("target") == "ubuntu_compatible"
         and type(release) is str and
         re.fullmatch(r"[0-9]{2}\.[0-9]{2}(?:\.[0-9]+)?", release) is not None)
        or
        (distro == "fedora" and result.get("target") == "fedora_compatible"
         and type(release) is str and re.fullmatch(r"[0-9]{2}", release) is not None
         and 43 <= int(release) <= 45)
    )
    if not (supported and result.get("mode") == "passive"
            and result.get("system") == "Linux"
            and result.get("installer_supported") is True
            and result.get("python_supported") is True
            and result.get("changes_performed") is False
            and result.get("missing_required") == []):
        raise RuntimeVerificationError("Linux Fedora/Ubuntu ou dependências não validados.")


def verify_installed_runtime(
    python: Path, expected_version: str, *, run=None,
) -> None:
    """Check dependencies + isolated CLI; never fall back to source-tree import."""
    run = subprocess.run if run is None else run
    for argv, timeout in (
        ([str(python), "-I", "-m", "pip", "check"], 30),
        ([str(python), "-I", "-m", "nexus.main", "--version"], 20),
        ([str(python), "-I", "-m", "nexus.main", "--platform-check"], 20),
    ):
        try:
            result = run(
                argv, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=timeout, check=True,
            )
            if result.returncode != 0:
                raise RuntimeVerificationError("Verificação do pacote falhou.")
            if argv[-1] == "--version":
                validate_version_output(result.stdout, expected_version)
            elif argv[-1] == "--platform-check":
                validate_platform_report(result.stdout)
        except (OSError, subprocess.SubprocessError, UnicodeError) as exc:
            raise RuntimeVerificationError("Falha nas verificações de instalação.") from exc
