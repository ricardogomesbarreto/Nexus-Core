"""Create bounded, symlink-free filesystem snapshots for Docker workspaces."""

import os
import stat
from pathlib import Path


MAX_WORKSPACE_FILES = 512
MAX_WORKSPACE_BYTES = 32 * 1024 * 1024
MAX_WORKSPACE_DEPTH = 8
_CHUNK = 64 * 1024


class WorkspaceSnapshotError(RuntimeError):
    """A workspace could not be copied within conservative security limits."""


def snapshot_directory(source_fd: int, destination: Path) -> None:
    """Copy exclusively through directory descriptors, never via a mutable path.

    A concurrent directory rename does not redirect reads. Symlinks, sockets,
    FIFOs, devices, oversized trees and oversized files are rejected.
    """
    usage = {"entries": 0, "files": 0, "bytes": 0}

    def copy_tree(fd: int, folder: Path, depth: int) -> None:
        if depth > MAX_WORKSPACE_DEPTH:
            raise WorkspaceSnapshotError("Workspace excede a profundidade máxima.")
        with os.scandir(fd) as scan:
            names = []
            for entry in scan:
                names.append(entry.name)
                if len(names) + usage["entries"] > MAX_WORKSPACE_FILES:
                    raise WorkspaceSnapshotError("Workspace contém itens demais.")
        for name in sorted(names):
            usage["entries"] += 1
            if usage["entries"] > MAX_WORKSPACE_FILES:
                raise WorkspaceSnapshotError("Workspace contém itens demais.")
            flags = os.O_RDONLY | os.O_NOFOLLOW | os.O_CLOEXEC | os.O_NONBLOCK
            child_fd = os.open(name, flags, dir_fd=fd)
            try:
                meta = os.fstat(child_fd)
                if stat.S_ISDIR(meta.st_mode):
                    subdir = folder / name
                    subdir.mkdir(mode=0o700)
                    copy_tree(child_fd, subdir, depth + 1)
                elif stat.S_ISREG(meta.st_mode):
                    usage["files"] += 1
                    if (usage["files"] > MAX_WORKSPACE_FILES
                            or usage["bytes"] + meta.st_size > MAX_WORKSPACE_BYTES):
                        raise WorkspaceSnapshotError("Workspace excede o limite de 512 arquivos ou 32 MB.")
                    target = folder / name
                    # Exclusive creation prevents overwriting existing files in staging.
                    with target.open("xb") as dest:
                        while True:
                            data = os.read(child_fd, _CHUNK)
                            if not data:
                                break
                            usage["bytes"] += len(data)
                            if usage["bytes"] > MAX_WORKSPACE_BYTES:
                                raise WorkspaceSnapshotError("Workspace excede 32 MB.")
                            dest.write(data)
                else:
                    raise WorkspaceSnapshotError("Workspace contém um arquivo especial não permitido.")
            finally:
                os.close(child_fd)

    try:
        copy_tree(source_fd, destination, 0)
    except (OSError, WorkspaceSnapshotError) as exc:
        raise WorkspaceSnapshotError(
            "Não foi possível preparar uma cópia segura do workspace."
        ) from exc
