"""Small native catalog of approved local desktop applications.

No package manager, container daemon, network fetch, or arbitrary launcher
is invoked by browsing the catalog. Launching remains an explicit action.
"""
from __future__ import annotations

import os
from queue import Empty, Queue
from threading import Event, Thread

from nexus.tools.desktop_apps import LaunchApplicationTool, OpenDefaultBrowserTool
from nexus.tools.local_container import (IMAGE_ID, LocalContainerError,
                                         authorize_local_image, run_local_image)


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


def open_apps_catalog(root, *, gate=None):
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Toplevel(root)
    window.title("Nexus Core — Aplicativos locais")
    window.geometry("680x490")
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

    ttk.Separator(panel).pack(fill="x", pady=(12, 8))
    ttk.Label(panel, text="IMAGEM LOCAL ISOLADA · OPCIONAL",
              style="Nexus.Section.TLabel").pack(anchor="w")
    ttk.Label(panel, text="Exige Podman local sem root. ID sha256 já instalado;"
              " sem rede, volumes do host ou download. Tempo máximo: 20 s.",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(2, 5))
    image_id = ttk.Entry(panel)
    image_id.pack(fill="x")
    output = tk.Text(panel, height=5, wrap="word", bg="#ffffff", fg="#382631")
    output.pack(fill="both", expand=True, pady=(6, 0))
    output.configure(state="disabled")
    events = Queue()
    cancellation = Event()
    busy = False

    def run_container():
        nonlocal busy, cancellation
        selected = image_id.get().strip()
        if busy:
            return
        if not IMAGE_ID.fullmatch(selected):
            status.configure(text="Informe um ID sha256 completo da imagem local.")
            return
        try:
            approved_gate = authorize_local_image(
                selected,
                lambda request: messagebox.askyesno(
                    "Nexus Core", request.description + "… sem rede e sem montar "
                    "arquivos do computador?", parent=window), gate=gate)
        except LocalContainerError as exc:
            status.configure(text=str(exc))
            return
        busy = True
        cancellation = Event()
        run_button.configure(state="disabled")
        status.configure(text="Executando imagem local por até 20 segundos…")

        def worker():
            try:
                result = run_local_image(selected, cancel=cancellation)
                approved_gate.audit_logger.record_execution(
                    "local_image_run", "local_image_run",
                    "success" if result.exit_code == 0 else "failed",
                    "Processo local encerrado; código " + str(result.exit_code))
                events.put((result, None))
            except LocalContainerError as exc:
                approved_gate.audit_logger.record_execution(
                    "local_image_run", "local_image_run", "failed", str(exc))
                events.put((None, str(exc)))

        Thread(target=worker, name="nexus-local-image", daemon=True).start()

    def poll():
        nonlocal busy
        if not window.winfo_exists():
            return
        try:
            result, error = events.get_nowait()
        except Empty:
            window.after(100, poll)
            return
        busy = False
        run_button.configure(state="normal")
        output.configure(state="normal")
        output.delete("1.0", "end")
        if result is not None:
            output.insert("1.0", result.output)
        output.configure(state="disabled")
        status.configure(text=error or f"Execução concluída; código de saída {result.exit_code}.")
        window.after(100, poll)

    run_button = ttk.Button(panel, text="Executar imagem instalada", command=run_container,
                            style="Nexus.TButton")
    run_button.pack(anchor="w", pady=(6, 0))

    def close():
        cancellation.set()
        window.destroy()

    window.protocol("WM_DELETE_WINDOW", close)
    window.after(100, poll)
    return window
