"""Prática nativa de cartões locais. Sem download, servidor ou modelo extra."""

from queue import Empty, Queue
from threading import Event, Thread

from nexus.config.settings import settings
from nexus.study.store import PostgreSQLStudyCards, StudyError


def open_study(root, source_hit=None, *, voice="Feminina", speed=1.0, volume=100):
    import tkinter as tk
    from tkinter import messagebox, ttk

    window = tk.Toplevel(root)
    window.title("Nexus Core — Estudo local")
    window.geometry("780x560")
    window.minsize(600, 440)
    panel = ttk.Frame(window, padding=14, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="ESTUDO · BIBLIOTECA LOCAL",
              style="Nexus.Section.TLabel").pack(anchor="w")
    source = (f"Trecho selecionado: {source_hit.name} ({source_hit.document_id}:"
              f"{source_hit.chunk_id})" if source_hit else
              "Pesquise um texto na Biblioteca para criar um cartão.")
    ttk.Label(panel, text=source, style="Nexus.Caption.TLabel",
              wraplength=700).pack(anchor="w", pady=(0, 8))
    ttk.Label(panel, text="Pergunta", style="Nexus.Section.TLabel").pack(anchor="w")
    question = ttk.Entry(panel)
    question.pack(fill="x")
    ttk.Label(panel, text="Resposta literal do trecho (até 1000 caracteres)",
              style="Nexus.Section.TLabel").pack(anchor="w", pady=(8, 0))
    answer = ttk.Entry(panel)
    answer.pack(fill="x")
    ttk.Label(panel, text="Nenhum texto é gerado automaticamente; a resposta deve aparecer na fonte.",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(4, 8))
    due_list = tk.Listbox(panel, height=5, exportselection=False,
                          bg="#ffffff", fg="#382631", selectbackground="#722F37")
    due_list.pack(fill="x")
    display = tk.Text(panel, height=8, wrap="word", state="disabled",
                      bg="#ffffff", fg="#382631", padx=10, pady=8)
    display.pack(fill="both", expand=True, pady=(6, 0))
    status = ttk.Label(panel, text="Consultando revisões locais…",
                       style="Nexus.Caption.TLabel")
    status.pack(anchor="w", pady=(6, 0))
    controls = ttk.Frame(panel, style="Nexus.App.TFrame")
    controls.pack(fill="x", pady=(6, 0))
    messages = Queue()
    cards = []
    current = None
    revealed = False
    busy = False
    exercise_session = None
    exercise_progress_saved = False
    speech_messages = Queue()
    speech_cancel = Event()
    speech_busy = False
    speech_paused = False
    speaker = None

    def show(text):
        display.configure(state="normal")
        display.delete("1.0", "end")
        display.insert("1.0", text)
        display.configure(state="disabled")

    def run(operation, *args):
        nonlocal busy
        if busy:
            return
        busy = True
        status.configure(text="Consultando PostgreSQL local…")

        def worker():
            store = None
            try:
                store = PostgreSQLStudyCards(settings)
                store.initialize()
                result = (getattr(store, operation)(*args)
                          if operation != "refresh" else None)
                messages.put((operation, result, store.due(), None))
            except Exception:
                # No question, answer, document path or credentials in the log.
                messages.put((operation, None, None,
                              "Estudo indisponível. Confira a biblioteca e o PostgreSQL local."))
            finally:
                if store is not None:
                    store.close()
        Thread(target=worker, name="nexus-study", daemon=True).start()

    def create():
        if source_hit is None:
            status.configure(text="Pesquise um trecho na Biblioteca antes de criar um cartão.")
            return
        try:
            prompt = PostgreSQLStudyCards._text(question.get(), 240, "Pergunta")
            reply = PostgreSQLStudyCards._text(answer.get(), 1000, "Resposta")
        except StudyError as exc:
            status.configure(text=str(exc))
            return
        if not messagebox.askyesno("Nexus Core — estudo",
                                   "Salvar este cartão vinculado ao trecho selecionado?",
                                   parent=window):
            return
        run("create", source_hit.chunk_id, prompt, reply)

    def select(event=None):
        nonlocal current, revealed
        selected = due_list.curselection()
        if not selected or busy:
            return
        current = cards[selected[0]]
        revealed = False
        show(f"Fonte: {current.source_name}\n\nPergunta: {current.question}\n\n"
             "Pense na resposta e clique em Mostrar resposta.")

    def reveal():
        nonlocal revealed
        if current is None or busy:
            return
        revealed = True
        show(f"Pergunta: {current.question}\n\nResposta: {current.answer}\n\n"
             f"Fonte: {current.source_name}\n{current.source_excerpt}")

    def grade(correct):
        if current is None or not revealed or busy:
            status.configure(text="Mostre a resposta antes de registrar o resultado.")
            return
        run("grade", current.id, correct)

    def remove():
        if current is not None and not busy and messagebox.askyesno(
            "Nexus Core — estudo", "Excluir este cartão? O documento original permanece.",
            parent=window,
        ):
            run("delete", current.id)

    def generate_exercises():
        nonlocal exercise_session, exercise_progress_saved
        if busy or source_hit is None:
            status.configure(text="Pesquise um trecho na Biblioteca antes de gerar exercícios.")
            return
        from nexus.study_session import StudySession
        from tkinter import simpledialog
        if not messagebox.askyesno(
            "Nexus Core — estudo",
            "Criar questões locais a partir do trecho selecionado? Não serão salvas.",
            parent=window,
        ):
            return
        exercise_session = StudySession.from_text(source_hit.text, limit=5)
        exercise_progress_saved = False
        if not exercise_session.questions:
            status.configure(text="O trecho não contém frases adequadas para questões.")
            return
        show(exercise_session.next_question().prompt)
        status.configure(text=f"{len(exercise_session.questions)} questões locais criadas")

    def answer_exercise():
        nonlocal exercise_session
        from tkinter import simpledialog
        if exercise_session is None or exercise_session.completed:
            status.configure(text="Gere questões antes de responder.")
            return
        response = simpledialog.askstring(
            "Nexus Core — exercício", exercise_session.next_question().prompt,
            parent=window,
        )
        if response is None:
            return
        try:
            attempt = exercise_session.submit(response)
        except (TypeError, ValueError):
            status.configure(text="Resposta inválida ou acima do limite.")
            return
        correct, answered = exercise_session.score
        message = ("Resposta literal correta." if attempt.correct else
                   f"Resposta literal esperada: {attempt.question.expected_answer}")
        message += f"\nFonte: {attempt.question.source_excerpt}"
        next_item = exercise_session.next_question()
        if next_item:
            message += f"\n\nPróxima questão:\n{next_item.prompt}"
        else:
            message += f"\n\nSessão concluída: {correct}/{answered} respostas literais corretas."
        show(message)
        status.configure(text=f"Exercícios: {answered}/{len(exercise_session.questions)} respondidos")

    def save_progress():
        if source_hit is None or exercise_session is None or not exercise_session.completed:
            status.configure(text="Conclua os exercícios de um trecho da Biblioteca.")
            return
        if exercise_progress_saved or busy:
            status.configure(text="Progresso já registrado ou operação em andamento.")
            return
        if not messagebox.askyesno(
            "Nexus Core — progresso",
            "Salvar somente o resultado desta sessão no PostgreSQL local? "
            "As respostas não serão armazenadas.",
            parent=window,
        ):
            return
        correct, total = exercise_session.score
        run("record_session", source_hit.chunk_id, correct, total)

    def show_history():
        run("recent_sessions")

    def read_excerpt():
        nonlocal speech_busy, speaker, speech_cancel, speech_paused
        if speech_busy:
            status.configure(text="Leitura já em andamento. Use Parar leitura.")
            return
        if source_hit is not None:
            excerpt = source_hit.text
        elif current is not None and revealed:
            excerpt = current.source_excerpt
        else:
            status.configure(text="Selecione um trecho na Biblioteca ou revele um cartão.")
            return
        if not excerpt.strip():
            return
        from nexus.voice.local import LocalSpeaker
        speaker = LocalSpeaker()
        speech_cancel = Event()
        speech_busy = True
        speech_paused = False
        status.configure(text="Lendo trecho com voz local…")
        selected_voice = voice if voice in LocalSpeaker.VOICES else "Feminina"

        def worker():
            try:
                options = {"cancelled": speech_cancel.is_set}
                if speed != 1.0 or volume != 100:
                    options["speed"] = speed
                    options["volume"] = volume
                speaker.speak(excerpt[:LocalSpeaker.MAX_SPEECH], selected_voice,
                              **options)
                speech_messages.put(None)
            except Exception:
                speech_messages.put("Leitura de voz indisponível. Confira Piper/RHVoice/eSpeak.")

        Thread(target=worker, name="nexus-study-speech", daemon=True).start()

    def toggle_pause_reading():
        nonlocal speech_paused
        if not speech_busy or speaker is None:
            status.configure(text="Nenhuma leitura ativa para pausar.")
            return
        action = speaker.resume if speech_paused else speaker.pause
        if action():
            speech_paused = not speech_paused
            status.configure(text="Leitura pausada." if speech_paused
                             else "Leitura retomada.")
        else:
            status.configure(text="A leitura não está disponível para pausa agora.")

    def stop_reading():
        nonlocal speech_paused
        speech_paused = False
        speech_cancel.set()
        if speaker is not None:
            speaker.stop()

    def poll_speech():
        nonlocal speech_busy
        if not window.winfo_exists():
            return
        try:
            result = speech_messages.get_nowait()
        except Empty:
            window.after(100, poll_speech)
            return
        speech_busy = False
        status.configure(text=result or "Leitura de voz concluída ou interrompida.")
        window.after(100, poll_speech)

    def close_study():
        stop_reading()
        window.destroy()

    buttons = (("Criar cartão", create), ("Atualizar revisões", lambda: run("refresh")),
               ("Mostrar resposta", reveal), ("Acertei", lambda: grade(True)),
               ("Repetir", lambda: grade(False)), ("Excluir cartão", remove),
               ("Gerar exercícios do trecho", generate_exercises),
               ("Responder exercício", answer_exercise),
               ("Ler trecho em voz alta", read_excerpt),
               ("Parar leitura", stop_reading),
               ("Pausar/retomar leitura", toggle_pause_reading),
               ("Salvar progresso", save_progress),
               ("Histórico de sessões", show_history))
    for column in range(3):
        controls.columnconfigure(column, weight=1)
    for index, (label, action) in enumerate(buttons):
        ttk.Button(controls, text=label, command=action,
                   style="Nexus.TButton").grid(row=index // 3, column=index % 3,
                                               sticky="ew", padx=3, pady=2)
    due_list.bind("<<ListboxSelect>>", select)

    def poll():
        nonlocal busy, cards, current, revealed, exercise_progress_saved
        if not window.winfo_exists():
            return
        try:
            operation, result, due, error = messages.get_nowait()
        except Empty:
            window.after(80, poll)
            return
        busy = False
        if operation == "record_session":
            if not error:
                exercise_progress_saved = True
            status.configure(text=(error or "Resultado registrado no PostgreSQL local, sem respostas."))
            window.after(80, poll)
            return
        if operation == "recent_sessions":
            if error:
                status.configure(text=error)
            else:
                show("\n".join(f"Trecho {chunk}: {correct}/{total} acertos"
                               for chunk, correct, total in result)
                     if result else "Nenhum resultado de sessão registrado.")
                status.configure(text=f"{len(result)} sessões recentes.")
            window.after(80, poll)
            return
        if error:
            status.configure(text=error)
        else:
            cards = due
            current = None
            revealed = False
            due_list.delete(0, "end")
            for card in cards:
                due_list.insert("end", f"{card.id} · {card.source_name} · {card.question[:90]}")
            if operation == "create":
                question.delete(0, "end")
                answer.delete(0, "end")
            show("Escolha um cartão pendente para revisar." if cards else
                 "Nenhum cartão pendente agora. Crie um a partir de um trecho da Biblioteca.")
            status.configure(text=f"{len(cards)} cartões disponíveis · operação concluída")
        window.after(80, poll)

    window.protocol("WM_DELETE_WINDOW", close_study)
    run("refresh")
    window.after(80, poll)
    window.after(100, poll_speech)
    return window
