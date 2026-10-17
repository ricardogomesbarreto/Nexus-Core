"""Bounded local image and document actions reached through the Nexus consent gate.

The optional Craft CLIs remain separate binaries. No arbitrary engine command,
MCP server, network endpoint or shell snippet is accepted from the model.
"""

import io
import os
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind


_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_MAX_INPUT = 20 * 1024 * 1024
_MAX_OUTPUT = 25 * 1024 * 1024


def _write_new(policy: PathSecurity, destination: str, data: bytes) -> str:
    """Create only a new file under a pinned, non-symlink parent directory."""
    raw, _ = policy._components(destination)
    if raw == policy.home or len(data) > _MAX_OUTPUT:
        raise ValueError("Destino inválido ou arquivo muito grande.")
    with policy.open_directory(raw.parent) as (parent_fd, _):
        fd = os.open(raw.name, os.O_WRONLY | os.O_CREAT | os.O_EXCL |
                     os.O_NOFOLLOW | os.O_CLOEXEC, 0o600, dir_fd=parent_fd)
        try:
            with os.fdopen(fd, "wb") as stream:
                fd = -1
                stream.write(data)
        except BaseException:
            if fd >= 0:
                os.close(fd)
            os.unlink(raw.name, dir_fd=parent_fd)
            raise
    return str(raw)


def _read_source(policy: PathSecurity, path: str, limit: int = _MAX_INPUT) -> bytes:
    with policy.open_regular_file(path) as (fd, _):
        if os.fstat(fd).st_size > limit:
            raise ValueError("Arquivo de origem excede o limite local.")
        data = bytearray()
        while len(data) <= limit:
            chunk = os.read(fd, min(65536, limit + 1 - len(data)))
            if not chunk:
                break
            data.extend(chunk)
        if len(data) > limit:
            raise ValueError("Arquivo de origem excede o limite local.")
        return bytes(data)


class EditImageTool(NexusTool):
    name = "edit_image_local"
    description = ("Edita uma foto local com Pillow: grayscale, invert, blur, "
                   "sharpen, rotate_left ou rotate_right; salva uma cópia nova.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True),
                FieldSpec("operation", ValueKind.STRING, nonempty=True)),
        resources=(ResourceSpec("source", "source"), ResourceSpec("output", "output")),
        outputs=(FieldSpec("path", ValueKind.STRING),
                 FieldSpec("operation", ValueKind.STRING)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),
                SensitiveResource("output", kwargs["output"]))

    def execute(self, source: str, output: str, operation: str, **kwargs) -> ToolResult:
        try:
            from PIL import Image, ImageFilter, ImageOps, UnidentifiedImageError
            if operation not in {"grayscale", "invert", "blur", "sharpen",
                                 "rotate_left", "rotate_right"}:
                raise ValueError("Edição não suportada. Escolha uma operação disponível.")
            suffix = Path(output).suffix.lower()
            if Path(source).suffix.lower() not in _IMAGE_EXTENSIONS or suffix not in _IMAGE_EXTENSIONS:
                raise ValueError("Use arquivos PNG, JPEG ou WebP.")
            policy = self.path_security or PathSecurity()
            content = _read_source(policy, source, 12 * 1024 * 1024)
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as raw:
                    if raw.format not in {"PNG", "JPEG", "WEBP"} or (
                        raw.width > 4096 or raw.height > 4096 or
                        raw.width * raw.height > 8_000_000
                    ):
                        raise ValueError("Imagem não suportada ou maior que 8 megapixels.")
                    raw.load()
                    image = ImageOps.exif_transpose(raw).convert("RGB")
            if operation == "grayscale":
                image = ImageOps.grayscale(image).convert("RGB")
            elif operation == "invert":
                image = ImageOps.invert(image)
            elif operation == "blur":
                image = image.filter(ImageFilter.GaussianBlur(radius=2))
            elif operation == "sharpen":
                image = image.filter(ImageFilter.UnsharpMask(radius=2, percent=140))
            elif operation == "rotate_left":
                image = image.transpose(Image.Transpose.ROTATE_90)
            else:
                image = image.transpose(Image.Transpose.ROTATE_270)
            result = io.BytesIO()
            image.save(result, format={".png": "PNG", ".jpg": "JPEG",
                                       ".jpeg": "JPEG", ".webp": "WEBP"}[suffix])
            path = _write_new(policy, output, result.getvalue())
            return ToolResult(True, self.name, data={"path": path, "operation": operation})
        except ImportError:
            return ToolResult(False, self.name, error="Instale o suporte local de imagens: pip install -e '.[vision]'.")
        except (ValueError, OSError, PermissionError, UnidentifiedImageError,
                Image.DecompressionBombWarning) as exc:
            return ToolResult(False, self.name, error=f"Edição não concluída: {type(exc).__name__}.")


