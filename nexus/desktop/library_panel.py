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
    tutor_controls = ttk.Frame(panel, style="Nexus.App.TFrame")
    tutor_controls.pack(fill="x", pady=(3, 0))
    ttk.Label(tutor_controls, text="Nível do tutor:", style="Nexus.Caption.TLabel").pack(
        side="left", padx=(0, 6))
    tutor_level = ttk.Combobox(
        tutor_controls, values=("Iniciante", "Intermediário", "Avançado"),
        state="readonly", width=15,
    )
    tutor_level.set("Iniciante")
    tutor_level.pack(side="left")

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
    source_hits = []
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
                if operation == "zim_article":
                    from nexus.knowledge.zim_article import LocalZimReader
                    result = LocalZimReader().read(*value)
                    queue.put((operation, result, None, None))
                    return
                if operation == "catalog":
                    from nexus.knowledge.offline_catalog import list_offline_materials
                    result = list_offline_materials(value)
                    queue.put((operation, result, None, None))
                    return
                if operation == "transcribe":
                    from nexus.voice.file_transcription import LocalWavTranscriber
                    result = LocalWavTranscriber().transcribe(value)
                    queue.put((operation, result, None, None))
                    return
                store = PostgreSQLKnowledgeBase(settings)
                store.initialize()
                if operation == "import":
                    result = store.ingest(value)
                elif operation == "search":
                    result = store.search(value, 5)
                elif operation == "tutor":
                    from nexus.study.tutor import tutor_question
                    topic, level = value
                    prompt = tutor_question(topic, level)
                    hits = store.search(topic, 3, for_context=True)
                    result = answer_from_hits(prompt, hits,
                                              app.model_router if hits else None)
                elif operation in ("answer", "summary", "study_plan", "tutor"):
                    hits = store.search(value, 3, for_context=True)
                    prompt = value
                    if operation == "summary":
                        prompt = "Resuma com fontes os trechos sobre: " + value[:120]
                    elif operation == "study_plan":
                        prompt = "Proponha etapas de estudo baseadas nas fontes sobre: " + value[:100]
                    result = answer_from_hits(prompt, hits,
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

    def summarize():
        value = current_query()
        if value is not None:
            work("summary", value)

    def tutor_guided():
        value = current_query()
        if value is None:
            return
        if len(value) > 65:
            status.configure(text="Para o tutor, use um assunto de até 65 caracteres.")
            return
        work("tutor", (value, tutor_level.get()))

    def study_plan():
        value = current_query()
        if value is not None:
            work("study_plan", value)

    def remove():
        positions = listing.curselection()
        if positions and not busy and messagebox.askyesno(
            "Nexus Core", "Excluir este documento da biblioteca local?",
            parent=window,
        ):
            work("delete", document_ids[positions[0]])

    def read_zim_article():
        if busy:
            return
        from tkinter import simpledialog
        archive = filedialog.askopenfilename(
            parent=window, title="Selecionar enciclopédia ZIM",
            filetypes=(("Arquivo ZIM", "*.zim"),),
        )
        if not archive:
            return
        url = simpledialog.askstring(
            "Nexus Core — artigo ZIM",
            "Informe o caminho/URL do artigo dentro do ZIM (ex.: Wikipedia.html):",
            parent=window,
        )
        if not url:
            return
        if messagebox.askyesno(
            "Nexus Core — enciclopédia offline",
            "Ler somente este artigo do ZIM selecionado usando zimdump local? "
            "Nenhum servidor será iniciado.",
            parent=window,
        ):
            work("zim_article", (archive, url.strip()))

    def browse_offline_catalog():
        if busy:
            return
        directory = filedialog.askdirectory(parent=window,
                                            title="Escolher pasta de materiais offline")
        if directory:
            work("catalog", directory)

    def transcribe_audio():
        if busy:
            return
        path = filedialog.askopenfilename(
            parent=window, title="Transcrever WAV local",
            filetypes=(("Áudio WAV PCM", "*.wav"),),
        )
        if path and messagebox.askyesno(
            "Nexus Core — transcrição local",
            "Transcrever este WAV localmente com Vosk? O áudio não será salvo na biblioteca.",
            parent=window,
        ):
            work("transcribe", path)

    def chosen_voice():
        selector = getattr(app, "voice_selector", None)
        if selector is None:
            return "Feminina"
        try:
            return selector.get()
        except Exception:
            return "Feminina"

    def playback_profile():
        return {
            "voice": chosen_voice(),
            "speed": getattr(app, "_speech_speed_percent", 100) / 100,
            "volume": getattr(app, "_speech_volume_percent", 100),
        }

    def practice():
        if busy:
            status.configure(text="Aguarde a operação atual.")
            return
        from nexus.desktop.study_panel import open_study
        open_study(root, **playback_profile())

    def create_card():
        if busy or not source_hits:
            status.configure(text="Pesquise um assunto primeiro para selecionar o primeiro trecho.")
            return
        from nexus.desktop.study_panel import open_study
        open_study(root, source_hits[0], **playback_profile())

    for col in (0, 1):
        controls.columnconfigure(col, weight=1)
    for index, (label, action) in enumerate((("Importar texto", import_file),
                          ("Pesquisar trechos", search),
                          ("Perguntar aos documentos", ask),
                          ("Excluir selecionado", remove),
                          ("Criar cartão do 1º trecho", create_card),
                          ("Revisar cartões", practice),
                          ("Transcrever WAV local", transcribe_audio),
                          ("Catálogo offline", browse_offline_catalog),
                          ("Ler artigo ZIM", read_zim_article),
                          ("Resumir trechos com IA local", summarize),
                          ("Plano de estudo com IA local", study_plan),
                          ("Tutor guiado por fontes", tutor_guided))):
        ttk.Button(controls, text=label, command=action,
                   style="Nexus.TButton").grid(row=index // 2, column=index % 2,
                                               sticky="ew", padx=3, pady=2)

    def poll():
        nonlocal busy, document_ids, source_hits
        if not window.winfo_exists():
            return
        try:
            operation, result, docs, error = queue.get_nowait()
        except Empty:
            window.after(80, poll)
            return
        busy = False
        if operation == "zim_article":
            source_hits = []
            display.configure(state="normal")
            display.delete("1.0", "end")
            display.insert("1.0", result if not error else
                           "Não foi possível ler o artigo. Confira o ZIM e zim-tools.")
            display.configure(state="disabled")
            status.configure(text="Artigo consultado localmente, sem salvar." if not error else error)
            window.after(80, poll)
            return
        if operation == "catalog":
            source_hits = []
            lines = ([f"{m.filename} · {m.category} · {m.bytes} bytes" for m in result]
                     if not error else ["Catálogo indisponível ou diretório não autorizado."])
            display.configure(state="normal")
            display.delete("1.0", "end")
            display.insert("1.0", "\\n".join(lines) if lines else
                           "Nenhum arquivo ZIM ou material de curso encontrado na pasta.")
            display.configure(state="disabled")
            status.configure(text=f"{len(result)} materiais identificados (metadados)." if not error
                             else error)
            window.after(80, poll)
            return
        if operation == "transcribe":
            source_hits = []
            display.configure(state="normal")
            display.delete("1.0", "end")
            display.insert("1.0", result if not error else
                           "Transcrição indisponível. Confira o WAV e o modelo Vosk local.")
            display.configure(state="disabled")
            status.configure(text="Transcrição local concluída; não salva." if not error else error)
            window.after(80, poll)
            return
        if error:
            source_hits = []
            status.configure(text=error)
        else:
            source_hits = result if operation == "search" else []
            document_ids = [d.id for d in docs]
            listing.delete(0, "end")
            for doc in docs:
                listing.insert("end", f"{doc.id} · {doc.name} · {doc.chunk_count} trechos")
            lines = []
            if operation == "search":
                lines = [f"Fonte {h.document_id}:{h.chunk_id} · {h.name}\n{h.text}"
                         for h in result]
            elif operation in ("answer", "summary", "study_plan"):
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
