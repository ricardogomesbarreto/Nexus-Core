"""The desktop app catalog cannot launch arbitrary programs by browsing it."""
from types import SimpleNamespace

from nexus.desktop import apps_catalog


def test_catalog_only_exposes_fixed_app_ids(monkeypatch):
    monkeypatch.setattr(apps_catalog.os.path, "isfile", lambda path: True)
    monkeypatch.setattr(apps_catalog.os, "access", lambda path, mode: True)
    monkeypatch.setattr(apps_catalog.OpenDefaultBrowserTool, "_system_binary",
                        lambda name: "/usr/bin/" + name)
    assert [item[0] for item in apps_catalog.available_apps()] == [
        "browser", "files", "terminal"
    ]


def test_catalog_launch_requires_confirmation_for_terminal(monkeypatch):
    import tkinter as tk
    from tkinter import messagebox, ttk

    try:
        root = tk.Tk()
    except tk.TclError:
        import pytest
        pytest.skip("Display Tk não disponível")
    root.withdraw()
    launches = []
    monkeypatch.setattr(apps_catalog, "available_apps", lambda: (
        ("browser", "Navegador padrão", True),
        ("terminal", "Terminal", True)))
    monkeypatch.setattr(messagebox, "askyesno", lambda *args, **kwargs: False)
    monkeypatch.setattr(apps_catalog.LaunchApplicationTool, "execute",
                        lambda self, application: launches.append(application) or
                        SimpleNamespace(success=True, error=None))
    monkeypatch.setattr(apps_catalog.OpenDefaultBrowserTool, "execute",
                        lambda self: launches.append("browser") or
                        SimpleNamespace(success=True, error=None))
    window = apps_catalog.open_apps_catalog(root)
    try:
        buttons = [child for child in window.winfo_children()[0].winfo_children()
                   if isinstance(child, ttk.Frame)]
        buttons[1].winfo_children()[-1].invoke()
        assert launches == []
        buttons[0].winfo_children()[-1].invoke()
        assert launches == ["browser"]
    finally:
        window.destroy()
        root.destroy()
