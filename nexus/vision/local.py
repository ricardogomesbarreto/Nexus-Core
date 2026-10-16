"""Explicit, bounded local image/screen/camera analysis.

No automatic capture, monitoring, filesystem enumeration, image retention,
network egress, agent actions or screenshot uploads to third-party services.
"""

import base64
import fcntl
import glob
import io
import json
import os
import re
import resource
import shutil
import stat
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
    # Common raster inputs are converted to metadata-free PNG for the model.
    # AVIF decoding depends on the Pillow build; unsupported codecs fail closed.
    FORMATS = frozenset({"PNG", "JPEG", "WEBP", "BMP", "GIF", "TIFF", "AVIF"})
    FILE_SUFFIXES = (".png", ".jpg", ".jpeg", ".jpe", ".jfif", ".webp",
                     ".bmp", ".gif", ".tif", ".tiff", ".avif")
    DEFAULT_PROMPT = ("Analise a imagem realmente enviada. Identifique os objetos, textos "
                      "ou elementos visíveis com precisão e responda em português brasileiro. "
                      "Se estiver ilegível ou incerto, informe a limitação; não invente.")
    VISION_MODEL_PREFIXES = ("gemma3:", "llava:", "llama3.2-vision:",
                             "qwen2.5vl:", "qwen3-vl:", "moondream:", "minicpm-v:")
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
                        raise VisionInputError("Formato não suportado (PNG/JPEG/WEBP/BMP/GIF/TIFF/AVIF).")
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
        if path.suffix.lower() not in self.FILE_SUFFIXES:
            raise VisionInputError("Somente PNG, JPEG, WEBP, BMP, GIF, TIFF ou AVIF.")
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
    def _limit_capture_output(cls) -> None:
        # Linux kernel hard-limit on the child's stdout regular file.
        # Enforced while the capture runs, not only after it finishes.
        resource.setrlimit(
            resource.RLIMIT_FSIZE,
            (cls.MAX_INPUT_BYTES + 1, cls.MAX_INPUT_BYTES + 1),
        )

    @classmethod
    def _capture(cls, command: list[str]) -> bytes:
        # No shell; stdout is an anonymous OS temporary file, not a saved screenshot.
        # Bounded subprocess runtime and file size prevent unbounded pipe allocation.
        try:
            with tempfile.TemporaryFile(mode="w+b") as output:
                result = subprocess.run(
                    command, stdin=subprocess.DEVNULL, stdout=output,
                    stderr=subprocess.DEVNULL, timeout=cls.CAPTURE_TIMEOUT,
                    check=False, preexec_fn=cls._limit_capture_output,
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
            return self.selected_screen(window=True)
        if os.environ.get("DISPLAY"):
            binary = shutil.which("import")
            if not binary:
                raise VisionError("X11 exige ImageMagick (comando import).")
            return self._capture([binary, "-window", "root", "png:-"])
        raise VisionError("Não há sessão gráfica Wayland/X11 disponível.")

    def selected_screen(self, *, window: bool = True) -> bytes:
        """Select a window (or monitor) in the compositor, then read one frame."""
        from nexus.vision.portal import PortalError, choose_screenshot
        try:
            selected = choose_screenshot(window=window)
            # Portal files may be outside HOME. Treat the URI as a one-shot
            # capability, with a bounded read and the normal image sanitizer.
            with selected.open("rb") as stream:
                data = stream.read(self.MAX_INPUT_BYTES + 1)
            return self._normalize_image(data)
        except PortalError as exc:
            raise VisionError(str(exc)) from exc
        except OSError as exc:
            raise VisionError("Imagem do portal não pôde ser lida.") from exc

    @staticmethod
    def _camera_supports_capture(path: Path) -> bool:
        """Check V4L2 capture capability, not merely /dev/video* existence.

        Some integrated webcams have two nodes: a video capture node and a
        metadata-only node. A QUERYCAP ioctl does not capture any frames.
        """
        try:
            flags = (os.O_RDONLY | os.O_NONBLOCK |
                     getattr(os, "O_CLOEXEC", 0) | getattr(os, "O_NOFOLLOW", 0))
            fd = os.open(path, flags)
            try:
                if not stat.S_ISCHR(os.fstat(fd).st_mode):
                    return False
                capability = bytearray(104)  # struct v4l2_capability
                fcntl.ioctl(fd, 0x80685600, capability, True)  # VIDIOC_QUERYCAP
                flags = int.from_bytes(capability[84:88], "little")
                device_caps = int.from_bytes(capability[88:92], "little")
                effective = device_caps if flags & 0x80000000 else flags
                return bool(effective & (0x00000001 | 0x00001000))
            finally:
                os.close(fd)
        except (OSError, ValueError):
            # An inaccessible/unsupported V4L2 device must not be offered.
            return False

    @staticmethod
    def cameras() -> list[tuple[int, str]]:
        """Discover actual V4L2 video capture devices without taking photos."""
        devices = []
        for path in glob.glob("/dev/video[0-9]*"):
            name = Path(path).name
            if not re.fullmatch(r"video[0-9]", name):
                continue
            index = int(name[5:])
            if not LocalVision._camera_supports_capture(Path(path)):
                continue
            try:
                label = Path(f"/sys/class/video4linux/{name}/name").read_text().strip()
            except OSError:
                label = "Câmera"
            devices.append((index, label[:100] or "Câmera"))
        return sorted(devices)

    @staticmethod
    def _camera_frame_is_dark(image: bytes) -> bool:
        """Detect near-black captures without storing or changing image data.

        Returning a black first frame is common while a UVC device adjusts
        exposure. A closed privacy shutter may produce the same result.
        """
        from PIL import Image, ImageStat
        with Image.open(io.BytesIO(image)) as frame:
            sample = frame.convert("L")
            sample.thumbnail((96, 96))
            mean = ImageStat.Stat(sample).mean[0]
            _low, high = sample.getextrema()
            return mean < 10 and high < 28

    def camera(self, index: int) -> bytes:
        if type(index) is not int or not 0 <= index <= 9:
            raise VisionInputError("Câmera deve ter índice de 0 a 9.")
        binary = shutil.which("ffmpeg")
        if not binary:
            raise VisionError("Captura de câmera exige FFmpeg.")
        try:
            # Let the webcam settle its automatic exposure; only the later
            # frame is retained. No continuous preview or disk recording.
            image = self._capture([
                binary, "-hide_banner", "-loglevel", "error", "-nostdin",
                "-f", "video4linux2", "-i", f"/dev/video{index}",
                "-vf", r"select=gte(n\,8)",
                "-frames:v", "1", "-f", "image2pipe", "-vcodec", "png", "pipe:1",
            ])
            if self._camera_frame_is_dark(image):
                raise VisionError(
                    f"A câmera {index} retornou uma imagem praticamente preta. "
                    "Verifique a tampa/tecla de privacidade, a iluminação "
                    "e se outro aplicativo está usando a webcam."
                )
            return image
        except VisionError as exc:
            if "praticamente preta" in str(exc):
                raise
            raise VisionError(
                f"A câmera {index} não conseguiu capturar uma foto. "
                "Verifique permissões, se ela está em uso e o formato V4L2."
            ) from exc

    def _installed_vision_model(self, requested: str) -> str:
        """Require a real local vision model; never infer vision from a text LLM."""
        query = getattr(self.transport, "list_models", None)
        if not callable(query):
            # Injected test transports keep their explicit model contract.
            return requested
        try:
            installed = query()
        except OllamaTransportError as exc:
            raise VisionError(
                "Ollama local indisponível. Inicie o Ollama e confira o modelo visual."
            ) from exc
        if not isinstance(installed, list):
            raise VisionError("Não foi possível consultar os modelos do Ollama.")
        names = [name for name in installed if isinstance(name, str)]
        explicit = os.environ.get("NEXUS_VISION_MODEL", "").strip()
        candidate = self.validate_model(explicit) if explicit else requested
        if candidate in names:
            if not candidate.startswith(self.VISION_MODEL_PREFIXES):
                raise VisionError(
                    f"O modelo '{candidate}' não possui capacidade visual confirmada. "
                    "Use um modelo visual local, como gemma3:4b."
                )
            return candidate
        if not explicit:
            for name in names:
                if name.startswith(self.VISION_MODEL_PREFIXES):
                    return self.validate_model(name)
        raise VisionError(
            f"Modelo visual '{candidate}' não está instalado no Ollama local. "
            "Instale com: ollama pull gemma3:4b. Depois reinicie a análise. "
            "A imagem não foi enviada a outro serviço."
        )

    def describe(self, image: bytes, *, question: str | None = None,
                 model: str = "gemma3:4b") -> dict:
        prompt = self.validate_question(question)
        model_name = self._installed_vision_model(self.validate_model(model))
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
            raise VisionError(
                f"O modelo visual '{model_name}' não conseguiu analisar a imagem. "
                "Confira se o Ollama está ativo e se o modelo aceita imagens. "
                "Execute: ollama list."
            ) from exc
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
            "wayland_portal_client": find_spec("dbus_next") is not None,
            "x11_import": bool(shutil.which("import")),
            "camera_ffmpeg": bool(shutil.which("ffmpeg")),
        },
        "notice": "O diagnóstico não captura imagens nem valida hardware real.",
    }
