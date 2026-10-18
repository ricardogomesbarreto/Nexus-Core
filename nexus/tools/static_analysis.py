"""REA-inspired local *static* artifact triage for NEXUS CORE.

This deliberately does not run, import, disassemble, decompile or attach to a
target. It does not start REA/MCP, invoke Node/Ghidra, download dependencies,
access the network, or write target bytes to the Nexus conversation archive.
The source is read through the same descriptor-pinned home policy as Craft.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import stat
import struct
import zipfile
from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.tools.wasm_structure import summarize_wasm
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind


MAX_FILE_BYTES = 128 * 1024 * 1024
MAX_HEADER_BYTES = 128 * 1024
MAX_ARCHIVE_MEMBERS = 3000
MAX_JS_SCAN_BYTES = 128 * 1024


def _identify(header: bytes, suffix: str) -> tuple[str, str]:
    """Return only grounded facts, not guesses about the target's behavior."""
    if header.startswith(b"\x7fELF") and len(header) >= 20:
        width = {1: "32", 2: "64"}.get(header[4], "desconhecida")
        endian = {1: "<", 2: ">"}.get(header[5])
        machine = "desconhecida"
        details = ""
        if endian:
            code = struct.unpack_from(endian + "H", header, 18)[0]
            label = {3: "x86", 40: "ARM", 62: "x86_64", 183: "AArch64", 243: "RISC-V"}.get(code, "não mapeada")
            machine = f"{code} ({label})"
            expected = 64 if width == "64" else 52 if width == "32" else 0
            if expected and len(header) >= expected:
                file_type = struct.unpack_from(endian + "H", header, 16)[0]
                address_fmt = "Q" if width == "64" else "I"
                entry = struct.unpack_from(endian + address_fmt, header, 24)[0]
                details = f" tipo ELF={file_type}; entrada declarada=0x{entry:x}."
        return "ELF", f"Binário Linux/Unix; classe={width} bits; código de arquitetura={machine}.{details}"
    if header[:2] == b"MZ" and len(header) >= 64:
        offset = struct.unpack_from("<I", header, 0x3c)[0]
        if offset <= len(header) - 26 and header[offset:offset + 4] == b"PE\0\0":
            machine = struct.unpack_from("<H", header, offset + 4)[0]
            sections = struct.unpack_from("<H", header, offset + 6)[0]
            optional_size = struct.unpack_from("<H", header, offset + 20)[0]
            details = ""
            if optional_size >= 2 and offset + 26 <= len(header):
                magic = struct.unpack_from("<H", header, offset + 24)[0]
                variant = {0x10b: "PE32", 0x20b: "PE32+"}.get(magic, "não identificada")
                details = f" variante={variant}."
            return "PE", (
                f"Executável Windows PE; arquitetura código={machine}; "
                f"seções declaradas={sections}.{details}"
            )
        return "MZ", "Cabeçalho MZ; assinatura PE não confirmada na amostra limitada."
    if len(header) >= 4 and header[:4] in (
        bytes.fromhex("feedface"), bytes.fromhex("cefaedfe"),
        bytes.fromhex("feedfacf"), bytes.fromhex("cffaedfe"),
        bytes.fromhex("cafebabe"), bytes.fromhex("bebafeca"),
    ):
        return "Mach-O", "Formato de executável Mach-O/fat reconhecido por assinatura."
    if header.startswith(b"\0asm") and len(header) >= 8:
        return "WASM", f"WebAssembly; versão={int.from_bytes(header[4:8], 'little')}."
    if header.startswith(b"%PDF-"):
        return "PDF", "Documento PDF; extração de texto pode ser solicitada separadamente."
    if header.startswith(bytes.fromhex("89504e470d0a1a0a")):
        return "PNG", "Imagem PNG; descrição visual é uma operação separada com consentimento."
    if header.startswith(bytes.fromhex("ffd8ff")):
        return "JPEG", "Imagem JPEG; análise visual precisa de autorização separada."
    if header.startswith(b"RIFF") and header[8:12] == b"WEBP":
        return "WEBP", "Imagem WebP identificada por assinatura; conteúdo visual não analisado."
    if header[:4] in (b"II\x2a\x00", b"MM\x00\x2a",
                      b"II\x2b\x00", b"MM\x00\x2b"):
        return "TIFF", "Imagem TIFF/BigTIFF identificada por assinatura; conteúdo visual não analisado."
    if header.startswith((b"GIF87a", b"GIF89a")):
        return "GIF", "Imagem GIF identificada por assinatura; frames não analisados."
    if header[:2] == b"PK":
        return "ZIP", "Contêiner ZIP/JAR/APK; índice será analisado sem extrair membros."
    if suffix == ".asar":
        return "ASAR", "Arquivo Electron ASAR; a análise atual é somente estática."
    if suffix in {".js", ".mjs", ".cjs", ".jsx", ".ts", ".tsx", ".json"}:
        try:
            header.decode("utf-8", errors="strict")
        except UnicodeDecodeError:
            return "DESCONHECIDO", "Texto UTF-8 não confirmado; análise profunda não executada."
        return "CODIGO_TEXTO", "Arquivo de código/texto UTF-8; análise puramente estática."
    return "DESCONHECIDO", "Tipo não identificado pela assinatura e amostra disponíveis."


