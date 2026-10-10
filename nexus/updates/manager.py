"""User-scoped update state: no root and no update to running Python modules."""
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import venv

from .releases import (
    ReleaseWheel, UpdateError, download_verified, latest_release, version_tuple,
)


def managed_home() -> Path:
    base = os.environ.get("XDG_DATA_HOME")
    root = Path(base).expanduser() if base and Path(base).is_absolute() else Path.home() / ".local/share"
    return root / "nexus-core" / "managed"


def _private_directory(path: Path) -> Path:
    # Do not follow an existing symlink supplied via XDG or inside app state.
    if path.is_symlink():
        raise UpdateError("Diretório gerenciado não pode ser link simbólico.")
    path.mkdir(mode=0o700, parents=True, exist_ok=True)
    if not path.is_dir():
        raise UpdateError("Diretório gerenciado inválido.")
    path.chmod(0o700)
    return path


def autoupdate_enabled(home: Path | None = None) -> bool:
    home = home if home is not None else managed_home()
    config = home / "auto-update.enabled"
    if config.is_symlink():
        return False
    try:
        return config.is_file() and config.read_text(encoding="ascii").strip() == "1"
    except (OSError, UnicodeError):
        return False


def set_autoupdate(enabled: bool, home: Path | None = None) -> None:
    home = _private_directory(home if home is not None else managed_home())
    path = home / "auto-update.enabled"
    if path.is_symlink():
        raise UpdateError("Arquivo de preferência inválido.")
    temporary = home / ".auto-update-tmp"
    if temporary.exists() or temporary.is_symlink():
        raise UpdateError("Preferências de atualização ocupadas.")
    try:
        with temporary.open("x", encoding="ascii") as handle:
            os.chmod(temporary, 0o600)
            handle.write("1\n" if enabled else "0\n")
        os.replace(temporary, path)
    finally:
        temporary.unlink(missing_ok=True)


def _metadata_file(home: Path) -> Path:
    return home / "staged-release.json"


def _wheel_path(home: Path, release: ReleaseWheel) -> Path:
    return home / "downloads" / release.filename


def _verify_wheel(path: Path, release: ReleaseWheel) -> bool:
    if path.is_symlink() or not path.is_file() or path.stat().st_size != release.size:
        return False
    sha = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            sha.update(chunk)
    return sha.hexdigest() == release.sha256


def pending_release(home: Path) -> ReleaseWheel | None:
    marker = _metadata_file(home)
    if marker.is_symlink() or not marker.is_file():
        return None
    try:
        data = json.loads(marker.read_text(encoding="utf-8"))
        if type(data) is not dict or set(data) != {
            "version", "filename", "url", "sha256", "size",
        }:
            return None
        release = ReleaseWheel(**data)
        # Validate every field again: the local state is not trusted.
        if type(release.size) is not int or not 0 < release.size <= 25 * 1024 * 1024:
            return None
        if (release.filename != f"nexus_core-{release.version}-py3-none-any.whl"
                or not re.fullmatch("[a-f0-9]{64}", release.sha256)
                or release.url != (
                    "https://github.com/ricardogomesbarreto/Nexus-Core/"
                    f"releases/download/v{release.version}/{release.filename}"
                )):
            return None
        version_tuple(release.version)
        if _verify_wheel(_wheel_path(home, release), release):
            return release
    except (OSError, ValueError, TypeError, UnicodeError):
        pass
    return None


def stage_latest(current_version: str, home: Path | None = None) -> ReleaseWheel | None:
    """Network-only fetch; no installation or process restart."""
    home = home if home is not None else managed_home()
    if not autoupdate_enabled(home):
        return None
    release = latest_release(current_version)
    if release is None:
        return None
    _private_directory(home)
    downloads = _private_directory(home / "downloads")
    target = _wheel_path(home, release)
    if not _verify_wheel(target, release):
        download_verified(release, downloads)
    payload = {
        "version": release.version,
        "filename": release.filename,
        "url": release.url,
        "sha256": release.sha256,
        "size": release.size,
    }
    marker = _metadata_file(home)
    if marker.is_symlink():
        raise UpdateError("Marcador de atualização inválido.")
    fd, name = tempfile.mkstemp(prefix=".release-", dir=home)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            os.fchmod(handle.fileno(), 0o600)
            json.dump(payload, handle, sort_keys=True)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(name, marker)
    finally:
        Path(name).unlink(missing_ok=True)
    return release


