"""Explicit, bounded local image/screen/camera analysis.

No automatic capture, monitoring, filesystem enumeration, image retention,
network egress, agent actions or screenshot uploads to third-party services.
"""

import base64
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
import warnings
from pathlib import Path

from nexus.config.settings import Settings
from nexus.models.ollama_transport import OllamaTransport, OllamaTransportError
from nexus.security.paths import PathSecurity


class VisionError(RuntimeError):
    """Generic operational failure without image data or credentials."""


class VisionInputError(VisionError, ValueError):
    """Image or capture parameters violate the explicit security limits."""


class LocalVision:
    MAX_INPUT_BYTES = 6 * 1024 * 1024
    MAX_OUTPUT_BYTES = 6 * 1024 * 1024
    MAX_PIXELS = 8_000_000
    MAX_DIMENSION = 4096
    MAX_PROMPT = 2000
    MAX_RESPONSE = 12000
    CAPTURE_TIMEOUT = 20
    FORMATS = frozenset({"PNG", "JPEG", "WEBP"})
    DEFAULT_PROMPT = "Descreva esta imagem objetivamente em português brasileiro."
    MODEL_PATTERN = re.compile(r"^[a-zA-Z0-9][a-zA-Z0-9_./:-]{0,127}$")

    def __init__(self, settings: Settings, path_security: PathSecurity | None = None,
                 transport=None):
        self.settings = settings
        self.path_security = path_security if path_security is not None else PathSecurity()
        self.transport = transport if transport is not None else OllamaTransport(
            base_url=settings.local_model_base_url
        )

    @classmethod
    def validate_question(cls, question: str | None) -> str:
        if question is None:
            return cls.DEFAULT_PROMPT
        if not isinstance(question, str) or not question.strip() or (
            len(question) > cls.MAX_PROMPT or "\x00" in question
        ):
            raise VisionInputError("Pergunta inválida (máximo 2000 caracteres).")
        return question.strip()

    @classmethod
    def validate_model(cls, model: str) -> str:
        if not isinstance(model, str) or not cls.MODEL_PATTERN.fullmatch(model):
            raise VisionInputError("Identificador de modelo local inválido.")
        return model

    @classmethod
    def _normalize_image(cls, data: bytes) -> bytes:
        if not data or len(data) > cls.MAX_INPUT_BYTES:
            raise VisionInputError("Imagem vazia ou maior que 6 MiB.")
        try:
            from PIL import Image, ImageOps, UnidentifiedImageError
        except ImportError as exc:
            raise VisionError("Instale suporte de visão: pip install -e '.[vision]'.") from exc

        try:
            with warnings.catch_warnings():
                warnings.simplefilter("error", Image.DecompressionBombWarning)
                with Image.open(io.BytesIO(data)) as raw:
                    if raw.format not in cls.FORMATS:
                        raise VisionInputError("Formato não suportado (PNG/JPEG/WEBP).")
                    width, height = raw.size
                    if (width <= 0 or height <= 0 or width > cls.MAX_DIMENSION
                            or height > cls.MAX_DIMENSION
                            or width * height > cls.MAX_PIXELS):
                        raise VisionInputError("Imagem excede 4096 px ou 8 megapixels.")
                    raw.load()
                    # Re-encode to PNG and discard EXIF/location/metadata.
                    normalized = ImageOps.exif_transpose(raw).convert("RGB")
                    buffer = io.BytesIO()
                    normalized.save(buffer, format="PNG")
                    image = buffer.getvalue()
        except VisionInputError:
            raise
        except (OSError, ValueError, Image.DecompressionBombWarning,
                Image.DecompressionBombError) as exc:
            raise VisionInputError("Imagem inválida, corrompida ou excessiva.") from exc
        if len(image) > cls.MAX_OUTPUT_BYTES:
            raise VisionInputError("Imagem normalizada maior que 6 MiB.")
        return image

    def image_from_file(self, source: str | Path) -> bytes:
        if not isinstance(source, (str, Path)) or not os.fspath(source).strip():
            raise VisionInputError("Caminho de imagem inválido.")
        path = Path(source).expanduser()
        if path.suffix.lower() not in {".png", ".jpg", ".jpeg", ".webp"}:
            raise VisionInputError("Somente PNG, JPEG ou WEBP.")
        try:
            with self.path_security.open_regular_file(path) as (fd, _):
                if os.fstat(fd).st_size > self.MAX_INPUT_BYTES:
                    raise VisionInputError("Imagem maior que 6 MiB.")
                data = bytearray()
                while len(data) <= self.MAX_INPUT_BYTES:
                    chunk = os.read(fd, min(65536, self.MAX_INPUT_BYTES + 1 - len(data)))
                    if not chunk:
                        break
                    data.extend(chunk)
        except (OSError, PermissionError) as exc:
            raise VisionInputError("Imagem fora do HOME autorizado ou inacessível.") from exc
        return self._normalize_image(bytes(data))

    @classmethod
    def _capture(cls, command: list[str]) -> bytes:
        # No shell; stdout is an anonymous OS temporary file, not a saved screenshot.
        # Bounded subprocess runtime and file size prevent unbounded pipe allocation.
        try:
            with tempfile.TemporaryFile(mode="w+b") as output:
                result = subprocess.run(
                    command, stdin=subprocess.DEVNULL, stdout=output,
                    stderr=subprocess.DEVNULL, timeout=cls.CAPTURE_TIMEOUT,
                    check=False,
                )
                if result.returncode != 0:
                    raise VisionError("Não foi possível capturar imagem local.")
                if output.tell() > cls.MAX_INPUT_BYTES:
                    raise VisionInputError("Captura maior que 6 MiB.")
                output.seek(0)
                return cls._normalize_image(output.read(cls.MAX_INPUT_BYTES + 1))
        except (subprocess.TimeoutExpired, OSError) as exc:
            raise VisionError("Captura local falhou ou ultrapassou o tempo limite.") from exc

    def screen(self) -> bytes:
        if os.environ.get("WAYLAND_DISPLAY"):
            binary = shutil.which("grim")
            if not binary:
                raise VisionError("Wayland exige o utilitário grim instalado.")
            return self._capture([binary, "-"])
        if os.environ.get("DISPLAY"):
            binary = shutil.which("import")
            if not binary:
                raise VisionError("X11 exige ImageMagick (comando import).")
            return self._capture([binary, "-window", "root", "png:-"])
        raise VisionError("Não há sessão gráfica Wayland/X11 disponível.")

    def camera(self, index: int) -> bytes:
        if type(index) is not int or not 0 <= index <= 9:
            raise VisionInputError("Câmera deve ter índice de 0 a 9.")
        binary = shutil.which("ffmpeg")
        if not binary:
            raise VisionError("Captura de câmera exige FFmpeg.")
        return self._capture([
            binary, "-hide_banner", "-loglevel", "error", "-nostdin",
            "-f", "video4linux2", "-i", f"/dev/video{index}",
            "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "pipe:1",
        ])

    def describe(self, image: bytes, *, question: str | None = None,
                 model: str = "gemma3:4b") -> dict:
        prompt = self.validate_question(question)
        model_name = self.validate_model(model)
        normalized = self._normalize_image(image)
        payload = {
            "model": model_name,
            "messages": [{
                "role": "user", "content": prompt,
                "images": [base64.b64encode(normalized).decode("ascii")],
            }],
            "stream": False,
        }
        try:
            response = self.transport.chat(
                payload=payload, timeout=self.settings.local_model_timeout
            )
        except OllamaTransportError as exc:
            raise VisionError("Falha no modelo visual Ollama local.") from exc
        if not isinstance(response, dict) or response.get("done") is not True:
            raise VisionError("Resposta visual incompleta do Ollama.")
        message = response.get("message")
        if not isinstance(message, dict) or not isinstance(message.get("content"), str):
            raise VisionError("Resposta visual inválida do Ollama.")
        answer = message["content"].strip()
        if not answer:
            raise VisionError("O modelo visual não retornou descrição.")
        if len(answer) > self.MAX_RESPONSE:
            answer = answer[:self.MAX_RESPONSE]
        return {"model": model_name, "description": answer}


def vision_dependencies() -> dict:
    """Readiness report only; never opens a camera, display or Ollama socket."""
    from importlib.util import find_spec
    return {
        "mode": "local-on-demand",
        "screen_capture_tested": False,
        "camera_capture_tested": False,
        "ollama_vision_tested": False,
        "checks": {
            "pillow": find_spec("PIL") is not None,
            "wayland_grim": bool(shutil.which("grim")),
            "x11_import": bool(shutil.which("import")),
            "camera_ffmpeg": bool(shutil.which("ffmpeg")),
        },
        "notice": "O diagnóstico não captura imagens nem valida hardware real.",
    }
