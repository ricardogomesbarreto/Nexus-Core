"""Opt-in execution of an already installed image in a local rootless runtime.

No image name, registry, Docker socket, host mount or command is accepted.
The image's own entrypoint executes only after explicit user confirmation.
"""
from __future__ import annotations

import json
import os
import re
import selectors
import signal
import stat
import subprocess
import tempfile
from dataclasses import dataclass
from pathlib import Path
from time import monotonic
from threading import Event

from nexus.security import (PermissionDecision, RiskLevel, SecurityGate,
                            SecurityRequest)

IMAGE_ID = re.compile(r"sha256:[0-9a-f]{64}\Z")
MAX_OUTPUT = 16 * 1024
TIMEOUT = 20


class LocalContainerError(ValueError):
    """Safe error without exposing runtime internals or user paths."""


@dataclass(frozen=True)
class LocalContainerResult:
    exit_code: int
    output: str
    truncated: bool


def authorize_local_image(image_id: str, confirm, *, gate: SecurityGate | None = None):
    """Evaluate the policy and record the human decision before any runtime call."""
    if not isinstance(image_id, str) or not IMAGE_ID.fullmatch(image_id):
        raise LocalContainerError("Informe o ID imutável sha256 da imagem local.")
    gate = gate or SecurityGate()
    gate.tool_permissions.register("local_image_run", RiskLevel.MEDIUM)
    request = SecurityRequest(action="local_image_run",
                              description="Executar imagem local isolada " + image_id[:19],
                              risk_level=RiskLevel.MEDIUM,
                              tool_name="local_image_run")
    result = gate.evaluate(request)
    if result.decision != PermissionDecision.CONFIRM:
        raise LocalContainerError("Política de execução local recusou a imagem.")
    approved = bool(confirm(request))
    gate.audit_logger.record(tool_name="local_image_run", action="local_image_run",
                             risk_level="MEDIUM", decision="APPROVED" if approved else "DENIED",
                             reason="Decisão explícita do usuário")
    if not approved:
        raise LocalContainerError("Execução não autorizada.")
    return gate


def _runtime() -> str:
    if os.geteuid() == 0:
        raise LocalContainerError("Execute o NEXUS CORE como usuário comum.")
    # Ignore PATH and user-controlled wrappers for a privileged API client.
    for location in ("/usr/bin/podman", "/bin/podman"):
        candidate = Path(location)
        try:
            info = candidate.lstat()
        except OSError:
            continue
        if (stat.S_ISREG(info.st_mode) and info.st_uid == 0
                and info.st_mode & stat.S_IXUSR):
            return location
    raise LocalContainerError("Podman local não encontrado nos diretórios do sistema.")


def _environment() -> dict[str, str]:
    # Disallow remote connection and registry/proxy configuration from inherited
    # environment. Podman still reads the user's normal local image store.
    names = ("HOME", "USER", "LOGNAME", "XDG_RUNTIME_DIR")
    return {**{key: os.environ[key] for key in names if key in os.environ},
            "PATH": "/usr/bin:/bin", "LC_ALL": "C"}


def _check_rootless(runtime: str, environment: dict[str, str]) -> None:
    try:
        report = subprocess.run([runtime, "info", "--format=json"],
                                stdin=subprocess.DEVNULL, capture_output=True,
                                timeout=4, env=environment, check=False)
        if report.returncode or len(report.stdout) > 128 * 1024:
            raise LocalContainerError("Runtime local indisponível.")
        info = json.loads(report.stdout)
        if (info.get("serviceIsRemote") is not False
                or info.get("host", {}).get("security", {}).get("rootless") is not True
                or str(info.get("host", {}).get("cgroupVersion")) != "v2"):
            raise LocalContainerError("É necessário Podman local sem root e cgroups v2.")
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, TypeError,
            AttributeError) as exc:
        raise LocalContainerError("Não foi possível verificar o runtime local.") from exc


def _command(runtime: str, image_id: str, cidfile: str) -> list[str]:
    if not isinstance(image_id, str) or not IMAGE_ID.fullmatch(image_id):
        raise LocalContainerError("Informe o ID imutável sha256 da imagem local.")
    return [runtime, "run", "--pull=never", "--rm", "--network=none",
            "--http-proxy=false", "--image-volume=ignore", "--read-only",
            "--read-only-tmpfs=false", "--log-driver=none",
            "--memory=256m", "--memory-swap=256m", "--cpus=1",
            "--pids-limit=64", "--cap-drop=ALL",
            "--security-opt=no-new-privileges", "--user=65534:65534",
            "--tmpfs=/tmp:rw,noexec,nosuid,size=32m", "--cidfile=" + cidfile,
            image_id]


def run_local_image(image_id: str, *, cancel: Event | None = None) -> LocalContainerResult:
    """Run a local image with strict bounds; no download or host filesystem access."""
    if not isinstance(image_id, str) or not IMAGE_ID.fullmatch(image_id):
        raise LocalContainerError("Informe o ID imutável sha256 da imagem local.")
    runtime = _runtime()
    environment = _environment()
    _check_rootless(runtime, environment)
    try:
        found = subprocess.run([runtime, "image", "exists", image_id],
                               stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                               stderr=subprocess.DEVNULL, timeout=4, env=environment,
                               check=False)
        if found.returncode:
            raise LocalContainerError("Imagem não encontrada no Podman local.")
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise LocalContainerError("Não foi possível consultar a imagem local.") from exc
    with tempfile.TemporaryDirectory(prefix="nexus-core-oci-") as directory:
        cidfile = str(Path(directory) / "container-id")
        command = _command(runtime, image_id, cidfile)
        process = None
        completed = False
        output = bytearray()
        try:
            process = subprocess.Popen(command, stdin=subprocess.DEVNULL,
                                       stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                       start_new_session=True, env=environment)
            deadline = monotonic() + TIMEOUT
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    if cancel is not None and cancel.is_set():
                        raise LocalContainerError("Execução cancelada.")
                    if monotonic() >= deadline:
                        raise LocalContainerError("Execução excedeu 20 segundos.")
                    events = selector.select(timeout=0.2)
                    if not events:
                        if process.poll() is not None:
                            break
                        continue
                    chunk = os.read(process.stdout.fileno(), 4096)
                    if not chunk:
                        break
                    if len(output) + len(chunk) > MAX_OUTPUT:
                        raise LocalContainerError("Saída acima de 16 KiB; execução interrompida.")
                    output.extend(chunk)
            process.wait(timeout=2)
            completed = True
            return LocalContainerResult(process.returncode,
                                        output.decode("utf-8", errors="replace"), False)
        except (OSError, subprocess.SubprocessError) as exc:
            raise LocalContainerError("Execução local indisponível.") from exc
        finally:
            if process is not None:
                if not completed and process.poll() is None:
                    try:
                        os.killpg(process.pid, signal.SIGKILL)
                    except ProcessLookupError:
                        pass
                try:
                    process.wait(timeout=2)
                except subprocess.TimeoutExpired:
                    pass
                if process.stdout is not None:
                    process.stdout.close()
            # A killed CLI may leave a container behind. Remove only the
            # container recorded in our private cidfile, never any other one.
            if not completed and Path(cidfile).is_file():
                try:
                    subprocess.run([runtime, "rm", "--force", "--cidfile=" + cidfile],
                                   stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                                   stderr=subprocess.DEVNULL, timeout=3, env=environment,
                                   check=False)
                except (OSError, subprocess.TimeoutExpired):
                    pass
