"""Painéis nativos de anotações e dados; serviços locais só sob ação do usuário."""

from queue import Empty, Queue
from threading import Thread

from nexus.config.settings import settings
from nexus.notes.store import NoteError, PostgreSQLNotes
from nexus.tools.data_local import MAX_BYTES, OPERATIONS, transform_text, transform_recipe


def open_notes(root):
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Toplevel(root)
    window.title("Nexus Core — Anotações locais")
    window.geometry("760x540")
    window.minsize(580, 420)
    window.configure(bg="#f5f1f3")
    panel = ttk.Frame(window, padding=14, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="ANOTAÇÕES · POSTGRESQL LOCAL",
              style="Nexus.Section.TLabel").pack(anchor="w")
    ttk.Label(panel, text="Salvas somente ao clicar em Salvar; não entram automaticamente no chat.",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(0, 8))
    listing = tk.Listbox(panel, height=6, exportselection=False, bg="#ffffff",
                         fg="#382631", selectbackground="#722F37")
    listing.pack(fill="x")
    ttk.Label(panel, text="Título", style="Nexus.Section.TLabel").pack(anchor="w", pady=(8, 0))
    title = ttk.Entry(panel)
    title.pack(fill="x")
    ttk.Label(panel, text="Texto (Markdown)", style="Nexus.Section.TLabel").pack(anchor="w", pady=(8, 0))
    body = tk.Text(panel, height=8, wrap="word", bg="#ffffff", fg="#382631")
    body.pack(fill="both", expand=True)
    status = ttk.Label(panel, text="Carregando anotações…", style="Nexus.Caption.TLabel")
    status.pack(anchor="w", pady=(6, 0))
    controls = ttk.Frame(panel, style="Nexus.App.TFrame")
    controls.pack(fill="x", pady=(6, 0))
    items = []
    selected_id = None
    results = Queue()
    busy = False

    def run(operation, *args):
        nonlocal busy
        if busy:
            return
        busy = True
        status.configure(text="Processando no PostgreSQL local…")
        def worker():
            store = None
            try:
                store = PostgreSQLNotes(settings)
                store.initialize()
                result = getattr(store, operation)(*args)
                listing_result = store.list() if operation != "list" else result
                results.put((operation, result, listing_result, None))
            except Exception:
                # No database credentials or note content in diagnostics.
                results.put((operation, None, None,
                             "Falha no PostgreSQL local ou na anotação; confira o serviço e os limites."))
            finally:
                if store is not None:
                    store.close()
        Thread(target=worker, name="nexus-notes", daemon=True).start()

    def clear():
        nonlocal selected_id
        selected_id = None
        listing.selection_clear(0, "end")
        title.delete(0, "end")
        body.delete("1.0", "end")
        title.focus_set()

    def select(event=None):
        nonlocal selected_id
        positions = listing.curselection()
        if not positions or busy:
            return
        item = items[positions[0]]
        selected_id = item.id
        title.delete(0, "end")
        title.insert(0, item.title)
        body.delete("1.0", "end")
        body.insert("1.0", item.body)

    def save():
        caption = title.get().strip()
        content = body.get("1.0", "end-1c").strip()
        try:
            PostgreSQLNotes._text(caption, PostgreSQLNotes.MAX_TITLE, "Título")
            PostgreSQLNotes._text(content, PostgreSQLNotes.MAX_BODY, "Texto")
        except NoteError as exc:
            status.configure(text=str(exc))
            return
        run("update", selected_id, caption, content) if selected_id else run("create", caption, content)

    def remove():
        if selected_id is not None and messagebox.askyesno(
            "Nexus Core", "Excluir esta anotação do PostgreSQL local?", parent=window
        ):
            run("delete", selected_id)

    for label, action in (("Nova", clear), ("Salvar", save),
                          ("Excluir", remove), ("Atualizar lista", lambda: run("list"))):
        ttk.Button(controls, text=label, command=action, style="Nexus.TButton").pack(
            side="left", padx=(0, 6))
    listing.bind("<<ListboxSelect>>", select)

    def poll():
        nonlocal busy, selected_id, items
        if not window.winfo_exists():
            return
        try:
            operation, result, refreshed, error = results.get_nowait()
        except Empty:
            window.after(80, poll)
            return
        busy = False
        if error:
            status.configure(text=error)
        else:
            items = refreshed
            listing.delete(0, "end")
            for item in items:
                listing.insert("end", f"{item.id} · {item.title}")
            if operation == "delete":
                clear()
            elif operation in {"create", "update"} and result is not None:
                selected_id = result.id
            status.configure(text=f"{len(items)} anotações · ação {operation} concluída")
        window.after(80, poll)

    run("list")
    window.after(80, poll)
    return window