MAX_ZIP_DIRECTORY_BYTES = 8 * 1024 * 1024


def _check_zip_directory_bounds(stream) -> None:
    """Bound ZIP central directory allocations before instantiating ZipFile.

    The End of Central Directory lives in the last 65557 bytes (22-byte
    record + 65535-byte comment). ZIP64 and multi-disk ZIP are intentionally
    unsupported by the lightweight analyzer; these are not rejected as
    dangerous files, only as beyond the declared local inspection policy.
    """
    stream.seek(0, os.SEEK_END)
    total = stream.tell()
    if total < 22:
        raise ValueError("ZIP sem diretório central.")
    size = min(total, 65557)
    stream.seek(total - size)
    tail = stream.read(size)
    pos = len(tail)
    found = -1
    while True:
        pos = tail.rfind(b"PK\x05\x06", 0, pos)
        if pos < 0:
            break
        if pos + 22 <= len(tail):
            comment_size = struct.unpack_from("<H", tail, pos + 20)[0]
            if pos + 22 + comment_size == len(tail):
                found = pos
                break
    if found < 0:
        raise ValueError("ZIP sem registro EOCD válido.")
    disk, central_disk, entries_disk, entries_total, directory_size, directory_offset = (
        struct.unpack_from("<HHHHII", tail, found + 4)
    )
    if disk or central_disk or entries_disk != entries_total:
        raise ValueError("ZIP multidisco não suportado.")
    if (entries_total == 0xFFFF or directory_size == 0xFFFFFFFF or
            directory_offset == 0xFFFFFFFF):
        raise ValueError("ZIP64 não suportado no índice limitado.")
    if entries_total > MAX_ARCHIVE_MEMBERS or directory_size > MAX_ZIP_DIRECTORY_BYTES:
        raise ValueError("Índice ZIP excede limites de entradas ou memória.")
    if directory_size + directory_offset > total:
        raise ValueError("Limites do índice ZIP inconsistentes.")


def _zip_summary(stream, suffix: str) -> tuple[str, str]:
    """Only inspect the central directory. Never extract or decompress entries."""
    _check_zip_directory_bounds(stream)
    with zipfile.ZipFile(stream, "r") as archive:
        names = archive.namelist()
        if len(names) > MAX_ARCHIVE_MEMBERS:
            raise ValueError("Índice do arquivo compactado excede o limite local.")
        clean_names = set(names)
        entries = archive.infolist()
        total_uncompressed = sum(x.file_size for x in entries)
        encrypted = sum(bool(x.flag_bits & 1) for x in entries)
        symbolic_links = sum((x.external_attr >> 16) & 0o170000 == 0o120000 for x in entries)
        native_libraries = sum(n.lower().endswith(".so") for n in names)
        abi_list = sorted({n.split("/")[1] for n in names
                           if n.startswith("lib/") and n.count("/") >= 2 and
                           n.split("/")[1] in {"x86", "x86_64", "armeabi-v7a", "arm64-v8a"}})
        zip_signatures = sum(n.startswith("META-INF/") and
                             n.upper().endswith((".RSA", ".DSA", ".EC")) for n in names)
        # Report index characteristics, not a malware verdict or a path.
        odd_paths = sum(
            n.startswith(("/", "\\")) or
            ".." in n.replace("\\", "/").split("/")
            for n in names
        )
        if total_uncompressed > 4 * 1024 * 1024 * 1024:
            raise ValueError("Contêiner compactado declara tamanho excessivo.")
        has_manifest = "AndroidManifest.xml" in clean_names
        dex_count = sum(bool(re.fullmatch(r"classes\d*\.dex", n)) for n in names)
        if suffix == ".apk" and (has_manifest or dex_count):
            kind = "APK"
        elif suffix == ".docx" and {"[Content_Types].xml", "word/document.xml"} <= clean_names:
            kind = "DOCX"
        elif suffix == ".odt" and {"mimetype", "content.xml"} <= clean_names:
            kind = "ODT"
        elif suffix in {".jar", ".war"} and (
            "META-INF/MANIFEST.MF" in clean_names or any(n.endswith(".class") for n in names)
        ):
            kind = "JAR"
        else:
            kind = "ZIP"
        return kind, (
            f"Índice local: {len(names)} entradas; tamanho descompactado declarado="
            f"{total_uncompressed} bytes; AndroidManifest={'sim' if has_manifest else 'não'}; "
            f"arquivos DEX={dex_count}; entradas criptografadas={encrypted}; "
            f"caminhos atípicos={odd_paths}; links simbólicos declarados={symbolic_links}; "
            f"bibliotecas nativas .so={native_libraries}; ABIs conhecidas={','.join(abi_list) or 'nenhuma'}; "
            f"entradas de assinatura declaradas={zip_signatures} (sem verificação criptográfica). "
            "Nenhum membro foi extraído ou executado."
        )


