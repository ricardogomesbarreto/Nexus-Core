def test_desktop_reports_missing_graphical_session(monkeypatch, capsys):
    import tkinter

    from nexus.desktop.window import launch_desktop

    def no_display():
        raise tkinter.TclError("headless")

    monkeypatch.setattr(tkinter, "Tk", no_display)
    assert launch_desktop() == 2
    assert "sessão gráfica Linux" in capsys.readouterr().err
