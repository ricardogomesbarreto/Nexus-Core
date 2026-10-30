"""Inspect official Kolibri KOLIBRI_DATA offline exports without starting Kolibri.

Kolibri exports channel databases under content/databases and binary resources
under content/storage. We inspect only filenames, inode types and sizes. We
never open the SQLite databases, execute their contents, recurse into storage,
connect to localhost, or modify an export. The selected folder must pass the
NEXUS CORE HOME/path-security policy.
"""
from __future__ import annotations

import os
import re
import stat
from dataclasses import dataclass
from pathlib import Path

from nexus.security.paths import PathSecurity


class KolibriExportError(ValueError):
    """Public error that omits paths and private metadata."""


@dataclass(frozen=True)
class KolibriChannel:
    channel_id: str
    database_bytes: int


@dataclass(frozen=True)
class KolibriExport:
    channels: tuple[KolibriChannel, ...]
    has_content_storage: bool


CHANNEL_DATABASE = re.compile(r"([0-9a-f]{32})(?:\.sqlite3?|\.db)?\Z")
DIR_FLAGS = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
FILE_FLAGS = os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC
MAX_ENTRIES = 300
MAX_CHANNELS = 60


def _directory(parent_fd: int, filename: str) -> int:
    return os.open(filename, DIR_FLAGS, dir_fd=parent_fd)


def inspect_kolibri_export(folder: str | Path,
                           paths: PathSecurity | None = None) -> KolibriExport:
    """Inspect a user-selected KOLIBRI_DATA under the authorized HOME tree.

    Metadata-only: never read channel DB bytes, run Kolibri, import or index.
    """
    if not isinstance(folder, (str, Path)) or not os.fspath(folder):
        raise KolibriExportError("Escolha uma pasta KOLIBRI_DATA válida.")
    if Path(folder).name != "KOLIBRI_DATA":
        raise KolibriExportError("Escolha a pasta KOLIBRI_DATA exportada pelo Kolibri.")
    guard = paths if paths is not None else PathSecurity()
    content_fd = db_fd = None
    try:
        with guard.open_directory(folder) as (root_fd, _):
            content_fd = _directory(root_fd, "content")
            db_fd = _directory(content_fd, "databases")
            found = []
            with os.scandir(db_fd) as entries:
                for inspected, entry in enumerate(entries, 1):
                    if inspected > MAX_ENTRIES:
                        raise KolibriExportError(
                            "Exportação contém entradas demais para inspeção limitada."
                        )
                    match = CHANNEL_DATABASE.fullmatch(entry.name)
                    if not match:
                        continue
                    if not entry.is_file(follow_symlinks=False):
                        continue
                    # Pin inode without following symlinks; metadata only.
                    fd = os.open(entry.name, FILE_FLAGS, dir_fd=db_fd)
                    try:
                        info = os.fstat(fd)
                        if not stat.S_ISREG(info.st_mode) or info.st_size <= 0:
                            continue
                        found.append(KolibriChannel(match.group(1), info.st_size))
                    finally:
                        os.close(fd)
                    if len(found) > MAX_CHANNELS:
                        raise KolibriExportError(
                            "Exportação excede o máximo de 60 canais."
                        )
            has_storage = False
            try:
                storage_fd = _directory(content_fd, "storage")
            except FileNotFoundError:
                pass
            else:
                has_storage = True
                os.close(storage_fd)
            found.sort(key=lambda channel: channel.channel_id)
            return KolibriExport(tuple(found), has_storage)
    except KolibriExportError:
        raise
    except (OSError, PermissionError) as exc:
        raise KolibriExportError(
            "Exportação Kolibri inválida, protegida ou inacessível."
        ) from exc
    finally:
        for fd in (db_fd, content_fd):
            if fd is not None:
                os.close(fd)
