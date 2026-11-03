"""Inventário opt-in de materiais offline sob HOME, sem servidores nem download.

Inclui apenas metadados de arquivos regulares no diretório indicado; não lê
o conteúdo, não varre subdiretórios, não extrai ZIM nem inicia Kolibri/Kiwix.
"""
from __future__ import annotations

import os
import stat
from dataclasses import dataclass
from pathlib import Path

from nexus.security.paths import PathSecurity


class OfflineCatalogError(ValueError):
    """Falha com mensagem sem caminhos ou conteúdo de arquivos."""


@dataclass(frozen=True)
class OfflineMaterial:
    filename: str
    category: str
    bytes: int


KINDS = {
    ".zim": "Enciclopédia ZIM (requer leitor Kiwix)",
    ".pdf": "Documento de estudo",
    ".epub": "Livro eletrônico",
    ".txt": "Texto",
    ".md": "Notas Markdown",
    ".html": "Material HTML",
    ".mp4": "Vídeo de curso",
    ".webm": "Vídeo de curso",
}
MAX_ENTRIES = 300
MAX_RESULTS = 60


def list_offline_materials(directory: str | Path,
                           paths: PathSecurity | None = None) -> list[OfflineMaterial]:
    """Retorna no máximo 60 itens de um único diretório escolhido pelo usuário."""
    if not isinstance(directory, (str, Path)) or not os.fspath(directory):
        raise OfflineCatalogError("Selecione um diretório local válido.")
    guard = paths if paths is not None else PathSecurity()
    materials = []
    try:
        with guard.open_directory(directory) as (fd, _):
            with os.scandir(fd) as entries:
                for inspected, entry in enumerate(entries, 1):
                    if inspected > MAX_ENTRIES:
                        raise OfflineCatalogError(
                            "Diretório muito grande: escolha uma pasta com até 300 entradas."
                        )
                    ext = Path(entry.name).suffix.lower()
                    if ext not in KINDS or not entry.is_file(follow_symlinks=False):
                        continue
                    metadata = entry.stat(follow_symlinks=False)
                    if not stat.S_ISREG(metadata.st_mode):
                        continue
                    materials.append(OfflineMaterial(entry.name, KINDS[ext], metadata.st_size))
    except OfflineCatalogError:
        raise
    except (OSError, PermissionError) as exc:
        raise OfflineCatalogError("Diretório indisponível ou não autorizado.") from exc
    materials.sort(key=lambda item: (item.category, item.filename.casefold()))
    return materials[:MAX_RESULTS]
