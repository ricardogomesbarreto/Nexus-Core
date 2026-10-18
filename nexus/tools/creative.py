"""Bounded local image and document actions reached through the Nexus consent gate.

The optional Craft CLIs remain separate binaries. No arbitrary engine command,
MCP server, network endpoint or shell snippet is accepted from the model.
"""

import io
import os
import selectors
import shutil
import subprocess
import tempfile
import time
import warnings
from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.security.paths import PathSecurity
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind


_IMAGE_EXTENSIONS = frozenset({".png", ".jpg", ".jpeg", ".webp"})
_MAX_INPUT = 20 * 1024 * 1024
_MAX_OUTPUT = 25 * 1024 * 1024


def _bounded_stdout(args: list[str], output: Path, directory: str, *, timeout: int = 90) -> None:
    """Write CLI text output with an absolute byte/time budget."""
    with output.open("xb") as target:
        process = subprocess.Popen(args, cwd=directory, stdin=subprocess.DEVNULL,
                                   stdout=subprocess.PIPE, stderr=subprocess.DEVNULL,
                                   close_fds=True)
        deadline = time.monotonic() + timeout
        total = 0
        try:
            assert process.stdout is not None
            with selectors.DefaultSelector() as selector:
                selector.register(process.stdout, selectors.EVENT_READ)
                while True:
                    remaining = deadline - time.monotonic()
                    if remaining <= 0 or not selector.select(remaining):
                        raise subprocess.TimeoutExpired(args, timeout)
                    chunk = os.read(process.stdout.fileno(), 65536)
                    if not chunk:
                        break
                    total += len(chunk)
                    if total > _MAX_OUTPUT:
                        raise ValueError("Saída de texto excede o limite local.")
                    target.write(chunk)
            process.wait(timeout=max(0.01, deadline - time.monotonic()))
            if process.returncode:
                raise ValueError("O CLI não extraiu o texto solicitado.")
        finally:
            if process.poll() is None:
                process.kill()
            process.wait()
            if process.stdout is not None:
                process.stdout.close()


