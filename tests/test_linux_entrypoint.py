import pytest

from nexus.main import cli


def test_entrypoint_reports_version_without_database(capsys):
    with pytest.raises(SystemExit) as exc:
        cli(["--version"])

    assert exc.value.code == 0
    from nexus.config.settings import settings
    assert capsys.readouterr().out.strip() == f"Nexus Core {settings.version}"
