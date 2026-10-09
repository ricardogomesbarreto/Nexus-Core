"""Read-only CLI desktop probe must not initialize application or devices."""
import json

import pytest


def test_desktop_probe_exits_without_database_or_agent(monkeypatch, capsys):
    import nexus.main as entry
    import nexus.automation as desktop
    monkeypatch.setattr(entry, "build_application",
                        lambda: pytest.fail("Desktop check started database"))
    monkeypatch.setattr(desktop, "desktop_capabilities",
                        lambda: {"session_x11": False, "xdotool": False})
    entry.cli(["--desktop-check"])
    assert json.loads(capsys.readouterr().out) == {
        "session_x11": False, "xdotool": False,
    }


@pytest.mark.parametrize("arguments", [
    ["--desktop-check", "--desktop"],
    ["--desktop-check", "--agent-prompt", "run"],
    ["--desktop-check", "--vision-screen"],
    ["--desktop-check", "--memory-list"],
    ["--desktop-check", "--knowledge-list"],
    ["--desktop-check", "--vision-question", "abc"],
    ["--desktop-check", "--vision-model", "different:model"],
])
def test_desktop_check_rejects_conflicting_sources(arguments):
    import nexus.main as entry
    with pytest.raises(SystemExit) as exc:
        entry.cli(arguments)
    assert exc.value.code == 2
