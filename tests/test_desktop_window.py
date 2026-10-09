import os
import time

import pytest

from nexus.agent import AgentOutcome
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow
from nexus.security import RiskLevel, SecurityRequest


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer display Linux")
def test_desktop_conversation_and_confirmation_on_graphical_display():
    import tkinter as tk

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    calls = []

    class FakeAgent:
        def run(self, prompt, is_cancelled=None):
            request = SecurityRequest(
                action="terminal_sandbox", description="Teste isolado",
                risk_level=RiskLevel.MEDIUM, tool_name="terminal_sandbox",
            )
            calls.append(confirmation.confirm(request))
            return AgentOutcome(True, content="Olá pela janela")

    class FakeApplication:
        agent = FakeAgent()

        def shutdown(self):
            calls.append("shutdown")

    try:
        window = DesktopWindow(root, FakeApplication(), confirmation)
        window._confirm = lambda request: True
        window.input.insert("1.0", "Olá")
        window._send()
        deadline = time.monotonic() + 5
        while window._busy and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert not window._busy
        assert calls == [True]
        assert "Olá pela janela" in window.transcript.get("1.0", "end")
        window._close()
        assert calls == [True, "shutdown"]
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
