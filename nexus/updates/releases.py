"""NEXUS CORE: stable GitHub release metadata validation and bounded downloads.

Never execute a downloaded asset here. Only an exact official wheel with
GitHub API reported sha256 digest can be staged. All failures are fail-closed.
"""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path
import re
import tempfile
from urllib.request import Request, urlopen


REPOSITORY = "ricardogomesbarreto/Nexus-Core"
API = "https://api.github.com/repos/" + REPOSITORY + "/releases/latest"
MAX_METADATA = 256 * 1024
MAX_WHEEL = 25 * 1024 * 1024
VERSION_PATTERN = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
SHA256_PATTERN = re.compile(r"^sha256:([a-f0-9]{64})$")


class UpdateError(ValueError):
    """A stable generic updater failure, without private network details."""


@dataclass(frozen=True)
class ReleaseWheel:
    version: str
    filename: str
    url: str
    sha256: str
    size: int


def version_tuple(version: str) -> tuple[int, int, int]:
    if type(version) is not str or not VERSION_PATTERN.fullmatch(version):
        raise UpdateError("Versão de atualização inválida.")
    return tuple(int(x) for x in version.split("."))


def parse_release(payload: str, current_version: str) -> ReleaseWheel | None:
    """Check all metadata before accepting a newer, stable, trusted artifact."""
    current = version_tuple(current_version)
    if type(payload) is not str or len(payload.encode("utf-8")) > MAX_METADATA:
        raise UpdateError("Metadados de atualização inválidos.")
    try:
        data = json.loads(payload)
    except (ValueError, TypeError) as exc:
        raise UpdateError("Resposta de atualização inválida.") from exc
    if type(data) is not dict or data.get("draft") is not False or data.get("prerelease") is not False:
        raise UpdateError("Apenas releases estáveis são aceitas.")
    tag = data.get("tag_name")
    if type(tag) is not str or not tag.startswith("v"):
        raise UpdateError("Tag de release inválida.")
    version = tag[1:]
    if version_tuple(version) <= current:
        return None
    filename = f"nexus_core-{version}-py3-none-any.whl"
    expected = (
        f"https://github.com/{REPOSITORY}/releases/download/{tag}/{filename}"
    )
    assets = data.get("assets")
    if type(assets) is not list or len(assets) > 30:
        raise UpdateError("Lista de artefatos inválida.")
    matches = [
        item for item in assets if type(item) is dict
        and item.get("name") == filename
    ]
    if len(matches) != 1:
        raise UpdateError("Wheel oficial da release não está disponível.")
    item = matches[0]
    digest = item.get("digest")
    if type(digest) is not str:
        raise UpdateError("Release não informa hash de integridade.")
    sha = SHA256_PATTERN.fullmatch(digest)
    if sha is None:
        raise UpdateError("Hash de integridade inválido.")
    if item.get("browser_download_url") != expected:
        raise UpdateError("A URL do artefato não pertence à release oficial.")
    size = item.get("size")
    if type(size) is not int or not 0 < size <= MAX_WHEEL:
        raise UpdateError("Tamanho do artefato inválido.")
    if item.get("state") not in (None, "uploaded"):
        raise UpdateError("Artefato ainda não está publicado.")
    return ReleaseWheel(version, filename, expected, sha.group(1), size)


def _https_get(url: str, *, maximum: int) -> bytes:
    request = Request(
        url,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Nexus-Core-Official-Updater",
        },
        method="GET",
    )
    try:
        with urlopen(request, timeout=8) as response:
            # urllib's standard redirect handling is HTTPS/CA verified;
            # restrict final download host to GitHub's asset infrastructure.
            final = response.geturl()
            from urllib.parse import urlsplit
            parsed = urlsplit(final)
            allowed = (
                parsed.hostname == "github.com" or
                (parsed.hostname is not None and
                 (parsed.hostname == "release-assets.githubusercontent.com" or
                  parsed.hostname.endswith(".githubusercontent.com")))
            )
            if parsed.scheme != "https" or not allowed:
                raise UpdateError("Redirecionamento de download não confiável.")
            value = response.read(maximum + 1)
    except UpdateError:
        raise
    except (OSError, TimeoutError, ValueError) as exc:
        raise UpdateError("Não foi possível consultar a atualização via HTTPS.") from exc
    if len(value) > maximum:
        raise UpdateError("Resposta de atualização excede o limite.")
    return value


def latest_release(current_version: str) -> ReleaseWheel | None:
    try:
        data = _https_get(API, maximum=MAX_METADATA)
        return parse_release(data.decode("utf-8", errors="strict"), current_version)
    except (UnicodeError, ValueError) as exc:
        raise UpdateError("Falha ao validar a release oficial.") from exc


def download_verified(release: ReleaseWheel, directory: Path) -> Path:
    """Stage verified wheel under an owner-controlled directory, atomically."""
    if not isinstance(release, ReleaseWheel):
        raise UpdateError("Atualização não validada.")
    if not directory.is_dir() or directory.is_symlink():
        raise UpdateError("Diretório de downloads não confiável.")
    # No path elements or user-supplied URLs.
    if release.filename != f"nexus_core-{release.version}-py3-none-any.whl":
        raise UpdateError("Nome do pacote não corresponde à versão.")
    filename = directory / release.filename
    if filename.is_symlink():
        raise UpdateError("Destino de atualização inválido.")
    temporary = None
    try:
        with tempfile.NamedTemporaryFile(
            prefix=".nexus-wheel-", dir=directory, delete=False
        ) as handle:
            temporary = Path(handle.name)
            body = _https_get(release.url, maximum=MAX_WHEEL)
            if len(body) != release.size:
                raise UpdateError("Tamanho do wheel difere do informado.")
            if hashlib.sha256(body).hexdigest() != release.sha256:
                raise UpdateError("Wheel não passou na validação SHA-256.")
            handle.write(body)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, filename)
        return filename
    except (OSError, UpdateError) as exc:
        raise UpdateError("Falha ao verificar ou armazenar a atualização.") from exc
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)
