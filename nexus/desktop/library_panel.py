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
                if operation == "kolibri_export":
                    from nexus.knowledge.kolibri_export import inspect_kolibri_export
                    result = inspect_kolibri_export(value)
                    queue.put((operation, result, None, None))
                    return
                if operation == "kolibri_export":
            source_hits = []
            if error:
                status.configure(text="Exportação Kolibri indisponível ou protegida.")
            else:
                lines = [
                    f"Canal {item.channel_id} · banco {item.database_bytes} bytes"
                    for item in result.channels
                ]
                header = (
                    f"Exportação Kolibri: {len(result.channels)} canais. "
                    f"Diretório de recursos: {'encontrado' if result.has_content_storage else 'ausente'}."
                )
                display.configure(state="normal")
                display.delete("1.0", "end")
                display.insert("1.0", header + "\n\n" +
                               ("\n".join(lines) if lines else
                                "Nenhum banco de canal identificável."))
                display.configure(state="disabled")
                status.configure(text="Inspeção somente de metadados; nenhum canal importado.")
            window.after(80, poll)
            return
        if operation == "course":
                    from nexus.study.offline_course import load_course
                    result = load_course(value)
                    queue.put((operation, result, None, None))
                    return
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
                    from nexus.voice.audio_transcription import LocalAudioTranscriber
                    result = LocalAudioTranscriber().transcribe(value)
                    queue.put((operation, result, None, None))
                    return
                store = PostgreSQLKnowledgeBase(settings)
                store.initialize()
                if operation == "import":
                    result = store.ingest(value)
                elif operation == "search":
                    result = store.search(value, 5)
                elif operation == "semantic":
                    from nexus.knowledge.semantic_local import LocalSemanticReranker
                    term, model_name = value
                    hits = store.semantic_candidates(term, 8)
                    result = (LocalSemanticReranker().rerank(term, hits, model_name)
                              if hits else [])
                elif operation == "tutor":
                    from nexus.study.tutor import tutor_question
                    topic, level = value
                    prompt = tutor_question(topic, level)
                    hits = store.search(topic, 3, for_context=True)
                    result = answer_from_hits(prompt, hits,
                                              app.model_router if hits else None)
                elif operation in ("answer", "summary", "study_plan"):
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

    def semantic_sample():
        if busy:
            return
        from tkinter import simpledialog
        term = current_query()
        if term is None:
            return
        model_name = simpledialog.askstring(
            "Nexus Core — similaridade semântica local",
            "Nome EXATO do modelo de embeddings já instalado no Ollama:",
            parent=window,
        )
        if not model_name:
            return
        if not messagebox.askyesno(
            "Nexus Core — busca offline",
            "Comparar a pergunta com até oito trechos (busca textual e amostra "
            "de documentos recentes) usando um modelo local? "
            "Não instala modelos nem salva vetores.",
            parent=window,
        ):
            return
        work("semantic", (term, model_name.strip()))

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

    def inspect_kolibri():
        if busy:
            status.configure(text="Aguarde a operação em andamento.")
            return
        directory = filedialog.askdirectory(
            parent=window, title="Escolher KOLIBRI_DATA dentro do HOME",
        )
        if not directory:
            return
        if messagebox.askyesno(
            "Nexus Core — exportação Kolibri",
            "Examinar somente os nomes e tamanhos dos canais da pasta "
            "KOLIBRI_DATA? Não serão lidos bancos SQLite, nem iniciados "
            "serviços ou importações.",
            parent=window,
        ):
            work("kolibri_export", directory)

    def open_offline_course():
        if busy:
            status.configure(text="Aguarde a operação em andamento.")
            return
        directory = filedialog.askdirectory(
            parent=window, title="Selecionar pasta com course.json e aulas TXT/MD",
        )
        if not directory:
            return
        if messagebox.askyesno(
            "Nexus Core — cursos locais",
            "Abrir o manifesto e os metadados das aulas desta pasta? "
            "Não inicia Kolibri ou outro serviço e não importa os arquivos.",
            parent=window,
        ):
            work("course", directory)

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
            parent=window, title="Transcrever áudio local",
            filetypes=(("Áudio local", "*.wav *.mp3 *.ogg *.flac *.m4a"),),
        )
        if path and messagebox.askyesno(
            "Nexus Core — transcrição local",
            "Transcrever áudio com Vosk e FFmpeg locais, quando necessário? "
            "O arquivo e o texto não serão salvos na biblioteca.",
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
                          ("Transcrever áudio local", transcribe_audio),
                          ("Catálogo offline", browse_offline_catalog),
                          ("Abrir curso offline", open_offline_course),
                          ("Inspecionar exportação Kolibri", inspect_kolibri),
                          ("Ler artigo ZIM", read_zim_article),
                          ("Resumir trechos com IA local", summarize),
                          ("Plano de estudo com IA local", study_plan),
                          ("Tutor guiado por fontes", tutor_guided),
                          ("Similaridade semântica local", semantic_sample))):
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
        if operation == "course":
            if error:
                status.configure(text="Curso indisponível. Confira course.json e os arquivos TXT/MD.")
            else:
                from nexus.desktop.course_panel import open_course
                open_course(root, result)
                status.configure(text=f"Curso local aberto: {len(result.lessons)} aulas.")
            window.after(80, poll)
            return
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
                           "Transcrição indisponível. Confira o arquivo, FFmpeg e Vosk local.")
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
            if operation == "semantic":
                source_hits = [match.hit for match in result]
                lines = [f"Similaridade {match.score:.3f} · "
                         f"Fonte {match.hit.document_id}:{match.hit.chunk_id}"
                         f" · {match.hit.name}\n{match.hit.text}"
                         for match in result]
                if not lines:
                    lines = ["Nenhum trecho disponível para a comparação local."]
            elif operation == "search":
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