def open_data_tools(root):
    import tkinter as tk
    from tkinter import ttk

    window = tk.Toplevel(root)
    window.title("Nexus Core — Ferramentas de dados")
    window.geometry("680x500")
    panel = ttk.Frame(window, padding=14, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="DADOS · PROCESSAMENTO LOCAL",
              style="Nexus.Section.TLabel").pack(anchor="w")
    ttk.Label(panel, text="Cole texto não confidencial. Codificação e hash não são criptografia.",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(0, 8))
    choice = ttk.Combobox(panel, values=OPERATIONS, state="readonly")
    choice.set("sha256")
    choice.pack(fill="x")
    ttk.Label(panel, text="Receita opcional: operações separadas por vírgula (até 8).",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(6, 0))
    recipe = ttk.Entry(panel)
    recipe.pack(fill="x")
    source = tk.Text(panel, height=6, wrap="word", bg="#ffffff", fg="#382631")
    source.pack(fill="both", expand=True, pady=(8, 4))
    status = ttk.Label(panel, text="Entrada máxima: 64 KiB", style="Nexus.Caption.TLabel")
    status.pack(anchor="w")
    output = tk.Text(panel, height=5, wrap="word", bg="#ffffff", fg="#382631")
    output.pack(fill="both", expand=True, pady=(4, 0))
    output.configure(state="disabled")

    def apply():
        value = source.get("1.0", "end-1c").encode("utf-8")
        if len(value) > MAX_BYTES:
            status.configure(text="Entrada acima de 64 KiB.")
            return
        try:
            steps = recipe.get().strip()
            result = (transform_recipe(steps.split(","), value) if steps
                      else transform_text(choice.get(), value))
        except ValueError as exc:
            status.configure(text=str(exc))
            return
        output.configure(state="normal")
        output.delete("1.0", "end")
        output.insert("1.0", result)
        output.configure(state="disabled")
        status.configure(text="Concluído localmente; nada foi enviado ao modelo.")

    ttk.Button(panel, text="Processar", command=apply,
               style="Nexus.Primary.TButton").pack(anchor="w", pady=(8, 0))
    return window


def open_benchmark(root):
    import tkinter as tk
    from tkinter import ttk
    from nexus.platforms.benchmark import benchmark_local

    window = tk.Toplevel(root)
    window.title("Nexus Core — Medição local")
    panel = ttk.Frame(window, padding=18, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="MEDIÇÃO VOLUNTÁRIA DE CPU E MEMÓRIA",
              style="Nexus.Section.TLabel").pack(anchor="w")
    status = ttk.Label(panel, text="Dura cerca de 800 ms, usa 8 MiB de RAM; sem rede nem ranking.",
                       style="Nexus.Caption.TLabel")
    status.pack(anchor="w", pady=8)
    results = Queue()
    busy = False

    def poll():
        nonlocal busy
        if not window.winfo_exists():
            return
        try:
            result = results.get_nowait()
        except Empty:
            window.after(80, poll)
            return
        busy = False
        button.configure(state="normal")
        if result is None:
            status.configure(text="Não foi possível concluir a medição local.")
        else:
            status.configure(text=(f"SHA-256: {result['cpu_hash_mib_per_s']} MiB/s · "
                                   f"cópia RAM: {result['memory_copy_mib_per_s']} MiB/s · "
                                   f"{result['elapsed_ms']} ms. Não mede temperatura."))

    def run():
        nonlocal busy
        if busy:
            return
        busy = True
        button.configure(state="disabled")
        status.configure(text="Medindo localmente…")
        def measure():
            try:
                result = benchmark_local()
            except (ValueError, MemoryError, OSError):
                result = None
            results.put(result)
        Thread(target=measure,
               name="nexus-benchmark", daemon=True).start()
        window.after(80, poll)

    button = ttk.Button(panel, text="Iniciar medição", command=run,
                        style="Nexus.Primary.TButton")
    button.pack(anchor="w", pady=(4, 0))
    return window
