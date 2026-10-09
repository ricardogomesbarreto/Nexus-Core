from threading import Thread

import pytest

from nexus.desktop.confirmation import DesktopConfirmation
from nexus.security import RiskLevel, SecurityRequest


def request():
    return SecurityRequest(
        action="terminal_sandbox", description="Execução isolada",
        risk_level=RiskLevel.MEDIUM, tool_name="terminal_sandbox",
    )


@pytest.mark.parametrize("approved", [True, False])
def test_worker_waits_for_explicit_desktop_decision(approved):
    confirmation = DesktopConfirmation()
    results = []
    worker = Thread(target=lambda: results.append(confirmation.confirm(request())))
    worker.start()
    seen = []
    for _ in range(100):
        confirmation.process(lambda value: seen.append(value) or approved)
        if seen:
            break
        worker.join(0.01)
    worker.join(1)
    assert not worker.is_alive()
    assert len(seen) == 1
    assert results == [approved]


def test_closing_confirmation_denies_new_requests():
    confirmation = DesktopConfirmation()
    confirmation.close()
    assert confirmation.confirm(request()) is False


def test_dialog_error_denies_request():
    confirmation = DesktopConfirmation()
    results = []
    worker = Thread(target=lambda: results.append(confirmation.confirm(request())))
    worker.start()

    def fail(_):
        raise RuntimeError("dialog failed")

    for _ in range(100):
        confirmation.process(fail)
        if results:
            break
        worker.join(0.01)
    worker.join(1)
    assert results == [False]
