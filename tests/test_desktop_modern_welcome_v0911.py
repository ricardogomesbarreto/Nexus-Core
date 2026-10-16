"""Desktop welcome truthfulness and compact, modern Tk layout."""

import os
import time
from types import SimpleNamespace

import pytest

from nexus.desktop.welcome import desktop_startup_message


def test_welcome_only_confirms_services_reported_ready():
    class HealthyApp:
        def status(self):
            return SimpleNamespace(database=True, model_layer=True)
    message, caption = desktop_startup_message(HealthyApp())
    assert message.startswith("Bem-vindo ao NEXUS CORE!")
    assert "PostgreSQL local está inicializado" in message
    assert "PostgreSQL local pronto" in caption
    assert "verificação real" in message
    assert "100% funcional" not in message
    assert "todos os recursos estão prontos" not in message.lower()


def test_welcome_does_not_claim_database_or_hardware_without_status():
    message, caption = desktop_startup_message(object())
    assert "A interface foi aberta" in message
    assert "PostgreSQL local está inicializado" not in message
    assert "Serviços e dispositivos a verificar" in caption


def test_welcome_survives_status_failure_without_side_effects():
    class FailedStatusApp:
        def status(self):
            raise RuntimeError("service temporarily unavailable")
    message, caption = desktop_startup_message(FailedStatusApp())
    assert "A interface foi aberta" in message
    assert "Serviços e dispositivos a verificar" in caption


@pytest.mark.skipif(not os.environ.get("DISPLAY"), reason="Requer Tk/Xvfb")
def test_desktop_layout_keeps_buttons_visible_and_equal_width_on_small_window():
    import tkinter as tk
    from tkinter import ttk

    from nexus.agent import AgentOutcome
    from nexus.desktop.confirmation import DesktopConfirmation
    from nexus.desktop.window import DesktopWindow

    class App:
        def __init__(self):
            self.agent = self
            self.called = []
            self.shutdown_called = False

        def run(self, prompt, **kwargs):
            self.called.append(prompt)
            return AgentOutcome(True, content="Ok")

        def status(self):
            return SimpleNamespace(database=True)

        def shutdown(self):
            self.shutdown_called = True

    class Recognizer:
        def recognize_continuous(self, cancelled):
            while not cancelled():
                time.sleep(0.01)
            return ""

        def stop(self):
            pass

    class Speaker:
        def speak(self, text, voice):
            pass

        def stop(self):
            pass

    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = App()
    try:
        window = DesktopWindow(root, app, confirmation,
                               recognizer=Recognizer(), speaker=Speaker())
        root.geometry("770x570")
        root.update()
        assert root.minsize() == (770, 570)
        assert ttk.Style(root).lookup("Nexus.Header.TFrame", "background") == "#241c24"
        assert ttk.Style(root).lookup("Nexus.Primary.TButton", "background") == "#722F37"
        assert window._brand_image is not None
        assert "Bem-vindo ao NEXUS CORE!" in window.transcript.get("1.0", "end")
        assert "PostgreSQL local está inicializado" in window.transcript.get("1.0", "end")
        assert not app.called  # Welcome never uses Ollama or agent tools.
        assert window.send_button.cget("style") == "Nexus.Primary.TButton"
        actions = [
            window.suggest_button, window.send_button, window.cancel_button,
            window.mic_button, window.shutdown_button,
        ]
        assert all(btn.winfo_ismapped() for btn in actions)
        positions = [btn.winfo_rootx() for btn in actions]
        assert positions == sorted(positions)
        widths = [btn.winfo_width() for btn in actions]
        assert max(widths) - min(widths) <= 10
        for widget in (*actions, window.input, window.status):
            assert widget.winfo_rootx() >= root.winfo_rootx()
            assert widget.winfo_rootx() + widget.winfo_width() <= (
                root.winfo_rootx() + root.winfo_width() + 2
            )
            assert widget.winfo_rooty() + widget.winfo_height() <= (
                root.winfo_rooty() + root.winfo_height() + 2
            )
        assert window.status.winfo_rooty() > window.send_button.winfo_rooty()
        assert len(window._vision_buttons) == 3
        vision_widths = [btn.winfo_width() for btn in window._vision_buttons]
        assert max(vision_widths) - min(vision_widths) <= 10
        assert window.input.winfo_ismapped()
        assert window.transcript.winfo_height() >= 70
        window._close()
        deadline = time.monotonic() + 5
        while not app.shutdown_called and time.monotonic() < deadline:
            root.update()
            time.sleep(0.01)
        assert app.shutdown_called
    finally:
        confirmation.close()
        try:
            root.destroy()
        except tk.TclError:
            pass
