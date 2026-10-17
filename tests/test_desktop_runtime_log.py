"""Live terminal events are useful without becoming a transcript."""

import logging
import time

import pytest

from nexus.desktop.runtime_log import live_event
from test_vision_desktop_integration import desktop, spin


def test_live_event_has_only_bounded_fixed_fields(caplog):
    caplog.set_level(logging.INFO, logger="nexus.desktop_runtime")
    live_event("ferramenta", "falhou", tool="secret=/home/ricardo/.ssh\npassword=abc",
               source="private camera title", elapsed_ms=9_999_999)
    assert "TESTE-LOCAL evento=ferramenta estado=falhou origem=outra ferramenta=outra duracao_ms=3600000" in caplog.text
    assert "ricardo" not in caplog.text
    assert "password" not in caplog.text
    for name, state in (("private utterance", "iniciado"), ("chat", "raw private result")):
        with pytest.raises(ValueError):
            live_event(name, state)


def test_gui_logs_chat_camera_and_consent_without_private_contents(desktop, monkeypatch, caplog):
    from tkinter import simpledialog
    from nexus.security import RiskLevel, SecurityRequest
    import nexus.desktop.window as window_module

    caplog.set_level(logging.INFO, logger="nexus.desktop_runtime")
    root, app, window, vision = desktop
    private = "MINHA_PERGUNTA_PRIVADA_426"
    window.input.insert("1.0", private)
    window._send()
    spin(root, lambda: not window._busy)
    assert "evento=chat estado=iniciado origem=texto" in caplog.text
    assert "evento=chat estado=concluido origem=texto duracao_ms=" in caplog.text
    assert private not in caplog.text

    monkeypatch.setattr(simpledialog, "askinteger", lambda *a, **kw: 0)
    monkeypatch.setattr(window.messagebox, "askyesno", lambda *a, **kw: True)
    window._start_live_camera()
    spin(root, lambda: "evento=camera estado=pronto" in caplog.text)
    assert "evento=camera estado=iniciado origem=camera_live" in caplog.text
    assert "evento=camera estado=pronto origem=camera_live" in caplog.text
    window._stop_live_camera()
    assert "evento=camera estado=desligado origem=camera_live" in caplog.text

    class StubPermissionDialog:
        def __init__(self, *args, **kwargs):
            pass
        def ask(self):
            return False

    monkeypatch.setattr(window_module, "PermissionDialog", StubPermissionDialog)
    request = SecurityRequest(action="launch_application", description=private,
                              risk_level=RiskLevel.MEDIUM,
                              tool_name="launch_application")
    assert window._confirm(request) is False
    assert "evento=autorizacao estado=solicitado ferramenta=launch_application" in caplog.text
    assert "evento=autorizacao estado=negado ferramenta=launch_application" in caplog.text
    assert private not in caplog.text

    window._busy = True
    window._operation_kind = "chat"
    window._operation_started = time.monotonic() - 11
    window._last_progress_interval = 0
    window._poll()
    window._poll()
    assert caplog.text.count("evento=chat estado=processando origem=texto") == 1
    window._finish_operation()
