"""Manual acceptance of the REAL optional Craft CLIs on the Linux host.

Read-only by default. --smoke deliberately runs installed binaries against
small synthetic files inside a private temporary directory. This is not a
sandbox: only run trusted locally installed executables. Never invokes MCP,
npx, REA setup, network downloads, Ollama, or changes system services.
"""
from __future__ import annotations

import argparse
import os
from pathlib import Path
import shutil
import struct
import subprocess
import tempfile
import zipfile
import zlib


CRAFT = {
    "PhotoCraft": ("photocraft-cli", "convert"),
    "WordCraft": ("wordcraft-cli", "convert"),
    "PdfCraft": ("pdfcraft-cli", "text"),
}
_TIMEOUT = 60
_MAX_RESULT = 25 * 1024 * 1024


def _execute(argv: list[str], *, stdout=None, timeout: int = _TIMEOUT) -> bool:
    try:
        result = subprocess.run(
            argv, stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL if stdout is None else stdout,
            stderr=subprocess.DEVNULL, timeout=timeout, check=False,
        )
        return result.returncode == 0
    except (OSError, subprocess.TimeoutExpired):
        return False


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return (
        struct.pack(">I", len(data)) + kind + data +
        struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    )


def _write_png(path: Path) -> None:
    """A genuine 1x1 RGB PNG, built without third-party dependencies."""
    ihdr = struct.pack(">IIBBBBB", 1, 1, 8, 2, 0, 0, 0)
    data = zlib.compress(b"\x00\x72\x2f\x37")
    path.write_bytes(
        b"\x89PNG\r\n\x1a\n" +
        _png_chunk(b"IHDR", ihdr) +
        _png_chunk(b"IDAT", data) +
        _png_chunk(b"IEND", b"")
    )


def _write_docx(path: Path) -> None:
    """Tiny conforming OOXML document; contents are synthetic."""
    with zipfile.ZipFile(path, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
            '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>'
            '<Default Extension="xml" ContentType="application/xml"/>'
            '<Override PartName="/word/document.xml" '
            'ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>'
            '</Types>'
        ))
        archive.writestr("_rels/.rels", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
            '<Relationship Id="rId1" '
            'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" '
            'Target="word/document.xml"/></Relationships>'
        ))
        archive.writestr("word/document.xml", (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
            '<w:body><w:p><w:r><w:t>NEXUS CORE CLI</w:t></w:r></w:p>'
            '<w:sectPr/></w:body></w:document>'
        ))


def _write_pdf(path: Path) -> None:
    """Tiny valid PDF with a literal test string and correct xref offsets."""
    stream = b"BT /F1 16 Tf 50 160 Td (NEXUS CORE CLI) Tj ET\n"
    objects = [
        b"<< /Type /Catalog /Pages 2 0 R >>",
        b"<< /Type /Pages /Kids [3 0 R] /Count 1 >>",
        b"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 300 220] /Resources << /Font << /F1 5 0 R >> >> /Contents 4 0 R >>",
        b"<< /Length " + str(len(stream)).encode("ascii") + b" >>\nstream\n" + stream + b"endstream",
        b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>",
    ]
    content = bytearray(b"%PDF-1.4\n")
    offsets = [0]
    for n, obj in enumerate(objects, 1):
        offsets.append(len(content))
        content.extend(f"{n} 0 obj\n".encode("ascii") + obj + b"\nendobj\n")
    start = len(content)
    content.extend(f"xref\n0 {len(offsets)}\n".encode("ascii"))
    content.extend(b"0000000000 65535 f \n")
    for offset in offsets[1:]:
        content.extend(f"{offset:010d} 00000 n \n".encode("ascii"))
    content.extend(
        f"trailer\n<< /Size {len(offsets)} /Root 1 0 R >>\nstartxref\n{start}\n%%EOF\n".encode("ascii")
    )
    path.write_bytes(content)


def _valid_output(path: Path, kind: str) -> bool:
    if path.is_symlink() or not path.is_file():
        return False
    size = path.stat().st_size
    if not 0 < size <= _MAX_RESULT:
        return False
    with path.open("rb") as stream:
        header = stream.read(16)
        if kind == "PhotoCraft":
            return header.startswith(b"RIFF") and header[8:12] == b"WEBP"
        if kind == "WordCraft":
            return header.startswith(b"%PDF-")
        if kind == "PdfCraft":
            return b"NEXUS CORE CLI" in header + stream.read(min(size, 1024 * 1024)).upper()
    return False


def smoke_cli(name: str, executable: str, work: Path) -> bool:
    """Exercise the documented real subcommand, never a stand-in mock."""
    if name == "PhotoCraft":
        source, output = work / "photo.png", work / "photo.webp"
        _write_png(source)
        argv = [executable, "convert", str(source), str(output)]
    elif name == "WordCraft":
        source, output = work / "word.docx", work / "word.pdf"
        _write_docx(source)
        argv = [executable, "convert", str(source), str(output)]
    else:
        source, output = work / "paper.pdf", work / "paper.txt"
        _write_pdf(source)
        argv = [executable, "text", str(source)]
    if name == "PdfCraft":
        # The real PDF CLI writes text to stdout; it does not take an out-file.
        with output.open("xb") as stream:
            ok = _execute(argv, stdout=stream)
    else:
        ok = _execute(argv)
    return ok and _valid_output(output, name)


