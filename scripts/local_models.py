"""Install locally required model assets during the opt-in Ubuntu setup."""

import os
import json
from pathlib import Path
import platform
import shutil
import subprocess
import tarfile
import tempfile
from urllib.parse import urlsplit
from urllib.request import urlopen
import zipfile


VOSK_NAME = "vosk-model-small-pt-0.3"
VOSK_URL = f"https://alphacephei.com/vosk/models/{VOSK_NAME}.zip"
MAX_ZIP_BYTES = 80 * 1024 * 1024
MAX_UNPACKED_BYTES = 250 * 1024 * 1024
OLLAMA_ARCHIVE = {
    "x86_64": "ollama-linux-amd64.tar.zst",
    "aarch64": "ollama-linux-arm64.tar.zst",
}
MAX_OLLAMA_ARCHIVE_BYTES = 3 * 1024 * 1024 * 1024
MAX_OLLAMA_UNPACKED_BYTES = 8 * 1024 * 1024 * 1024
PIPER_VOICE = "pt_BR-faber-medium"
PIPER_VOICE_URL = (
    "https://huggingface.co/rhasspy/piper-voices/resolve/v1.0.0/"
    "pt/pt_BR/faber/medium/" + PIPER_VOICE + ".onnx"
)
MAX_PIPER_BYTES = 100 * 1024 * 1024


def install_piper_voice(destination: Path, *, opener=urlopen) -> None:
    """Fetch the fixed free pt-BR voice and config, then commit both together."""
    destination = Path(destination)
    config_path = destination.with_suffix(".onnx.json")
    if destination.is_file() and config_path.is_file():
        return
    if destination.exists() or config_path.exists() or destination.is_symlink():
        raise ValueError("Voz neural parcial: remova somente os arquivos incompletos.")
    parent = destination.parent
    parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if parent.is_symlink() or parent.stat().st_uid != os.getuid():
        raise ValueError("Pasta da voz neural insegura.")
    parent.chmod(0o700)
    stage = Path(tempfile.mkdtemp(prefix=".piper-", dir=parent))
    try:
        for suffix, maximum in (("", MAX_PIPER_BYTES), (".json", 65536)):
            with opener(PIPER_VOICE_URL + suffix, timeout=60) as response:
                if urlsplit(response.geturl()).scheme != "https":
                    raise ValueError("Redirecionamento inseguro da voz neural.")
                with (stage / (PIPER_VOICE + ".onnx" + suffix)).open("wb") as output:
                    size = 0
                    for block in iter(lambda: response.read(1024 * 1024), b""):
                        size += len(block)
                        if size > maximum:
                            raise ValueError("Modelo de voz maior que o limite.")
                        output.write(block)
        model_file = stage / destination.name
        configuration = stage / config_path.name
        if model_file.stat().st_size < 1024 * 1024:
            raise ValueError("Modelo neural incompleto.")
        payload = json.loads(configuration.read_text(encoding="utf-8"))
        if (type(payload) is not dict or type(payload.get("language")) is not dict
                or payload["language"].get("code") != "pt_BR"):
            raise ValueError("Configuração da voz neural inválida.")
        model_file.replace(destination)
        configuration.replace(config_path)
    finally:
        shutil.rmtree(stage, ignore_errors=True)