class CreateGraphicTool(NexusTool):
    name = "create_graphic_local"
    description = ("Cria um cartaz gráfico local PNG com título e cores da marca; "
                   "não gera fotografias por IA. Salva uma cópia nova.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("title", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True)),
        resources=(ResourceSpec("output", "output"),),
        outputs=(FieldSpec("path", ValueKind.STRING),),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("output", kwargs["output"]),)

    def execute(self, title: str, output: str, **kwargs) -> ToolResult:
        try:
            from PIL import Image, ImageDraw, ImageFont
            if (not 1 <= len(title.strip()) <= 100 or "\x00" in title or
                    Path(output).suffix.lower() != ".png"):
                raise ValueError("Título ou destino inválido.")
            image = Image.new("RGB", (1200, 675), "#241c24")
            canvas = ImageDraw.Draw(image)
            for y in range(675):
                canvas.line((0, y, 1200, y), fill=(36 + y // 65, 28 + y // 80, 36 + y // 70))
            canvas.rounded_rectangle((55, 55, 1145, 620), radius=32,
                                     outline="#bb8999", width=3)
            canvas.rounded_rectangle((90, 95, 235, 109), radius=7, fill="#9ee6b6")
            font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
            font = ImageFont.truetype(font_path, 56) if Path(font_path).is_file() else ImageFont.load_default()
            words = title.strip().split()
            rows, line = [], ""
            for word in words:
                candidate = f"{line} {word}".strip()
                if canvas.textbbox((0, 0), candidate, font=font)[2] > 960 and line:
                    rows.append(line)
                    line = word
                else:
                    line = candidate
            rows.append(line)
            if len(rows) > 5 or any(canvas.textbbox((0, 0), row, font=font)[2] > 960 for row in rows):
                raise ValueError("Título longo demais para o cartaz.")
            y = 190
            for row in rows:
                canvas.text((95, y), row, fill="#ffffff", font=font)
                y += 78
            canvas.rectangle((95, 555, 1105, 558), fill="#bb8999")
            result = io.BytesIO()
            image.save(result, format="PNG")
            path = _write_new(self.path_security or PathSecurity(), output, result.getvalue())
            return ToolResult(True, self.name, data={"path": path})
        except ImportError:
            return ToolResult(False, self.name, error="Instale o suporte local de imagens: pip install -e '.[vision]'.")
        except (ValueError, OSError, PermissionError) as exc:
            return ToolResult(False, self.name, error=f"Cartaz não criado: {type(exc).__name__}.")


class CraftConvertTool(NexusTool):
    name = "craft_convert_local"
    description = ("Usa CLI local instalado: PhotoCraft para converter imagem, "
                   "WordCraft para converter documento, PdfCraft para extrair texto PDF. "
                   "Informe source, output e kind (image, document ou pdf_text).")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True),
                FieldSpec("kind", ValueKind.STRING, nonempty=True)),
        resources=(ResourceSpec("source", "source"), ResourceSpec("output", "output")),
        outputs=(FieldSpec("path", ValueKind.STRING), FieldSpec("kind", ValueKind.STRING)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),
                SensitiveResource("output", kwargs["output"]))

    def execute(self, source: str, output: str, kind: str, **kwargs) -> ToolResult:
        options = {
            "image": ("photocraft-cli", {".png", ".jpg", ".jpeg", ".psd", ".pcraft", ".webp"},
                      {".png", ".jpg", ".jpeg", ".webp", ".pcraft"}),
            "document": ("wordcraft-cli", {".docx", ".odt", ".md", ".txt"},
                         {".docx", ".pdf", ".md", ".txt"}),
            "pdf_text": ("pdfcraft-cli", {".pdf"}, {".txt"}),
        }
        if kind not in options:
            return ToolResult(False, self.name, error="Tipo de conversão indisponível.")
        binary, input_types, output_types = options[kind]
        source_ext, output_ext = Path(source).suffix.lower(), Path(output).suffix.lower()
        if source_ext not in input_types or output_ext not in output_types:
            return ToolResult(False, self.name, error="Formato de entrada ou saída não suportado.")
        executable = shutil.which(binary)
        if executable is None:
            return ToolResult(False, self.name, error=f"CLI local opcional não instalado: {binary}.")
        try:
            policy = self.path_security or PathSecurity()
            data = _read_source(policy, source)
            with tempfile.TemporaryDirectory(prefix="nexus-craft-") as directory:
                work = Path(directory)
                infile = work / ("entrada" + source_ext)
                outfile = work / ("saida" + output_ext)
                infile.write_bytes(data)
                if kind == "image":
                    args = [executable, "convert", str(infile), str(outfile)]
                elif kind == "document":
                    args = [executable, "convert", str(infile), str(outfile)]
                else:
                    args = [executable, "text", str(infile)]
                with open(outfile, "wb") if kind == "pdf_text" else open(os.devnull, "wb") as stream:
                    result = subprocess.run(args, cwd=directory, stdin=subprocess.DEVNULL,
                                            stdout=stream, stderr=subprocess.DEVNULL,
                                            timeout=90, check=False)
                if result.returncode != 0 or not outfile.is_file():
                    raise ValueError("O programa local não conseguiu converter o arquivo.")
                if outfile.stat().st_size > _MAX_OUTPUT:
                    raise ValueError("Resultado maior que o limite local.")
                saved = _write_new(policy, output, outfile.read_bytes())
            return ToolResult(True, self.name, data={"path": saved, "kind": kind})
        except (OSError, PermissionError, ValueError, subprocess.TimeoutExpired) as exc:
            return ToolResult(False, self.name,
                              error=f"Conversão local não concluída: {type(exc).__name__}.")