def _validate_converted_output(data: bytes, extension: str) -> None:
    """Reject empty or obviously mismatched formats before saving a result.

    Magic bytes do not certify conversion correctness, but prevent a CLI that
    exits zero without producing a usable file from reporting success.
    """
    if not data:
        raise ValueError("O conversor produziu um arquivo vazio.")
    signatures = {
        ".pdf": data.startswith(bytes.fromhex("255044462d")),
        ".png": data.startswith(bytes.fromhex("89504e470d0a1a0a")),
        ".jpg": data.startswith(bytes.fromhex("ffd8ff")),
        ".jpeg": data.startswith(bytes.fromhex("ffd8ff")),
        ".webp": data.startswith(b"RIFF") and data[8:12] == b"WEBP",
        ".tif": data.startswith((b"II\x2a\x00", b"MM\x00\x2a")),
        ".tiff": data.startswith((b"II\x2a\x00", b"MM\x00\x2a")),
        ".rtf": data.startswith(b"{\\rtf"),
        ".docx": data.startswith(bytes.fromhex("504b0304")),
        ".odt": data.startswith(bytes.fromhex("504b0304")),
    }
    if extension in signatures and not signatures[extension]:
        raise ValueError("O conversor produziu um formato incompatível.")


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
    description = ("Edita foto local com Pillow: grayscale, invert, blur, sharpen, "
                   "rotate_left, rotate_right, autocontrast, sepia, "
                   "flip_horizontal, flip_vertical, brighten ou contrast; "
                   "salva uma cópia nova.")
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
            from PIL import Image, ImageEnhance, ImageFilter, ImageOps, UnidentifiedImageError
            if operation not in {"grayscale", "invert", "blur", "sharpen",
                                 "rotate_left", "rotate_right", "autocontrast",
                                 "sepia", "flip_horizontal", "flip_vertical",
                                 "brighten", "contrast"}:
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
                    oriented = ImageOps.exif_transpose(raw)
                    # Color effects must not turn an edited PNG/WebP into an
                    # opaque image. Keep the original alpha separate so blur
                    # and sharpening do not change its transparency either.
                    alpha = (oriented.convert("RGBA").getchannel("A")
                             if "A" in oriented.getbands() or
                             "transparency" in oriented.info else None)
                    image = oriented.convert("RGB")
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
                if alpha is not None:
                    alpha = alpha.transpose(Image.Transpose.ROTATE_90)
            elif operation == "rotate_right":
                image = image.transpose(Image.Transpose.ROTATE_270)
                if alpha is not None:
                    alpha = alpha.transpose(Image.Transpose.ROTATE_270)
            elif operation == "autocontrast":
                image = ImageOps.autocontrast(image)
            elif operation == "sepia":
                image = ImageOps.colorize(ImageOps.grayscale(image), "#30201b", "#f4d8a6")
            elif operation == "flip_horizontal":
                image = image.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
                if alpha is not None:
                    alpha = alpha.transpose(Image.Transpose.FLIP_LEFT_RIGHT)
            elif operation == "flip_vertical":
                image = image.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
                if alpha is not None:
                    alpha = alpha.transpose(Image.Transpose.FLIP_TOP_BOTTOM)
            elif operation == "brighten":
                image = ImageEnhance.Brightness(image).enhance(1.25)
            elif operation == "contrast":
                image = ImageEnhance.Contrast(image).enhance(1.3)
            if alpha is not None:
                if suffix in {".jpg", ".jpeg"}:
                    background = Image.new("RGB", image.size, "white")
                    background.paste(image, mask=alpha)
                    image = background
                else:
                    image = image.convert("RGBA")
                    image.putalpha(alpha)
            # A fresh canvas excludes source metadata, including location.
            fresh = Image.new(image.mode, image.size)
            fresh.paste(image)
            result = io.BytesIO()
            fresh.save(result, format={".png": "PNG", ".jpg": "JPEG",
                                       ".jpeg": "JPEG", ".webp": "WEBP"}[suffix])
            path = _write_new(policy, output, result.getvalue())
            return ToolResult(True, self.name, data={"path": path, "operation": operation})
        except ImportError:
            return ToolResult(False, self.name, error="Instale o suporte local de imagens: pip install -e '.[vision]'.")
        except (ValueError, OSError, PermissionError, UnidentifiedImageError,
                Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
            return ToolResult(False, self.name, error=f"Edição não concluída: {type(exc).__name__}.")


class ImageGeometryTool(NexusTool):
    """Crop or resize one authorized raster, never modifying the input."""

    name = "image_geometry_local"
    description = ("Recorta ou redimensiona foto local PNG/JPEG/WebP. "
                   "Informe source, output, operation (crop ou resize), "
                   "x, y, width e height em pixels. Salva uma cópia nova.")
    risk_level = RiskLevel.MEDIUM
    path_security = None
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("source", ValueKind.STRING, nonempty=True),
                FieldSpec("output", ValueKind.STRING, nonempty=True),
                FieldSpec("operation", ValueKind.STRING, nonempty=True),
                FieldSpec("x", ValueKind.INTEGER), FieldSpec("y", ValueKind.INTEGER),
                FieldSpec("width", ValueKind.INTEGER), FieldSpec("height", ValueKind.INTEGER)),
        resources=(ResourceSpec("source", "source"), ResourceSpec("output", "output")),
        outputs=(FieldSpec("path", ValueKind.STRING), FieldSpec("operation", ValueKind.STRING),
                 FieldSpec("width", ValueKind.INTEGER), FieldSpec("height", ValueKind.INTEGER)),
    )

    def sensitive_resources(self, **kwargs):
        return (SensitiveResource("source", kwargs["source"]),
                SensitiveResource("output", kwargs["output"]))

    def execute(self, source: str, output: str, operation: str,
                x: int, y: int, width: int, height: int, **kwargs) -> ToolResult:
        try:
            from PIL import Image, ImageOps, UnidentifiedImageError
            suffix = Path(output).suffix.lower()
            if (operation not in {"crop", "resize"} or
                    Path(source).suffix.lower() not in _IMAGE_EXTENSIONS or
                    suffix not in _IMAGE_EXTENSIONS or
                    not (0 <= x <= 4096 and 0 <= y <= 4096 and
                         1 <= width <= 4096 and 1 <= height <= 4096 and
                         width * height <= 8_000_000) or
                    (operation == "resize" and (x != 0 or y != 0))):
                raise ValueError("Medidas, formato ou operação inválidos.")
            policy = self.path_security or PathSecurity()
            content = _read_source(policy, source, 12 * 1024 * 1024)
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(content)) as raw:
                    if (raw.format not in {"PNG", "JPEG", "WEBP"} or
                            raw.width > 4096 or raw.height > 4096 or
                            raw.width * raw.height > 8_000_000):
                        raise ValueError("Imagem de origem fora dos limites.")
                    raw.load()
                    oriented = ImageOps.exif_transpose(raw)
                    mode = ("RGBA" if "A" in oriented.getbands() or
                            "transparency" in oriented.info else "RGB")
                    image = oriented.convert(mode)
            if operation == "crop":
                if x + width > image.width or y + height > image.height:
                    raise ValueError("O recorte ultrapassa a imagem.")
                image = image.crop((x, y, x + width, y + height))
            else:
                image = image.resize((width, height), Image.Resampling.LANCZOS)
            # A fresh canvas discards source metadata (including location).
            fresh = Image.new(image.mode, image.size)
            fresh.paste(image)
            if suffix in {".jpg", ".jpeg"} and fresh.mode == "RGBA":
                background = Image.new("RGB", fresh.size, "white")
                background.paste(fresh, mask=fresh.getchannel("A"))
                fresh = background
            encoded = io.BytesIO()
            fresh.save(encoded, format={".png": "PNG", ".jpg": "JPEG",
                                        ".jpeg": "JPEG", ".webp": "WEBP"}[suffix])
            saved = _write_new(policy, output, encoded.getvalue())
            return ToolResult(True, self.name, data={"path": saved, "operation": operation,
                                                      "width": width, "height": height})
        except ImportError:
            return ToolResult(False, self.name, error="Instale o suporte local de imagens: pip install -e '.[vision]'.")
        except (ValueError, OSError, PermissionError, UnidentifiedImageError,
                Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
            return ToolResult(False, self.name,
                              error=f"Transformação não concluída: {type(exc).__name__}.")


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
            # Font paths vary between Debian/Ubuntu, Fedora and Arch.
            # Keep the same palette without requiring a distro-specific font.
            font = None
            for font_path in (
                "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
                "/usr/share/fonts/dejavu-sans-fonts/DejaVuSans.ttf",
                "/usr/share/fonts/TTF/DejaVuSans.ttf",
                "/usr/share/fonts/truetype/liberation2/LiberationSans-Regular.ttf",
                "/usr/share/fonts/liberation-sans/LiberationSans-Regular.ttf",
            ):
                if Path(font_path).is_file():
                    try:
                        font = ImageFont.truetype(font_path, 56)
                        break
                    except OSError:
                        pass
            if font is None:
                font = ImageFont.load_default(size=56)
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
                   "WordCraft para converter documento ou extrair texto, "
                   "PdfCraft para extrair texto PDF. Informe source, output e "
                   "kind (image, document, document_text ou pdf_text).")
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
            "image": ("photocraft-cli", {".png", ".jpg", ".jpeg", ".psd", ".pcraft", ".webp", ".tif", ".tiff"},
                      {".png", ".jpg", ".jpeg", ".webp", ".pcraft", ".tif", ".tiff"}),
            "document": ("wordcraft-cli", {".docx", ".odt", ".md", ".txt", ".rtf"},
                         {".docx", ".pdf", ".md", ".txt", ".odt", ".rtf"}),
            "document_text": ("wordcraft-cli", {".docx", ".odt", ".rtf"}, {".txt"}),
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
                if kind in {"pdf_text", "document_text"}:
                    _bounded_stdout(args, outfile, directory)
                else:
                    with open(os.devnull, "wb") as stream:
                        result = subprocess.run(args, cwd=directory, stdin=subprocess.DEVNULL,
                                                stdout=stream, stderr=subprocess.DEVNULL,
                                                timeout=90, check=False)
                    if result.returncode != 0:
                        raise ValueError("O programa local não conseguiu converter o arquivo.")
                # Do not follow a CLI-created symlink pointing outside the
                # private work directory. Use pinned regular-file descriptors
                # just like the source-file reader, with an output size cap.
                staging_policy = PathSecurity()
                staging_policy.home = work
                staging_policy.protected_paths = []
                converted = _read_source(staging_policy, str(outfile), _MAX_OUTPUT)
                if kind in {"pdf_text", "document_text"}:
                    converted.decode("utf-8", errors="strict")
                _validate_converted_output(converted, output_ext)
                saved = _write_new(policy, output, converted)
            return ToolResult(True, self.name, data={"path": saved, "kind": kind})
        except (OSError, PermissionError, ValueError, UnicodeError,
                subprocess.TimeoutExpired) as exc:
            return ToolResult(False, self.name,
                              error=f"Conversão local não concluída: {type(exc).__name__}.")
