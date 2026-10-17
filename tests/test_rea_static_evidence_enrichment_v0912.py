"""REA static report gains evidence, never executes inspected applications."""
import io
import struct
import zipfile

from nexus.tools.static_analysis import _identify, _zip_summary


def test_elf_reports_declared_metadata_without_decompilation():
    header = bytearray(64)
    header[:6] = b"\x7fELF\x02\x01"
    struct.pack_into("<H", header, 16, 3)
    struct.pack_into("<H", header, 18, 62)
    struct.pack_into("<Q", header, 24, 0x401000)
    kind, summary = _identify(bytes(header), ".elf")
    assert kind == "ELF"
    assert "x86_64" in summary and "tipo ELF=3" in summary
    assert "0x401000" in summary


def test_pe_reports_declared_sections_and_pe32_plus():
    header = bytearray(256)
    header[:2] = b"MZ"
    struct.pack_into("<I", header, 0x3c, 0x80)
    header[0x80:0x84] = b"PE\0\0"
    struct.pack_into("<H", header, 0x84, 0x8664)
    struct.pack_into("<H", header, 0x86, 5)
    struct.pack_into("<H", header, 0x94, 240)
    struct.pack_into("<H", header, 0x98, 0x20b)
    kind, summary = _identify(bytes(header), ".exe")
    assert kind == "PE"
    assert "seções declaradas=5" in summary
    assert "PE32+" in summary


def test_zip_reports_encryption_and_odd_path_counts_without_paths():
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w") as archive:
        archive.writestr("ordinary.txt", b"safe test")
        archive.writestr("../parent/sensitive.txt", b"fixture")
        archive.writestr("/absolute/member.txt", b"fixture")
    buffer.seek(0)
    kind, summary = _zip_summary(buffer, ".zip")
    assert kind == "ZIP"
    assert "caminhos atípicos=2" in summary
    assert "entradas criptografadas=0" in summary
    assert "sensitive.txt" not in summary
