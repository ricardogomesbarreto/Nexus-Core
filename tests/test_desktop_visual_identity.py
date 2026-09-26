import json
import struct
from pathlib import Path
from xml.etree import ElementTree as ET


ROOT = Path(__file__).resolve().parents[1]
BRAND = ROOT / "assets" / "brand"
ICONS = ROOT / "assets" / "icons"
UI = ICONS / "ui"

EXPECTED_UI_ICONS = {
    "add",
    "attention",
    "back",
    "close",
    "confirm",
    "credentials",
    "delete",
    "edit",
    "forward",
    "history",
    "menu",
    "notifications",
    "overview",
    "profile",
    "protected-access",
    "refresh",
    "search",
    "system",
}


def test_desktop_visual_identity_assets_exist():
    assert (BRAND / "nexus-core-logo.png").is_file()
    assert (ICONS / "desktop-manifest.json").is_file()
    assert (ICONS / "nexus-core.svg").is_file()
    assert (ICONS / "nexus-core-symbolic.svg").is_file()

    assert {path.stem for path in UI.glob("*.svg")} == EXPECTED_UI_ICONS


def test_desktop_manifest_contract():
    manifest = json.loads(
        (ICONS / "desktop-manifest.json").read_text(encoding="utf-8")
    )

    assert manifest["platform"] == "desktop-native"
    assert manifest["web_application"] is False
    assert manifest["format"] == "SVG"
    assert manifest["primary_color"] == "#722F37"

    icons = manifest["icons"]

    assert len(icons) == 18
    assert {item["id"] for item in icons} == EXPECTED_UI_ICONS

    for item in icons:
        assert (ICONS / item["path"]).is_file()


def test_official_logo_png_contract():
    data = (BRAND / "nexus-core-logo.png").read_bytes()

    assert data[:8] == b"\x89PNG\r\n\x1a\n"

    width, height, bit_depth, color_type = struct.unpack(
        ">IIBB",
        data[16:26],
    )

    assert (width, height) == (2048, 682)
    assert bit_depth == 8
    assert color_type == 6


def test_desktop_svg_assets_are_valid_local_xml():
    paths = [
        ICONS / "nexus-core.svg",
        ICONS / "nexus-core-symbolic.svg",
        *sorted(UI.glob("*.svg")),
    ]

    assert len(paths) == 20

    for path in paths:
        root = ET.parse(path).getroot()

        assert root.tag.split("}")[-1] == "svg"

        for element in root.iter():
            tag = element.tag.split("}")[-1]

            assert tag not in {
                "script",
                "foreignObject",
                "image",
            }

            for attribute, value in element.attrib.items():
                if attribute.endswith("href"):
                    assert not value.lower().startswith(
                        (
                            "http:",
                            "https:",
                            "file:",
                            "javascript:",
                        )
                    )
