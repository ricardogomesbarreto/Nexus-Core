"""Prévia raster isolada de um arquivo local de mosaicos (formato v3).

O descritor é aberto pela política de arquivos do Nexus e herdado por um
processo com limites. Nunca se inicia servidor ou se consulta uma URL.
"""

import base64
import binascii
import io
import json
import math
import os
import resource
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

from nexus.security.paths import PathSecurity


class LocalMapError(ValueError):
    """Falha sanitizada, sem caminho ou conteúdo do usuário."""


@dataclass(frozen=True)
class MapTile:
    image: bytes
    z: int
    x: int
    y: int
    min_zoom: int
    max_zoom: int
    attribution: str


def read_tile(path: str | Path, coordinates: tuple[int, int, int] | None = None,
              *, policy: PathSecurity | None = None) -> MapTile:
    """Lê um mosaico raster local mediante escolha explícita do usuário."""
    if Path(path).suffix.lower() != ".pmtiles":
        raise LocalMapError("Selecione um arquivo de mapa .pmtiles.")
    if coordinates is not None and (
        len(coordinates) != 3 or any(type(v) is not int for v in coordinates)
        or not 0 <= coordinates[0] <= 24
        or not 0 <= coordinates[1] < 1 << coordinates[0]
        or not 0 <= coordinates[2] < 1 << coordinates[0]
    ):
        raise LocalMapError("Coordenadas de visualização inválidas.")
    try:
        with (policy or PathSecurity()).open_regular_file(path) as (fd, _):
            size = os.fstat(fd).st_size
            if not 127 <= size <= 20 * 1024**3:
                raise LocalMapError("Arquivo local inválido ou acima do limite de 20 GiB.")
            args = [sys.executable, "-m", "nexus.maps.local", "--worker", str(fd)]
            if coordinates is not None:
                args.extend(str(v) for v in coordinates)
            result = subprocess.run(args, pass_fds=(fd,), capture_output=True,
                                    timeout=8, check=False)
        if result.returncode != 0 or len(result.stdout) > 6 * 1024**2:
            raise LocalMapError("Mapa indisponível ou formato não suportado.")
        payload = json.loads(result.stdout)
        if "error" in payload:
            raise LocalMapError(payload["error"])
        image = base64.b64decode(payload["image"], validate=True)
        if len(image) > 4 * 1024**2:
            raise LocalMapError("Imagem de mapa acima do limite.")
        return MapTile(image, payload["z"], payload["x"], payload["y"],
                       payload["min_zoom"], payload["max_zoom"],
                       payload["attribution"])
    except (OSError, subprocess.TimeoutExpired, json.JSONDecodeError, binascii.Error, KeyError,
            ValueError) as exc:
        if isinstance(exc, LocalMapError):
            raise
        raise LocalMapError("Não foi possível ler o mapa local; confira o arquivo e a instalação.") from exc


def _worker(fd: int, coordinates: tuple[int, int, int] | None):
    # A biblioteca de terceiros manipula diretórios comprimidos: isolar leitura.
    memory = 384 * 1024**2
    resource.setrlimit(resource.RLIMIT_AS, (memory, memory))
    resource.setrlimit(resource.RLIMIT_CPU, (4, 4))
    from pmtiles.reader import Reader
    from pmtiles.tile import Compression, TileType
    from PIL import Image

    size = os.fstat(fd).st_size

    def limited_read(offset, length):
        if (type(offset) is not int or type(length) is not int or offset < 0
                or not 0 < length <= 2 * 1024**2 or offset + length > size):
            raise LocalMapError("Índice do mapa inválido ou acima do limite.")
        return os.pread(fd, length, offset)

    reader = Reader(limited_read)
    header = reader.header()
    if header["tile_type"] not in (TileType.PNG, TileType.JPEG, TileType.WEBP):
        raise LocalMapError("Este mapa usa mosaicos vetoriais ou formato não suportado.")
    if header["tile_compression"] != Compression.NONE:
        raise LocalMapError("Compressão de mosaico ainda não suportada.")
    min_zoom, max_zoom = header["min_zoom"], header["max_zoom"]
    if not 0 <= min_zoom <= max_zoom <= 24:
        raise LocalMapError("Níveis de ampliação inválidos.")
    if coordinates is None:
        z = max(min_zoom, min(max_zoom, header["center_zoom"]))
        count = 1 << z
        lon = max(-180, min(180, header["center_lon_e7"] / 10**7))
        lat = max(-85.051128, min(85.051128, header["center_lat_e7"] / 10**7))
        x = max(0, min(count - 1, int((lon + 180) / 360 * count)))
        y = max(0, min(count - 1, int((1 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2 * count)))
    else:
        z, x, y = coordinates
        if not min_zoom <= z <= max_zoom:
            raise LocalMapError("Ampliação fora dos níveis do mapa.")
    tile = reader.get(z, x, y)
    if not tile or len(tile) > 2 * 1024**2:
        raise LocalMapError("Nenhum mosaico disponível nesta posição.")
    Image.MAX_IMAGE_PIXELS = 4_000_000
    with Image.open(io.BytesIO(tile)) as source:
        if source.format not in {"PNG", "JPEG", "WEBP"} or source.width * source.height > 4_000_000:
            raise LocalMapError("Imagem de mosaico inválida ou muito grande.")
        image = source.convert("RGB")
    image.thumbnail((760, 580))
    output = io.BytesIO()
    image.save(output, format="PNG")
    attribution = ""
    if header["metadata_length"] <= 64 * 1024:
        metadata = reader.metadata()
        value = metadata.get("attribution", "")
        if isinstance(value, str):
            attribution = value[:200].replace("<", " ").replace(">", " ")
    return {"image": base64.b64encode(output.getvalue()).decode("ascii"),
            "z": z, "x": x, "y": y, "min_zoom": min_zoom,
            "max_zoom": max_zoom, "attribution": attribution}


def _main():
    try:
        fd = int(sys.argv[2])
        coords = tuple(map(int, sys.argv[3:])) if len(sys.argv) > 3 else None
        payload = _worker(fd, coords)
    except ImportError:
        payload = {"error": "Leitor de mapas indisponível; instale o extra maps."}
    except (LocalMapError, OSError, ValueError, MemoryError, KeyError):
        payload = {"error": "Mapa indisponível ou formato não suportado."}
    print(json.dumps(payload, ensure_ascii=False))


if __name__ == "__main__" and len(sys.argv) >= 3 and sys.argv[1] == "--worker":
    _main()
