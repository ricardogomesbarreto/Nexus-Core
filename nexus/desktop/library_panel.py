"""Biblioteca textual nativa, opt-in, baseada no PostgreSQL local."""
from queue import Empty, Queue
from threading import Thread

from nexus.config.settings import settings
from nexus.knowledge.answer import answer_from_hits
from nexus.knowledge.store import PostgreSQLKnowledgeBase


def open_library(root, app):
    import tkinter as tk
    from tkinter import filedialog, messagebox, ttk

    window = tk.Toplevel(root)
    window.title("Nexus Core — Biblioteca local")
    window.geometry("820x580")
    window.minsize(620, 430)
    panel = ttk.Frame(window, padding=14, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="BIBLIOTECA TEXTUAL · POSTGRESQL LOCAL",
              style="Nexus.Section.TLabel").pack(anchor="w")
    ttk.Label(panel, text="Importe .txt/.md do seu diretório pessoal. Pesquise sem modelo; perguntar ativa o Ollama local.",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(0, 8))
    listing = tk.Listbox(panel, height=5, exportselection=False,
                         bg="#ffffff", fg="#382631", selectbackground="#722F37")
    listing.pack(fill="x")
    query = ttk.Entry(panel)
    query.pack(fill="x", pady=(8, 4))
    query.insert(0, "Digite o assunto para buscar ou perguntar")
    reading = ttk.Frame(panel, style="Nexus.App.TFrame")
    reading.pack(fill="both", expand=True, pady=(6, 0))
    display = tk.Text(reading, height=12, wrap="word", state="disabled",
                      bg="#ffffff", fg="#382631", padx=10, pady=8)
    scrollbar = ttk.Scrollbar(reading, command=display.yview)
    display.configure(yscrollcommand=scrollbar.set)
    display.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    status = ttk.Label(panel, text="Consultando documentos locais…",
                       style="Nexus.Caption.TLabel")
    status.pack(anchor="w", pady=(6, 0))
    controls = ttk.Frame(panel, style="Nexus.App.TFrame")
    controls.pack(fill="x", pady=(6, 0))
    queue = Queue()
    document_ids = []
    busy = False

    def work(operation, value=None):
        nonlocal busy
        if busy:
            return
        busy = True
        status.configure(text="Processando localmente…")

        def worker():
            store = None
            try:
                store = PostgreSQLKnowledgeBase(settings)
                store.initialize()
                if operation == "import":
                    result = store.ingest(value)
                elif operation == "search":
                    result = store.search(value, 5)
                elif operation == "answer":
                    hits = store.search(value, 3, for_context=True)
                    result = answer_from_hits(value, hits,
                                              app.model_router if hits else None)
                elif operation == "delete":
                    result = store.delete(value)
                else:
                    result = None
                docs = store.list_documents(20)
                queue.put((operation, result, docs, None))
            except Exception:
                # Never print document text, paths, model prompts or credentials.
                queue.put((operation, None, None,
                           "Consulta indisponível. Confira PostgreSQL, Ollama e os limites do arquivo."))
            finally:
                if store is not None:
                    store.close()
        Thread(target=worker, name="nexus-library", daemon=True).start()

    def import_file():
        path = filedialog.askopenfilename(parent=window, title="Importar texto local",
                                          filetypes=(("Texto UTF-8", "*.txt *.md"),))
        if path:
            work("import", path)

    def current_query():
        value = query.get().strip()
        if not 1 <= len(value) <= 160 or value == "Digite o assunto para buscar ou perguntar":
            status.configure(text="Digite uma pergunta de 1 a 160 caracteres.")
            return None
        return value

    def search():
        value = current_query()
        if value is not None:
            work("search", value)

    def ask():
        value = current_query()
        if value is not None:
            work("answer", value)

    def remove():
        positions = listing.curselection()
        if positions and not busy and messagebox.askyesno(
            "Nexus Core", "Excluir este documento da biblioteca local?",
            parent=window,
        ):
            work("delete", document_ids[positions[0]])

    for col in (0, 1):
        controls.columnconfigure(col, weight=1)
    for index, (label, action) in enumerate((("Importar texto", import_file),
                          ("Pesquisar trechos", search),
                          ("Perguntar aos documentos", ask),
                          ("Excluir selecionado", remove))):
        ttk.Button(controls, text=label, command=action,
                   style="Nexus.TButton").grid(row=index // 2, column=index % 2,
                                               sticky="ew", padx=3, pady=2)

    def poll():
        nonlocal busy, document_ids
        if not window.winfo_exists():
            return
        try:
            operation, result, docs, error = queue.get_nowait()
        except Empty:
            window.after(80, poll)
            return
        busy = False
        if error:
            status.configure(text=error)
        else:
            document_ids = [d.id for d in docs]
            listing.delete(0, "end")
            for doc in docs:
                listing.insert("end", f"{doc.id} · {doc.name} · {doc.chunk_count} trechos")
            lines = []
            if operation == "search":
                lines = [f"Fonte {h.document_id}:{h.chunk_id} · {h.name}\n{h.text}"
                         for h in result]
            elif operation == "answer":
                lines = [result["answer"], "", "Trechos consultados:"]
                lines += [f"{s['document_id']}:{s['chunk_id']} · {s['name']}\n{s['excerpt']}"
                          for s in result["sources"]]
                if result["model_used"]:
                    lines += ["", "Resposta gerada localmente; confira os trechos originais."]
            elif operation == "import":
                lines = [f"Documento {result.id} importado." if result.added
                         else f"Documento {result.id} já está na biblioteca."]
            elif operation == "delete":
                lines = ["Documento excluído." if result else "Documento não encontrado."]
            display.configure(state="normal")
            display.delete("1.0", "end")
            display.insert("1.0", "\n\n".join(lines) if lines else "Nenhum resultado encontrado.")
            display.configure(state="disabled")
            status.configure(text=f"{len(docs)} documentos listados · operação concluída")
        window.after(80, poll)

    work("list")
    window.after(80, poll)
    return window
