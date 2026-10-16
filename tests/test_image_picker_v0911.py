"""File picker: visible format groups and a safe starting directory."""

from nexus.desktop.image_picker import IMAGE_GROUPS, image_filetypes, image_start_directory
from nexus.vision.local import LocalVision


def test_dialog_formats_match_decoder_extension_policy():
    extensions = {ext for title, names in IMAGE_GROUPS for ext in names}
    assert extensions == set(LocalVision.FILE_SUFFIXES)
    entries = image_filetypes()
    assert entries[0][0] == "Todas as imagens suportadas"
    assert entries[-1] == ("Todos os arquivos (validar conteúdo)", "*")
    assert len(entries) == len(IMAGE_GROUPS) + 2
    for ext in extensions:
        assert "*" + ext in entries[0][1].split()
        assert "*" + ext.upper() in entries[0][1].split()


def test_picker_prefers_photo_folders_without_directory_enumeration(tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    downloads = home / "Downloads"
    downloads.mkdir()
    assert image_start_directory(home) == downloads
    pictures = home / "Pictures"
    pictures.mkdir()
    assert image_start_directory(home) == pictures
    images = home / "Imagens"
    images.mkdir()
    assert image_start_directory(home) == images


def test_picker_ignores_symlinked_photo_directories(tmp_path):
    home = tmp_path / "home"
    outside = tmp_path / "outside"
    home.mkdir()
    outside.mkdir()
    (home / "Imagens").symlink_to(outside, target_is_directory=True)
    assert image_start_directory(home) == home
