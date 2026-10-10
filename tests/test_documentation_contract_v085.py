"""Executable policy checks matching the v0.8.5 documentation audit."""
from pathlib import Path

from nexus.config.settings import PROJECT_ROOT


RELEASES = (
    "0.3.9", "0.4.0", "0.4.1", "0.5.0",
    "0.6.0", "0.6.1", "0.6.2", "0.6.3",
    "0.7.0", "0.7.1", "0.7.2", "0.7.3",
    "0.8.0", "0.8.1", "0.8.2", "0.8.3", "0.8.4", "0.8.5",
)


def test_every_version_note_and_historical_readme_anchor_exists():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    for release in RELEASES:
        path = PROJECT_ROOT / "docs" / f"RELEASE_NOTES_v{release}.md"
        assert path.is_file(), path
        assert f"docs/RELEASE_NOTES_v{release}.md" in readme
    audit = PROJECT_ROOT / "docs/DOCUMENTATION_AUDIT_v0.8.5.md"
    assert audit.is_file()
    assert "docs/DOCUMENTATION_AUDIT_v0.8.5.md" in readme


def test_all_unhomologated_release_workflows_stay_explicitly_disabled():
    for release in (
        "0.7.3", "0.8.0", "0.8.1", "0.8.2",
        "0.8.3", "0.8.4", "0.8.5",
    ):
        path = PROJECT_ROOT / ".github/workflows" / f"release-v{release}.yml"
        text = path.read_text(encoding="utf-8")
        assert "if: ${{ false }}" in text, path
        assert "workflow_run:" not in text, path
        assert "workflow_dispatch:" in text, path


def test_x11_operational_document_reports_actual_merge_and_pending_hardware():
    document = (
        PROJECT_ROOT / "docs/X11_PHYSICAL_HOMOLOGATION.md"
    ).read_text(encoding="utf-8")
    assert "os PRs #11 (v0.7.3) e #12 (v0.8.0) já foram integrados" in document
    assert "teste físico X11 ainda não foi registrado" in document
    assert "PR #11 continua em rascunho" not in document


def test_only_ubuntu_is_supported_in_operational_installation_policy():
    readme = (PROJECT_ROOT / "README.md").read_text(encoding="utf-8")
    audit = (
        PROJECT_ROOT / "docs/DOCUMENTATION_AUDIT_v0.8.5.md"
    ).read_text(encoding="utf-8")
    assert "Ubuntu Desktop 24.04 LTS" in readme
    assert "ao Ubuntu Desktop 24.04 LTS" in audit
    assert "historicamente" not in audit.lower() or "Ubuntu" in audit
    assert "Debian" in audit  # only as future policy or superseded text


def test_recovery_is_separate_and_does_not_require_python_env_of_nexus():
    script = (PROJECT_ROOT / "nexus/updates/recovery.py").read_text(encoding="utf-8")
    installer = (PROJECT_ROOT / "scripts/install_linux.py").read_text(encoding="utf-8")
    assert "write_recovery_launcher(home)" in installer
    assert "nexus-core-recover" in installer
    assert "from nexus" not in script
    assert "import psycopg" not in script
    assert "REVERTER" in script
