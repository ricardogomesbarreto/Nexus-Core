"""Cancellation of pending consent must be a hard authorization denial."""
import time
from threading import Event, Thread

from nexus.desktop.confirmation import DesktopConfirmation
from nexus.security import RiskLevel, SecurityRequest


def request():
    return SecurityRequest(
        action="terminal_sandbox", description="Comando local protegido",
        risk_level=RiskLevel.MEDIUM, tool_name="terminal_sandbox",
    )


def test_cancel_pending_releases_waiting_worker_and_prevents_late_approval():
    bridge = DesktopConfirmation()
    result = []
    worker = Thread(target=lambda: result.append(bridge.confirm(request())))
    worker.start()
    # Either cancel before or after the queue becomes visible: pending state
    # must be rejected without approval or a 300 second wait.
    deadline = time.monotonic() + 2
    while time.monotonic() < deadline:
        with bridge._lock:
            if bridge._pending:
                break
        time.sleep(0.001)
    with bridge._lock:
        assert bridge._pending
    bridge.cancel_pending()
    worker.join(timeout=2)
    assert not worker.is_alive()
    assert result == [False]
    callback_count = []
    bridge.process(lambda req: callback_count.append(req) or True)
    assert callback_count == []


def test_cancellation_during_modal_consent_cannot_be_reversed():
    bridge = DesktopConfirmation()
    result = []
    approval_started = Event()
    allow_return = Event()
    worker = Thread(target=lambda: result.append(bridge.confirm(request())))
    worker.start()

    def pretend_modal(_):
        approval_started.set()
        allow_return.wait(2)
        return True

    dialog = Thread(target=lambda: bridge.process(pretend_modal))
    dialog.start()
    assert approval_started.wait(2)
    bridge.cancel_pending()
    allow_return.set()
    dialog.join(timeout=2)
    worker.join(timeout=2)
    assert not dialog.is_alive()
    assert not worker.is_alive()
    assert result == [False]


def test_bridge_can_accept_new_confirmations_after_cancel():
    bridge = DesktopConfirmation()
    bridge.cancel_pending()
    result = []
    worker = Thread(target=lambda: result.append(bridge.confirm(request())))
    worker.start()
    for _ in range(100):
        bridge.process(lambda _: True)
        if result:
            break
        worker.join(timeout=0.01)
    worker.join(timeout=2)
    assert result == [True]
