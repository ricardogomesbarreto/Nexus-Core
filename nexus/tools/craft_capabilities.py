"""Explicit, read-only discovery of optional Craft command line programs.

The source snapshots define a conservative contract. Discovery never enables
an action or certifies the provenance, isolation or correct output of a binary.
"""

from __future__ import annotations

from dataclasses import dataclass
import os
import re
import selectors
import shutil
import subprocess
import time
from typing import Callable


@dataclass(frozen=True)
class CraftContract:
    binary: str
    snapshot_version: str
    commands: tuple[str, ...]
    formats: tuple[str, ...]


# From the five original ZIPs, Cargo workspace manifests and CLI source files.
# These are Nexus operations only, not every command advertised by upstream.
CONTRACTS = (
    CraftContract("photocraft-cli", "0.9.0", ("convert", "info"),
                  ("png", "jpg", "jpeg", "webp", "psd", "pcraft", "tif", "tiff")),
    CraftContract("wordcraft-cli", "0.7.0", ("convert", "info", "text"),
                  ("docx", "odt", "rtf", "md", "txt", "pdf")),
    CraftContract("pdfcraft-cli", "0.8.0", ("text", "info", "render", "extract", "combine"),
                  ("pdf", "txt", "png")),
)

_MAX_OUTPUT = 64 * 1024
_TIMEOUT = 3.0


def _read_command(binary: str, flag: str) -> str | None:
    """Limit elapsed time and captured output even for a broken executable."""
    try:
        process = subprocess.Popen([binary, flag], stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   close_fds=True)
    except OSError:
        return None
    output = bytearray()
    deadline = time.monotonic() + _TIMEOUT
    try:
        assert process.stdout is not None
        with selectors.DefaultSelector() as selector:
            selector.register(process.stdout, selectors.EVENT_READ)
            while True:
                remaining = deadline - time.monotonic()
                if remaining <= 0:
                    return None
                if not selector.select(remaining):
                    return None
                chunk = os.read(process.stdout.fileno(), min(4096, _MAX_OUTPUT + 1 - len(output)))
                if not chunk:
                    break
                output.extend(chunk)
                if len(output) > _MAX_OUTPUT:
                    return None
        process.wait(timeout=max(0.01, deadline - time.monotonic()))
        if process.returncode != 0:
            return None
        return output.decode("utf-8", errors="replace")
    except (OSError, subprocess.TimeoutExpired):
        return None
    finally:
        if process.poll() is None:
            process.kill()
        process.wait()
        if process.stdout is not None:
            process.stdout.close()


def inspect_craft_capabilities(
    *, find_binary: Callable[[str], str | None] = shutil.which,
    query: Callable[[str, str], str | None] = _read_command,
) -> dict:
    """Probe only --version and --help on explicitly requested diagnostics.

    `available` means the CLI advertises the audited snapshot's small set of
    commands. It does not certify a build or grant permission to run it.
    """
    entries = []
    for contract in CONTRACTS:
        binary = find_binary(contract.binary)
        version = None
        commands: list[str] = []
        if binary is None:
            status = "missing"
        else:
            raw_version = query(binary, "--version")
            raw_help = query(binary, "--help")
            if raw_version is not None:
                match = re.search(r"(?m)^" + re.escape(contract.binary) +
                                  r"\s+(\d+\.\d+\.\d+)(?=\s|$)", raw_version)
                if match:
                    version = match.group(1)
            if raw_help is not None:
                commands = [name for name in contract.commands if re.search(
                    r"(?m)^\s*" + re.escape(contract.binary) + r"\s+" +
                    re.escape(name) + r"(?=\s|$)", raw_help)]
            if version is not None and version != contract.snapshot_version:
                status = "incompatible"
            elif raw_version is None or version is None or raw_help is None or len(commands) != len(contract.commands):
                status = "degraded"
            else:
                status = "available"
        entries.append({"binary": contract.binary, "status": status,
                        "version": version, "snapshot_version": contract.snapshot_version,
                        "advertised_commands": commands,
                        "nexus_commands": list(contract.commands),
                        "contract_formats": list(contract.formats),
                        "real_operation_tested": False})
    return {"schema": "nexus.craft-capabilities.v1", "mode": "explicit_local_probe",
            "tools": entries, "real_operation_tested": False,
            "external_network_used": False}