def _checked_current(home: Path) -> Path:
    target = home / "current"
    versions = home / "versions"
    if not target.is_symlink() or versions.is_symlink() or not versions.is_dir():
        raise UpdateError("Instalação gerenciada não encontrada.")
    current = target.resolve(strict=True)
    if current.parent != versions.resolve(strict=True):
        raise UpdateError("O link atual aponta para fora da instalação.")
    if not re.fullmatch(r"v[0-9]+\.[0-9]+\.[0-9]+", current.name):
        raise UpdateError("Versão instalada inválida.")
    if not (current / "bin/python").is_file():
        raise UpdateError("Executável da instalação não encontrado.")
    return current


def _switch_current(home: Path, version_dir: Path) -> None:
    """Atomic symlink switch preserving a previous version for rollback."""
    current = home / "current"
    versions = home / "versions"
    if version_dir.parent.resolve() != versions.resolve():
        raise UpdateError("Caminho de versão inesperado.")
    if current.exists() or current.is_symlink():
        previous = _checked_current(home)
        new_previous = home / ".previous-next"
        if new_previous.exists() or new_previous.is_symlink():
            raise UpdateError("Atualização simultânea não permitida.")
        try:
            new_previous.symlink_to(previous)
            os.replace(new_previous, home / "previous")
        finally:
            new_previous.unlink(missing_ok=True)
    temp = home / ".current-next"
    if temp.exists() or temp.is_symlink():
        raise UpdateError("Atualização simultânea não permitida.")
    try:
        temp.symlink_to(version_dir)
        os.replace(temp, current)
    finally:
        temp.unlink(missing_ok=True)


def install_staged(home: Path | None = None, *, current_version: str) -> str | None:
    """Apply an already verified wheel in a fresh venv, never inside the app.

    Only the managed external launcher should call this before starting Nexus.
    On failure the current installation remains selected.
    """
    home = home if home is not None else managed_home()
    if not autoupdate_enabled(home):
        return None
    release = pending_release(home)
    if release is None or version_tuple(release.version) <= version_tuple(current_version):
        return None
    _checked_current(home)
    versions = _private_directory(home / "versions")
    target = versions / ("v" + release.version)
    if target.exists() or target.is_symlink():
        # Reuse of a directory after a failed install could be compromised.
        raise UpdateError("A versão de destino já existe: instalação requer revisão.")
    try:
        venv.create(target, with_pip=True, symlinks=False)
        python = target / "bin" / "python"
        wheel = _wheel_path(home, release)
        if not _verify_wheel(wheel, release):
            raise UpdateError("Wheel de atualização foi alterado.")
        subprocess.run(
            [str(python), "-m", "pip", "install", "--disable-pip-version-check",
             "--no-input", "--retries", "1", "--timeout", "15",
             str(wheel) + "[voice,vision]"],
            stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL, timeout=300, check=True,
        )
        result = subprocess.run(
            [str(python), "-m", "nexus.main", "--version"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=20, check=True,
        )
        if result.stdout.decode("utf-8", errors="strict").strip() != (
            "Nexus Core " + release.version
        ):
            raise UpdateError("O pacote instalado não corresponde à release.")
        _switch_current(home, target)
        _metadata_file(home).unlink(missing_ok=True)
        return release.version
    except (OSError, subprocess.SubprocessError, UpdateError, UnicodeError) as exc:
        # Only the unselected venv created by this call may be discarded.
        import shutil
        if target.is_dir() and not target.is_symlink():
            shutil.rmtree(target, ignore_errors=True)
        raise UpdateError("Atualização falhou; versão anterior preservada.") from exc


def current_python(home: Path | None = None) -> Path:
    home = home if home is not None else managed_home()
    return _checked_current(home) / "bin/python"
