"""Workspace staging rejects dangerous entries and pins original directory inodes."""

import os

import pytest

from nexus.security.workspace import (
    WorkspaceSnapshotError,
    snapshot_directory,
)


def test_snapshot_rejects_symlink_to_outside(tmp_path):
    folder = tmp_path / "workspace"
    folder.mkdir()
    private = tmp_path / "outside.txt"
    private.write_text("SECRET")
    (folder / "redirect.txt").symlink_to(private)
    staged = tmp_path / "snapshot"
    staged.mkdir()
    fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with pytest.raises(WorkspaceSnapshotError):
            snapshot_directory(fd, staged)
    finally:
        os.close(fd)
    assert "SECRET" not in str(list(staged.iterdir()))


def test_snapshot_uses_pinned_directory_after_path_swap(tmp_path):
    folder = tmp_path / "workspace"
    folder.mkdir()
    (folder / "allowed.txt").write_text("ALLOWED")
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "allowed.txt").write_text("PRIVATE")
    fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    folder.rename(tmp_path / "renamed")
    folder.symlink_to(outside, target_is_directory=True)
    staged = tmp_path / "snapshot"
    staged.mkdir()
    try:
        snapshot_directory(fd, staged)
    finally:
        os.close(fd)
    assert (staged / "allowed.txt").read_text() == "ALLOWED"


def test_snapshot_rejects_oversized_tree(tmp_path):
    folder = tmp_path / "workspace"
    folder.mkdir()
    (folder / "large.bin").write_bytes(b"X" * (32 * 1024 * 1024 + 1))
    staged = tmp_path / "snapshot"
    staged.mkdir()
    fd = os.open(folder, os.O_RDONLY | os.O_DIRECTORY | os.O_NOFOLLOW)
    try:
        with pytest.raises(WorkspaceSnapshotError):
            snapshot_directory(fd, staged)
    finally:
        os.close(fd)