def smoke_advanced_cli(name: str, executable: str, work: Path) -> bool:
    """Run info, Word text and PdfCraft render/extract on synthetic files."""
    from nexus.tools.craft_inspect import _safe_summary
    from nexus.tools.pdf_extract import _validate_pdf_copy
    from nexus.tools.pdf_render import _validate_png

    kind = {"PhotoCraft": "image", "WordCraft": "document", "PdfCraft": "pdf"}[name]
    filename = {"PhotoCraft": "info.png", "WordCraft": "info.docx", "PdfCraft": "info.pdf"}[name]
    source = work / filename
    if name == "PhotoCraft":
        _write_png(source)
    elif name == "WordCraft":
        _write_docx(source)
    else:
        _write_pdf(source)
    result = work / (name.lower() + "-info.json")
    with result.open("xb") as stream:
        ok = _execute([executable, "info", str(source)], stdout=stream)
    if not ok or result.stat().st_size > 512 * 1024:
        return False
    try:
        _safe_summary(kind, result.read_bytes())
    except (ValueError, UnicodeError):
        return False
    if name == "WordCraft":
        out = work / "word-text.txt"
        with out.open("xb") as stream:
            ok = _execute([executable, "text", str(source)], stdout=stream)
        if (not ok or out.stat().st_size > _MAX_RESULT or
                b"NEXUS CORE CLI" not in out.read_bytes()):
            return False
    if name == "PdfCraft":
        out = work / "pdf-preview.png"
        args = [executable, "render", str(source), "--page", "1",
                "--dpi", "96", "--out", str(out)]
        if not _execute(args):
            return False
        if out.is_symlink() or not out.is_file() or out.stat().st_size > _MAX_RESULT:
            return False
        try:
            _validate_png(out.read_bytes())
        except (ValueError, OSError):
            return False
        extract = work / "pdf-extract.pdf"
        if not _execute([executable, "extract", str(source), "--pages", "1",
                         "--out", str(extract)]):
            return False
        if extract.is_symlink() or not extract.is_file() or extract.stat().st_size > _MAX_RESULT:
            return False
        try:
            _validate_pdf_copy(extract.read_bytes())
        except (ValueError, OSError):
            return False
    return True


def run(*, smoke: bool = False, rea: bool = False, advanced: bool = False) -> int:
    failures = 0
    with tempfile.TemporaryDirectory(prefix="nexus-cli-acceptance-") as folder:
        work = Path(folder)
        for name, (binary, _) in CRAFT.items():
            executable = shutil.which(binary)
            if not executable:
                print(f"[CLI-LOCAL] ferramenta={name} estado=ausente")
                failures += 1
                continue
            if not _execute([executable, "--help"], timeout=12):
                print(f"[CLI-LOCAL] ferramenta={name} estado=ajuda_falhou")
                failures += 1
                continue
            if not smoke:
                print(f"[CLI-LOCAL] ferramenta={name} estado=cli_detectado teste=nao_executado")
                continue
            ok = smoke_cli(name, executable, work)
            print(f"[CLI-LOCAL] ferramenta={name} estado={'passou' if ok else 'falhou'} teste=conversao_real")
            failures += not ok
            if advanced:
                passed = smoke_advanced_cli(name, executable, work)
                print(f"[CLI-LOCAL] ferramenta={name} estado={'passou' if passed else 'falhou'} teste=metadados_e_previa")
                failures += not passed
        if rea:
            executable = shutil.which("rea")
            if not executable:
                print("[CLI-LOCAL] ferramenta=REA estado=ausente")
                failures += 1
            else:
                # Discover the optional installed CLI without running a target,
                # setup, a provider, or the REA MCP server.
                ok = _execute([executable, "--help"], timeout=12)
                print(f"[CLI-LOCAL] ferramenta=REA estado={'cli_detectado' if ok else 'falhou'} teste=sem_alvo")
                failures += not ok
    return int(bool(failures))


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--smoke", action="store_true",
                        help="Executar conversoes reais apenas em arquivos sinteticos temporarios")
    parser.add_argument("--rea", action="store_true",
                        help="Verificar o comando REA instalado sem analisar arquivos")
    parser.add_argument("--advanced", action="store_true",
                        help="Acrescentar testes reais de info, Word text, PDF render/extract; exige --smoke")
    options = parser.parse_args()
    if options.advanced and not options.smoke:
        parser.error("--advanced exige --smoke para confirmação explícita da execução")
    return run(smoke=options.smoke, rea=options.rea, advanced=options.advanced)


if __name__ == "__main__":
    raise SystemExit(main())
