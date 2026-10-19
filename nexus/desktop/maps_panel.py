"""Prévia local de mapas raster sem servidor, rede ou navegador."""

import io
from queue import Empty, Queue
from threading import Thread

from nexus.maps.local import LocalMapError, read_tile


def open_maps(root):
    import tkinter as tk
    from tkinter import filedialog, ttk
    from PIL import Image, ImageTk

    window = tk.Toplevel(root)
    window.title("Nexus Core — Mapas locais")
    window.geometry("840x720")
    window.minsize(520, 470)
    panel = ttk.Frame(window, padding=14, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="MAPAS LOCAIS · PRÉVIA RASTER",
              style="Nexus.Section.TLabel").pack(anchor="w")
    ttk.Label(panel, text="Escolha um mapa .pmtiles seu. Sem downloads, serviços ou envio de dados.",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(0, 8))
    status = ttk.Label(panel, text="Aguardando escolha do arquivo.",
                       style="Nexus.Caption.TLabel")
    status.pack(anchor="w", pady=(4, 6))
    image = ttk.Label(panel, anchor="center")
    image.pack(fill="both", expand=True)
    attribution = ttk.Label(panel, text="", style="Nexus.Caption.TLabel")
    attribution.pack(anchor="w")
    controls = ttk.Frame(panel, style="Nexus.App.TFrame")
    controls.pack(fill="x", pady=(8, 0))
    events = Queue()
    current = None
    path = None
    busy = False

    def load(coords=None):
        nonlocal busy
        if path is None or busy:
            return
        busy = True
        status.configure(text="Lendo posição local…")

        def worker():
            try:
                events.put((read_tile(path, coords), None))
            except LocalMapError as exc:
                events.put((None, str(exc)))
        Thread(target=worker, name="nexus-map-preview", daemon=True).start()

    def choose():
        nonlocal path
        selected = filedialog.askopenfilename(parent=window, title="Escolher mapa local",
                                              filetypes=(("Mapas locais", "*.pmtiles"),))
        if selected and not busy:
            path = selected
            load()

    def move(dx, dy):
        if current:
            z, x, y = current.z, current.x + dx, current.y + dy
            if 0 <= x < 1 << z and 0 <= y < 1 << z:
                load((z, x, y))

    def zoom(delta):
        if current:
            z = current.z + delta
            if current.min_zoom <= z <= current.max_zoom:
                x = current.x * 2 if delta > 0 else current.x // 2
                y = current.y * 2 if delta > 0 else current.y // 2
                load((z, x, y))

    for label, action in (("Abrir mapa…", choose), ("←", lambda: move(-1, 0)),
                          ("→", lambda: move(1, 0)), ("↑", lambda: move(0, -1)),
                          ("↓", lambda: move(0, 1)), ("−", lambda: zoom(-1)),
                          ("+", lambda: zoom(1))):
        ttk.Button(controls, text=label, command=action,
                   style="Nexus.TButton").pack(side="left", padx=3)

    def poll():
        nonlocal current, busy
        if not window.winfo_exists():
            return
        try:
            result, error = events.get_nowait()
        except Empty:
            window.after(80, poll)
            return
        busy = False
        if error:
            status.configure(text=error)
        else:
            current = result
            photo = ImageTk.PhotoImage(Image.open(io.BytesIO(result.image)), master=window)
            image.configure(image=photo)
            image.image = photo
            status.configure(text=f"Mosaico local · zoom {result.z} · posição {result.x}/{result.y}")
            attribution.configure(text=f"Créditos informados no arquivo: {result.attribution}" if result.attribution else
                                  "Confira a licença e os créditos do arquivo de mapa usado.")
        window.after(80, poll)

    window.after(80, poll)
    return window
