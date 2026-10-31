"""Small native catalog of approved local desktop applications.

No package manager, container daemon, network fetch, or arbitrary launcher
is invoked by browsing the catalog. Launching remains an explicit action.
"""
from __future__ import annotations

import os

from nexus.tools.desktop_apps import LaunchApplicationTool, OpenDefaultBrowserTool


def available_apps() -> tuple[tuple[str, str, bool], ...]:
    """Inspect only fixed binary locations, without executing any app."""
    browser_ready = all(OpenDefaultBrowserTool._system_binary(name)
                        for name in ("xdg-settings", "gtk-launch"))
    items = [("browser", "Navegador padrão", bool(browser_ready))]
    for key, label in (("files", "Gerenciador de arquivos"),
                       ("terminal", "Terminal")):
        names = LaunchApplicationTool.APPLICATIONS[key]
        found = any(os.path.isfile(os.path.join(directory, name))
                    and os.access(os.path.join(directory, name), os.X_OK)
                    for name in names for directory in LaunchApplicationTool.SYSTEM_BIN_DIRS)
        items.append((key, label, found))
    return tuple(items)


def open_apps_catalog(root):
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Toplevel(root)
    window.title("Nexus Core — Aplicativos locais")
    window.geometry("620x330")
    panel = ttk.Frame(window, padding=16, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="APLICATIVOS DISPONÍVEIS NESTE COMPUTADOR",
              style="Nexus.Section.TLabel").pack(anchor="w")
    ttk.Label(panel, text="Abre somente aplicativos conhecidos, por ação explícita."
              " Não instala nem baixa programas.",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(2, 12))
    status = ttk.Label(panel, text="Selecione um aplicativo.", style="Nexus.Caption.TLabel")
    status.pack(side="bottom", anchor="w", pady=(8, 0))

    def launch(key):
        if key != "browser" and not messagebox.askyesno(
            "Nexus Core", "Abrir este aplicativo local?", parent=window
        ):
            status.configure(text="Abertura cancelada.")
            return
        result = (OpenDefaultBrowserTool().execute() if key == "browser"
                  else LaunchApplicationTool().execute(key))
        status.configure(text="Aplicativo solicitado." if result.success
                         else result.error or "Aplicativo indisponível.")

    for key, label, found in available_apps():
        row = ttk.Frame(panel, style="Nexus.App.TFrame")
        row.pack(fill="x", pady=3)
        ttk.Label(row, text=label, style="Nexus.Section.TLabel").pack(side="left")
        ttk.Button(row, text="Abrir", command=lambda selected=key: launch(selected),
                   state="normal" if found else "disabled",
                   style="Nexus.TButton").pack(side="right")
    return window
