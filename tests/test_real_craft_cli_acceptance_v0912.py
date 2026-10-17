"""Regression tests for the opt-in, real-command Craft acceptance harness."""
from pathlib import Path
import zipfile

import pytest

from scripts import validate_craft_cli as cli


def test_synthetic_fixtures_are_real_containers(tmp_path):
    png, docx, pdf = (tmp_path / name for name in ("photo.png", "word.docx", "paper.pdf"))
    cli._write_png(png)
    cli._write_docx(docx)
    cli._write_pdf(pdf)

    assert png.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    with zipfile.ZipFile(docx) as z:
        assert b"NEXUS CORE CLI" in z.read("word/document.xml")
    pdf_bytes = pdf.read_bytes()
    assert pdf_bytes.startswith(b"%PDF-1.4")
    xref = int(pdf_bytes.split(b"startxref\n")[1].split(b"\n")[0])
    assert pdf_bytes[xref:xref + 4] == b"xref"


@pytest.mark.parametrize("name,subcommand", [
    ("PhotoCraft", "convert"), ("WordCraft", "convert"),
    ("PdfCraft", "text"),
])
def test_smoke_uses_real_documented_cli_argv_and_private_temp_files(
    tmp_path, monkeypatch, name, subcommand
):
    calls = []

    def fake_execute(argv, **kwargs):
        calls.append((argv, kwargs))
        assert argv[0] == "/usr/local/bin/test-cli"
        assert argv[1] == subcommand
        source = Path(argv[2])
        assert source.is_file() and source.parent == tmp_path
        if name == "PhotoCraft":
            assert Path(argv[3]).suffix == ".webp"
            Path(argv[3]).write_bytes(b"RIFF\x04\x00\x00\x00WEBP")
        elif name == "WordCraft":
            assert Path(argv[3]).suffix == ".pdf"
            Path(argv[3]).write_bytes(b"%PDF-1.7\nconverted")
        else:
            assert len(argv) == 3
            kwargs["stdout"].write(b"NEXUS CORE CLI\n")
        return True

    monkeypatch.setattr(cli, "_execute", fake_execute)
    assert cli.smoke_cli(name, "/usr/local/bin/test-cli", tmp_path)
    assert len(calls) == 1


def test_failing_or_wrong_output_cannot_be_reported_as_real_success(
    tmp_path, monkeypatch
):
    monkeypatch.setattr(cli, "_execute", lambda argv, **kwargs: False)
    assert not cli.smoke_cli("PhotoCraft", "/usr/bin/photocraft-cli", tmp_path)

    def wrong_output(argv, **kwargs):
        Path(argv[3]).write_bytes(b"not a document")
        return True

    monkeypatch.setattr(cli, "_execute", wrong_output)
    assert not cli.smoke_cli("WordCraft", "/usr/bin/wordcraft-cli", tmp_path)


def test_diagnostic_is_read_only_by_default_and_requires_real_binaries(
    tmp_path, monkeypatch, capsys
):
    calls = []
    monkeypatch.setattr(cli.shutil, "which", lambda name: None)
    monkeypatch.setattr(cli, "_execute", lambda *a, **kw: calls.append(a) or True)
    assert cli.run(smoke=False, rea=True) == 1
    assert calls == []
    assert capsys.readouterr().out.count("estado=ausente") == 4


def test_no_smoke_runs_only_help_and_never_loads_rea_engine(monkeypatch, capsys):
    calls = []
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/opt/verified/" + name)
    def spy(argv, **kwargs):
        calls.append(argv)
        return True
    monkeypatch.setattr(cli, "_execute", spy)
    assert cli.run(smoke=False, rea=True) == 0
    assert calls == [
        ["/opt/verified/photocraft-cli", "--help"],
        ["/opt/verified/wordcraft-cli", "--help"],
        ["/opt/verified/pdfcraft-cli", "--help"],
        ["/opt/verified/rea", "--help"],
    ]
    assert capsys.readouterr().out.count("cli_detectado") == 4