def install_portuguese_voice_model(destination: Path, *, opener=urlopen) -> None:
    """Download the fixed official archive into a private directory atomically."""
    destination = Path(destination)
    if destination.is_dir():
        return
    if destination.exists() or destination.is_symlink():
        raise ValueError("Caminho do modelo Vosk já existe e não é um diretório.")
    parent = destination.parent
    if parent.is_symlink():
        raise ValueError("Pasta do modelo Vosk não pode ser um link simbólico.")
    parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if parent.is_symlink() or parent.stat().st_uid != os.getuid():
        raise ValueError("Pasta do modelo Vosk não pertence ao usuário.")
    parent.chmod(0o700)
    archive_path = None
    staging = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".vosk-", suffix=".zip",
                                         delete=False) as archive:
            archive_path = Path(archive.name)
            with opener(VOSK_URL, timeout=60) as response:
                final_url = urlsplit(response.geturl())
                if (final_url.scheme != "https"
                        or final_url.hostname != "alphacephei.com"):
                    raise ValueError("Origem do modelo Vosk inesperada.")
                total = 0
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    total += len(block)
                    if total > MAX_ZIP_BYTES:
                        raise ValueError("Arquivo Vosk maior que o limite.")
                    archive.write(block)
        staging = Path(tempfile.mkdtemp(prefix=".vosk-extract-", dir=parent))
        with zipfile.ZipFile(archive_path) as zipped:
            members = zipped.infolist()
            if len(members) > 512 or not members:
                raise ValueError("Arquivo Vosk inválido.")
            size = 0
            for item in members:
                parts = Path(item.filename).parts
                if (not parts or parts[0] != VOSK_NAME
                        or any(part in ("", ".", "..") for part in parts)
                        or item.filename.startswith("/")
                        or (item.external_attr >> 16) & 0o170000 == 0o120000):
                    raise ValueError("Caminho inseguro no arquivo Vosk.")
                size += item.file_size
                if size > MAX_UNPACKED_BYTES:
                    raise ValueError("Modelo Vosk maior que o limite.")
                target = staging.joinpath(*parts)
                if item.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                else:
                    target.parent.mkdir(parents=True, exist_ok=True)
                    with zipped.open(item) as source, target.open("wb") as output:
                        shutil.copyfileobj(source, output)
        extracted = staging / VOSK_NAME
        if not (extracted / "am" / "final.mdl").is_file():
            raise ValueError("Modelo Vosk incompleto.")
        if destination.exists():
            raise ValueError("Modelo Vosk apareceu durante a instalação.")
        extracted.rename(destination)
    finally:
        if archive_path is not None:
            archive_path.unlink(missing_ok=True)
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)


def install_ollama_runtime(destination: Path, *, opener=urlopen) -> Path:
    """Install the vendor's Linux archive under the user's private data path."""
    name = OLLAMA_ARCHIVE.get(platform.machine())
    if name is None:
        raise ValueError("Arquitetura sem pacote Ollama configurado.")
    destination = Path(destination)
    if destination.exists() or destination.is_symlink():
        raise ValueError("Pasta de instalação Ollama já existe.")
    parent = destination.parent
    parent.mkdir(parents=True, mode=0o700, exist_ok=True)
    if parent.is_symlink() or parent.stat().st_uid != os.getuid():
        raise ValueError("Pasta de instalação Ollama insegura.")
    parent.chmod(0o700)
    archive_path = None
    tar_path = None
    staging = None
    try:
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".ollama-", suffix=".zst",
                                         delete=False) as archive:
            archive_path = Path(archive.name)
            url = "https://ollama.com/download/" + name
            with opener(url, timeout=60) as response:
                if urlsplit(response.geturl()).scheme != "https":
                    raise ValueError("Redirecionamento inseguro do Ollama.")
                total = 0
                for block in iter(lambda: response.read(1024 * 1024), b""):
                    total += len(block)
                    if total > MAX_OLLAMA_ARCHIVE_BYTES:
                        raise ValueError("Pacote Ollama maior que o limite.")
                    archive.write(block)
        with tempfile.NamedTemporaryFile(dir=parent, prefix=".ollama-", suffix=".tar",
                                         delete=False) as expanded:
            tar_path = Path(expanded.name)
            subprocess.run(["zstd", "-q", "-d", "-c", str(archive_path)],
                           stdout=expanded, stderr=subprocess.DEVNULL,
                           check=True, timeout=600)
        if tar_path.stat().st_size > MAX_OLLAMA_UNPACKED_BYTES:
            raise ValueError("Pacote Ollama expandido maior que o limite.")
        staging = Path(tempfile.mkdtemp(prefix=".ollama-unpack-", dir=parent))
        with tarfile.open(tar_path, "r:") as tar:
            members = tar.getmembers()
            if (not members or len(members) > 5000
                    or sum(member.size for member in members) > MAX_OLLAMA_UNPACKED_BYTES
                    or any(not (member.isfile() or member.isdir() or member.issym())
                           for member in members)):
                raise ValueError("Pacote Ollama inválido.")
            tar.extractall(staging, filter="data")
        binary = staging / "bin" / "ollama"
        if binary.is_symlink() or not binary.is_file():
            raise ValueError("Executável Ollama ausente do pacote oficial.")
        binary.chmod(0o700)
        if destination.exists():
            raise ValueError("Pasta Ollama apareceu durante a instalação.")
        staging.rename(destination)
        staging = None
        return destination / "bin" / "ollama"
    finally:
        if archive_path is not None:
            archive_path.unlink(missing_ok=True)
        if tar_path is not None:
            tar_path.unlink(missing_ok=True)
        if staging is not None:
            shutil.rmtree(staging, ignore_errors=True)
