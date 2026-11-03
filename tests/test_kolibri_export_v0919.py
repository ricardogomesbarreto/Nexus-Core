"""Safe inspection of exported Kolibri content without running Kolibri."""
import os

import pytest

from nexus.knowledge.kolibri_export import (
    KolibriExportError, inspect_kolibri_export,
)
from nexus.security.paths import PathSecurity


def guard(home):
    policy = PathSecurity()
    policy.home = home.resolve()
    policy.protected_paths = []
    return policy


def export_at(tmp_path):
    folder = tmp_path / "KOLIBRI_DATA"
    databases = folder / "content" / "databases"
    databases.mkdir(parents=True)
    (folder / "content" / "storage").mkdir()
    return folder, databases


def test_only_channel_metadata_no_database_content_reads(tmp_path, monkeypatch):
    folder, db = export_at(tmp_path)
    channel = "0123456789abcdef0123456789abcdef"
    (db / f"{channel}.sqlite3").write_bytes(b"private channel database")
    (db / "db.sqlite3").write_bytes(b"private facility data")
    (db / "not_a_channel.txt").write_bytes(b"ignored")
    found = inspect_kolibri_export(folder, guard(tmp_path))
    assert found.has_content_storage
    assert len(found.channels) == 1
    assert found.channels[0].channel_id == channel
    assert found.channels[0].database_bytes == len(b"private channel database")
    assert not any("private" in str(item) for item in found.channels)


def test_unexported_folder_not_treated_as_kolibri(tmp_path):
    path = tmp_path / "other_folder"
    path.mkdir()
    with pytest.raises(KolibriExportError, match="KOLIBRI_DATA"):
        inspect_kolibri_export(path, guard(tmp_path))


def test_symlinked_database_skipped_and_symlinked_parent_rejected(tmp_path):
    folder, db = export_at(tmp_path)
    target = tmp_path / "private.sqlite3"
    target.write_bytes(b"private")
    (db / ("a" * 32 + ".sqlite3")).symlink_to(target)
    assert inspect_kolibri_export(folder, guard(tmp_path)).channels == ()
    linked = tmp_path / "link"
    linked.symlink_to(folder, target_is_directory=True)
    # Even if caller supplies matching basename at a symlinked directory.
    nested = tmp_path / "linkroot"
    nested.mkdir()
    (nested / "KOLIBRI_DATA").symlink_to(folder, target_is_directory=True)
    with pytest.raises(KolibriExportError):
        inspect_kolibri_export(nested / "KOLIBRI_DATA", guard(tmp_path))


def test_storage_is_optional_and_is_never_enumerated(tmp_path, monkeypatch):
    folder, db = export_at(tmp_path)
    (folder / "content" / "storage").rmdir()
    (db / ("b" * 32 + ".sqlite3")).write_bytes(b"x")
    found = inspect_kolibri_export(folder, guard(tmp_path))
    assert len(found.channels) == 1 and not found.has_content_storage


def test_entry_count_limit_stops_large_folder(tmp_path):
    folder, db = export_at(tmp_path)
    for index in range(301):
        (db / f"other-{index}.txt").touch()
    with pytest.raises(KolibriExportError, match="entradas demais"):
        inspect_kolibri_export(folder, guard(tmp_path))


def test_channel_count_limit(tmp_path):
    folder, db = export_at(tmp_path)
    for index in range(61):
        (db / f"{index:032x}.sqlite3").write_bytes(b"channel")
    with pytest.raises(KolibriExportError, match="60 canais"):
        inspect_kolibri_export(folder, guard(tmp_path))


def test_nonregular_channel_metadata_is_ignored(tmp_path):
    folder, db = export_at(tmp_path)
    (db / ("f" * 32 + ".sqlite3")).mkdir()
    (db / ("e" * 32 + ".sqlite3")).touch()
    assert inspect_kolibri_export(folder, guard(tmp_path)).channels == ()