class InspectArtifactTool(NexusTool):
    """Local static triage; delegated read requires individual SecurityGate consent."""

    name = "inspect_artifact_local"
    description = (
        "Identifica formato e características estáticas de arquivo local autorizado "
        "(ELF, PE, Mach-O, WASM, APK/JAR/ZIP, JS/Electron e documentos); "
        "não executa programas, não faz pentest e não usa internet."
    )
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),),
        resources=(ResourceSpec("source", "source"),),
        outputs=(
            FieldSpec("kind", ValueKind.STRING),
            FieldSpec("size_bytes", ValueKind.INTEGER),
            FieldSpec("sha256", ValueKind.STRING),
            FieldSpec("summary", ValueKind.STRING),
        ),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),)

    def execute(self, source: str, **kwargs) -> ToolResult:
        try:
            policy = self.path_security or PathSecurity()
            with policy.open_regular_file(source) as (fd, path):
                before = os.fstat(fd)
                if not stat.S_ISREG(before.st_mode) or not 0 <= before.st_size <= MAX_FILE_BYTES:
                    raise ValueError("Arquivo grande demais para análise estática local.")
                hasher = hashlib.sha256()
                header = bytearray()
                total = 0
                while True:
                    chunk = os.read(fd, 64 * 1024)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > MAX_FILE_BYTES:
                        raise ValueError("Arquivo excede o limite de 128 MiB.")
                    hasher.update(chunk)
                    if len(header) < MAX_HEADER_BYTES:
                        header.extend(chunk[:MAX_HEADER_BYTES - len(header)])
                # The file descriptor is pinned; do not re-open by path.
                after = os.fstat(fd)
                if before.st_dev != after.st_dev or before.st_ino != after.st_ino or total != after.st_size:
                    raise ValueError("Arquivo alterado durante a inspeção.")
                suffix = path.suffix.lower()
                kind, summary = _identify(bytes(header), suffix)
                if kind == "WASM":
                    summary += " " + summarize_wasm(bytes(header), total_size=total)
                elif kind == "ZIP" and total:
                    # os.dup pins the same inode; no extraction of ZIP payload.
                    with os.fdopen(os.dup(fd), "rb") as stream:
                        stream.seek(0)
                        kind, summary = _zip_summary(stream, suffix)
                elif kind == "CODIGO_TEXTO" and suffix != ".json":
                    excerpt = bytes(header[:MAX_JS_SCAN_BYTES]).decode("utf-8")
                    imports = len(re.findall(
                        r"\b(?:import\s+(?!\()|require\s*\(|export\s+)", excerpt,
                    ))
                    summary += (
                        f" Referências sintáticas aproximadas import/require/export="
                        f"{imports}; sem execução ou reconstrução de código."
                    )
                return ToolResult(
                    True, self.name, data={
                        "kind": kind, "size_bytes": total,
                        "sha256": hasher.hexdigest(), "summary": summary,
                    },
                )
        except (OSError, PermissionError, ValueError, zipfile.BadZipFile,
                UnicodeError, struct.error, OverflowError) as exc:
            # Do not reveal file contents, extracted paths or exception text.
            return ToolResult(
                False, self.name,
                error=f"Análise local não concluída: {type(exc).__name__}.",
            )
