"""Round trip real do pacote opcional com arquivo sintético de uma única posição."""

from io import BytesIO
from pathlib import Path

import pytest

from nexus.maps.local import LocalMapError, read_tile

pmtiles = pytest.importorskip("pmtiles")
PIL = pytest.importorskip("PIL.Image")


def archive(path, kind, image=b"not-an-image"):
    from pmtiles.tile import Compression, TileType, zxy_to_tileid
    from pmtiles.writer import Writer

    with path.open("wb") as stream:
        writer = Writer(stream)
        writer.write_tile(zxy_to_tileid(0, 0, 0), image)
        writer.finalize({"tile_type": kind, "tile_compression": Compression.NONE,
                         "min_zoom": 0, "max_zoom": 0, "center_zoom": 0},
                        {"attribution": "Autor da amostra"})


def test_raster_preview_is_opt_in_local_and_bounded(tmp_path, monkeypatch):
    from pmtiles.tile import TileType
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    image = PIL.new("RGB", (32, 32), "#722f37")
    output = BytesIO()
    image.save(output, format="PNG")
    path = tmp_path / "amostra.pmtiles"
    archive(path, TileType.PNG, output.getvalue())
    tile = read_tile(path)
    assert (tile.z, tile.x, tile.y, tile.min_zoom, tile.max_zoom) == (0, 0, 0, 0, 0)
    assert tile.attribution == "Autor da amostra"
    assert PIL.open(BytesIO(tile.image)).getpixel((2, 2)) == (114, 47, 55)


def test_vector_and_corrupt_files_report_a_local_error(tmp_path, monkeypatch):
    from pmtiles.tile import TileType
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    path = tmp_path / "vetorial.pmtiles"
    archive(path, TileType.MVT)
    with pytest.raises(LocalMapError, match="formato não suportado"):
        read_tile(path)
    path.write_bytes(b"x" * 200)
    with pytest.raises(LocalMapError, match="formato não suportado"):
        read_tile(path)


def test_path_and_coordinates_rejected_before_worker(tmp_path, monkeypatch):
    from pmtiles.tile import TileType
    monkeypatch.setattr(Path, "home", lambda: tmp_path)
    target = tmp_path / "mapa.pmtiles"
    archive(target, TileType.PNG)
    link = tmp_path / "atalho.pmtiles"
    link.symlink_to(target)
    with pytest.raises(LocalMapError, match="Não foi possível ler"):
        read_tile(link)
    with pytest.raises(LocalMapError, match="Coordenadas"):
        read_tile(target, (2, -1, 0))
