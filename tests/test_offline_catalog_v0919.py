"""Inventário offline não percorre subpastas nem segue links simbólicos."""
from pathlib import Path

import pytest

from nexus.knowledge.offline_catalog import OfflineCatalogError, list_offline_materials
from nexus.security.paths import PathSecurity


def guard_for(tmp_path):
    guard = PathSecurity()
    guard.home = tmp_path.resolve()
    return guard


def test_catalog_scans_only_selected_folder(tmp_path):
    (tmp_path / "a.zim").write_bytes(b"ZIM")
    (tmp_path / "curso.pdf").write_bytes(b"PDF")
    (tmp_path / "private.key").write_bytes(b"not material")
    sub = tmp_path / "outro"
    sub.mkdir()
    (sub / "hidden.mp4").write_bytes(b"course")
    (tmp_path / "link.zim").symlink_to(tmp_path / "a.zim")
    records = list_offline_materials(tmp_path, guard_for(tmp_path))
    assert [item.filename for item in records] == ["curso.pdf", "a.zim"]
    assert records[1].bytes == 3


def test_catalog_respects_max_entries(tmp_path):
    for index in range(301):
        (tmp_path / f"file{index}.txt").touch()
    with pytest.raises(OfflineCatalogError, match="300"):
        list_offline_materials(tmp_path, guard_for(tmp_path))


def test_catalog_rejects_symlinked_directory(tmp_path):
    actual = tmp_path / "folder"
    actual.mkdir()
    (tmp_path / "link").symlink_to(actual, target_is_directory=True)
    with pytest.raises(OfflineCatalogError):
        list_offline_materials(tmp_path / "link", guard_for(tmp_path))
