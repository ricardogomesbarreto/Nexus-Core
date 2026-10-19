"""Opt-in real CLI metadata/render acceptance is not equivalent to mocked success."""
import io
import json
from pathlib import Path

import pytest

from scripts import validate_craft_cli as cli


@pytest.mark.parametrize("name", ["PhotoCraft", "WordCraft", "PdfCraft"])
def test_advanced_probe_executes_only_documented_commands_on_synthetic_files(
    monkeypatch, tmp_path, name
):
    commands = []
    def execute(argv, **kwargs):
        commands.append(argv)
        assert argv[0] == "/trusted/cli"
        if argv[1] == "info":
            assert Path(argv[2]).parent == tmp_path
            data = {
                "PhotoCraft": {"width": 1, "height": 1},
                "WordCraft": {"pages": 1, "words": 3},
                "PdfCraft": {"pages": 1, "encrypted": False},
            }[name]
            kwargs["stdout"].write(json.dumps(data).encode())
            return True
        if argv[1] == "text":
            assert name == "WordCraft"
            kwargs["stdout"].write(b"NEXUS CORE CLI\n")
            return True
        if argv[1] == "extract":
            assert name == "PdfCraft" and argv[3:5] == ["--pages", "1"]
            cli._write_pdf(Path(argv[6]))
            return True
        if argv[1] == "combine":
            assert name == "PdfCraft" and Path(argv[2]).is_file() and Path(argv[3]).is_file()
            assert argv[4] == "--out"
            cli._write_pdf(Path(argv[5]))
            return True
        if argv[1] == "edit":
            assert name == "PdfCraft" and argv[3] == "--out"
            assert argv[5:] == ["--rotate", "1:90"]
            cli._write_pdf(Path(argv[4]))
            return True
        assert name == "PdfCraft" and argv[1] == "render"
        assert argv[3:7] == ["--page", "1", "--dpi", "96"]
        cli._write_png(Path(argv[8]))
        return True
    monkeypatch.setattr(cli, "_execute", execute)
    assert cli.smoke_advanced_cli(name, "/trusted/cli", tmp_path)
    assert [call[1] for call in commands] == (
        ["info", "render", "extract", "combine", "edit"] if name == "PdfCraft" else
        ["info", "text"] if name == "WordCraft" else ["info"]
    )


def test_advanced_probe_refuses_false_positive_invalid_json(monkeypatch, tmp_path):
    def fake(argv, **kw):
        kw["stdout"].write(b'{"title":"confidential only"}')
        return True
    monkeypatch.setattr(cli, "_execute", fake)
    assert not cli.smoke_advanced_cli("WordCraft", "/trusted/cli", tmp_path)


def test_run_advanced_is_opt_in_and_reports_real_checks(monkeypatch, capsys):
    monkeypatch.setattr(cli.shutil, "which", lambda name: "/trusted/" + name)
    monkeypatch.setattr(cli, "_execute", lambda argv, **kw: True)
    calls = []
    monkeypatch.setattr(cli, "smoke_cli", lambda *a: calls.append(("basic", a[0])) or True)
    monkeypatch.setattr(cli, "smoke_advanced_cli", lambda *a: calls.append(("advanced", a[0])) or True)
    assert cli.run(smoke=True) == 0
    assert [x for x in calls if x[0] == "advanced"] == []
    assert cli.run(smoke=True, advanced=True) == 0
    assert len([x for x in calls if x[0] == "advanced"]) == 3
    assert capsys.readouterr().out.count("teste=metadados_e_previa") == 3
