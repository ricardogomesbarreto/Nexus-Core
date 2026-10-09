"""Restrict filesystem access to a trusted home directory without symlink races."""

import os
import stat
from contextlib import contextmanager
from pathlib import Path


class PathSecurity:
    """Policy check plus descriptor-anchored Linux access for filesystem tools."""

    def __init__(self):
        self.home = Path.home().resolve()
        self.protected_paths = [
            *(Path(p).resolve() for p in (
                "/boot", "/etc", "/bin", "/sbin", "/usr", "/var", "/root",
                "/sys", "/proc", "/dev", "/run", "/lib", "/lib64",
                "/opt", "/srv", "/snap",
            )),
            *(self.home / p for p in (
                ".ssh", ".gnupg", ".aws", ".docker", ".kube", ".config",
                ".local/share/keyrings",
            )),
        ]

    def resolve(self, path: str | Path) -> Path:
        return Path(path).expanduser().resolve(strict=False)

    @staticmethod
    def _is_inside(target: Path, parent: Path) -> bool:
        try:
            target.relative_to(parent)
            return True
        except ValueError:
            return False

    def is_protected(self, path: str | Path) -> bool:
        target = self.resolve(path)
        return any(self._is_inside(target, protected) for protected in self.protected_paths)

    def is_allowed(self, path: str | Path) -> bool:
        target = self.resolve(path)
        return not self.is_protected(target) and self._is_inside(target, self.home)

    def _components(self, path: str | Path) -> tuple[Path, tuple[str, ...]]:
        """Lexical validation precedes opening; never follow a symlink at access time."""
        raw = Path(os.path.abspath(os.path.expanduser(os.fspath(path))))
        home = self.home
        try:
            relative = raw.relative_to(home)
        except ValueError as exc:
            raise PermissionError("Caminho fora da área autorizada do Nexus.") from exc
        if self.is_protected(raw) or not self.is_allowed(raw):
            raise PermissionError("Caminho protegido ou fora da área autorizada.")
        return raw, relative.parts

    @contextmanager
    def open_directory(self, path: str | Path):
        """Keep every ancestor anchored by an open descriptor (no symlink following)."""
        raw, components = self._components(path)
        flags = os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC
        current_fd = os.open(self.home, flags)
        try:
            for component in components:
                try:
                    next_fd = os.open(component, flags, dir_fd=current_fd)
                except OSError as exc:
                    if exc.errno in (40, 20):  # ELOOP or ENOTDIR (including symlink)
                        raise PermissionError("Componentes simbólicos ou inválidos são bloqueados.") from exc
                    raise
                os.close(current_fd)
                current_fd = next_fd
            yield current_fd, raw
        finally:
            os.close(current_fd)

    @contextmanager
    def open_regular_file(self, path: str | Path):
        """Pin a regular file inode with O_NOFOLLOW; no second pathname lookup for reads."""
        raw, _ = self._components(path)
        with self.open_directory(raw.parent) as (parent_fd, _):
            try:
                fd = os.open(
                    raw.name,
                    os.O_RDONLY | os.O_NONBLOCK | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=parent_fd,
                )
            except OSError as exc:
                if exc.errno == 40:  # ELOOP
                    raise PermissionError("Links simbólicos não são permitidos.") from exc
                raise
            try:
                if not stat.S_ISREG(os.fstat(fd).st_mode):
                    raise IsADirectoryError("O caminho não é um arquivo regular.")
                yield fd, raw
            finally:
                os.close(fd)
