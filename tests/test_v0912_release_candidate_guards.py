"""Release-candidate workflow guardrails; no physical test is forged by CI."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CANDIDATE = ROOT / ".github/workflows/release-candidate-v0.9.12.yml"
STABLE = ROOT / ".github/workflows/release-v0.9.12.yml"
README = ROOT / "README.md"
ROADMAP = ROOT / "docs/ROADMAP_v0.9.12_RELEASE_STATUS.md"
NOTES = ROOT / "docs/RELEASE_NOTES_v0.9.12-rc.3.md"


def test_release_candidate_is_immutable_and_bound_to_successful_push_main_ci():
    source = CANDIDATE.read_text(encoding="utf-8")
    for expected in (
        "workflow_run:", "types: [completed]", "branches: [main]",
        "workflow_run.conclusion == 'success'",
        "workflow_run.event == 'push'",
        "workflow_run.head_branch == 'main'",
        "workflow_run.head_repository.full_name == github.repository",
        "git rev-parse origin/main", "git rev-parse HEAD",
        'version" != "0.9.12"',
        "v0.9.12-rc.3", "--prerelease", "--verify-tag",
        "SHA256SUMS", "python -m build --wheel",
    ):
        assert expected in source
    assert "workflow_dispatch:" not in source


def test_stable_release_stays_explicitly_disabled():
    source = STABLE.read_text(encoding="utf-8")
    assert "if: $" + "{{ false }}" in source
    assert "v0.9.12" in source


def test_candidate_notes_and_roadmap_disclose_physical_acceptance_gap():
    notes = NOTES.read_text(encoding="utf-8")
    roadmap = ROADMAP.read_text(encoding="utf-8")
    readme = README.read_text(encoding="utf-8")
    assert "pré-lançamento" in notes
    assert "10 pendentes" in notes
    assert "11 PASSOU / 10 PENDENTE" in roadmap
    assert "BLOQUEADA" in roadmap
    assert "release-candidate-v0.9.12.yml" in readme
    assert "ROADMAP_v0.9.12_RELEASE_STATUS.md" in readme
