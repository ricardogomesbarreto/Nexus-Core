import pytest

from nexus.main import cli


def test_entrypoint_reports_version_without_database(capsys):
    with pytest.raises(SystemExit) as exc:
        cli(["--version"])

    assert exc.value.code == 0
    assert capsys.readouterr().out.strip() == "Nexus Core 0.7.0"
