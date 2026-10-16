"""Usable native image dialog options without browsing files in the background.

Only Tk's explicitly requested picker navigates directories. Files are still
validated by LocalVision and PathSecurity after an individual user selection.
"""

from pathlib import Path

# Keep these extensions synchronized with LocalVision.FILE_SUFFIXES.
IMAGE_GROUPS = (
    ("PNG", (".png",)),
    ("JPEG / JPG", (".jpg", ".jpeg", ".jpe", ".jfif")),
    ("WEBP", (".webp",)),
    ("BMP", (".bmp",)),
    ("GIF", (".gif",)),
    ("TIFF", (".tif", ".tiff")),
    ("AVIF (se suportado)", (".avif",)),
)


def image_filetypes():
    """Tk's chooser needs readable format names, not one truncated pattern."""
    groups = []
    all_patterns = []
    for title, extensions in IMAGE_GROUPS:
        patterns = []
        for ext in extensions:
            patterns.extend(("*" + ext, "*" + ext.upper()))
        groups.append((title, " ".join(patterns)))
        all_patterns.extend(patterns)
    return [
        ("Todas as imagens suportadas", " ".join(all_patterns)),
        *groups,
        ("Todos os arquivos (validar conteúdo)", "*"),
    ]


def image_start_directory(home: Path | None = None) -> Path:
    """Choose a friendly folder; don't enumerate personal files or follow links."""
    base = home if home is not None else Path.home()
    for name in ("Imagens", "Pictures", "Downloads"):
        candidate = base / name
        if not candidate.is_symlink() and candidate.is_dir():
            return candidate
    return base
