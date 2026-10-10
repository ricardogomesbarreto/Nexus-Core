"""Repository-wide static integrity sweep beyond application unit tests.

Compile all tracked Python modules, validate text/JSON/SVG files and require
real icon and release-documentation targets. No network or extra tools needed.
"""
import json
import pathlib
import tomllib
import xml.etree.ElementTree as ET

from nexus.config.settings import PROJECT_ROOT, settings


TEXT_EXTENSIONS = frozenset({
    ".py", ".md", ".txt", ".toml", ".yml", ".yaml", ".json", ".svg",
})
SKIP_DIRECTORIES = {".git", ".pytest_cache", "__pycache__", ".venv", "venv", ".tox"}


def source_files():
    for path in PROJECT_ROOT.rglob("*"):
        if not path.is_file() or any(part in SKIP_DIRECTORIES for part in path.parts):
            continue
        yield path


def test_all_python_text_json_and_svg_files_have_valid_syntax():
    found = {"py": 0, "json": 0, "svg": 0}
    for path in source_files():
        if path.suffix not in TEXT_EXTENSIONS:
            continue
        text = path.read_text(encoding="utf-8")
        if path.suffix == ".py":
            compile(text, str(path), "exec")
            found["py"] += 1
        elif path.suffix == ".json":
            json.loads(text)
            found["json"] += 1
        elif path.suffix == ".svg":
            ET.fromstring(text)
            found["svg"] += 1
    assert found["py"] >= 80
    assert found["json"] >= 2
    assert found["svg"] >= 20


def test_desktop_asset_manifest_targets_are_real_and_not_absolute():
    folder = PROJECT_ROOT / "assets" / "icons"
    document = json.loads((folder / "desktop-manifest.json").read_text(encoding="utf-8"))
    paths = [document["application_icon"], document["symbolic_icon"]]
    paths += [entry["path"] for entry in document["icons"]]
    assert len(paths) == len(set(paths))
    for name in paths:
        file = pathlib.PurePosixPath(name)
        assert not file.is_absolute() and ".." not in file.parts
        assert (folder / name).is_file()
    app = json.loads((folder / "manifest.json").read_text(encoding="utf-8"))
    assert (folder / app["sprite"]).is_file()


def test_release_history_readme_links_and_version_consistency():
    with (PROJECT_ROOT / "pyproject.toml").open("rb") as handle:
        config = tomllib.load(handle)
    assert settings.version == config["project"]["version"]
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    assert f"v{settings.version}" in readme
    assert (PROJECT_ROOT / "docs" /
            f"RELEASE_NOTES_v{settings.version}.md").is_file()
    for number in ("0.4.0", "0.4.1", "0.5.0", "0.6.0", "0.6.1", "0.6.2", "0.6.3", "0.7.0", "0.7.1", "0.7.2", "0.7.3", "0.8.0", "0.8.1", "0.8.2", "0.8.3", "0.8.4", "0.8.5"):
        assert f"v{number}" in readme
        assert (PROJECT_ROOT / "docs" / f"RELEASE_NOTES_v{number}.md").is_file()
