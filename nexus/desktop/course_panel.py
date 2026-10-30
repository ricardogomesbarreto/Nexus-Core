"""Leitor nativo de cursos TXT/Markdown locais, sem servidor ou novas dependências.

O progresso e as respostas vivem só na memória desta janela. Não há leitura
automática de materiais antes do clique nem criação de arquivos ou banco.
"""
from __future__ import annotations

from queue import Empty, Queue
from threading import Event, Thread

from nexus.config.settings import settings
from nexus.study.offline_course import OfflineCourse, CourseError, read_lesson
from nexus.study.course_search import search_course
from nexus.study.recommendations import recommend_study_step
from nexus.study_session import StudySession


def open_course(root, course: OfflineCourse, *, voice="Feminina", speed=1.0, volume=100):
    import tkinter as tk
    from tkinter import simpledialog, ttk

    if not isinstance(course, OfflineCourse):
        raise CourseError("Curso local inválido.")

    window = tk.Toplevel(root)
    window.title("Nexus Core — Curso offline")
    window.geometry("760x550")
    window.minsize(600, 450)
    panel = ttk.Frame(window, padding=14, style="Nexus.App.TFrame")
    panel.pack(fill="both", expand=True)
    ttk.Label(panel, text="CURSOS · BIBLIOTECA LOCAL",
              style="Nexus.Section.TLabel").pack(anchor="w")
    ttk.Label(panel, text=f"{course.title} · {len(course.lessons)} aulas",
              style="Nexus.Caption.TLabel").pack(anchor="w", pady=(0, 7))
    listing = tk.Listbox(panel, height=5, exportselection=False,
                         bg="#ffffff", fg="#382631", selectbackground="#722F37")
    listing.pack(fill="x")
    search_row = ttk.Frame(panel, style="Nexus.App.TFrame")
    search_row.pack(fill="x", pady=(5, 0))
    search_entry = ttk.Entry(search_row)
    search_entry.pack(side="left", fill="x", expand=True, padx=(0, 6))
    search_entry.insert(0, "Buscar nas aulas (2–120 caracteres)")
    reading = ttk.Frame(panel, style="Nexus.App.TFrame")
    reading.pack(fill="both", expand=True, pady=(7, 0))
    display = tk.Text(reading, height=10, wrap="word", state="disabled",
                      bg="#ffffff", fg="#382631", padx=10, pady=8)
    scrollbar = ttk.Scrollbar(reading, command=display.yview)
    display.configure(yscrollcommand=scrollbar.set)
    display.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    status = ttk.Label(
        panel, text="Selecione uma aula e clique em Ler aula. Não há sincronização ou servidor.",
        style="Nexus.Caption.TLabel",
    )
    status.pack(anchor="w", pady=(7, 0))
    controls = ttk.Frame(panel, style="Nexus.App.TFrame")
    controls.pack(fill="x", pady=(6, 0))
    completed: set[int] = set()
    recent_scores: list[tuple[int, int]] = []
    read_index = None
    lesson_text = ""
    session = None
    session_counted = False
    progress_events = Queue()
    progress_busy = False
    activity_events = Queue()
    search_busy = False
    speech_busy = False
    speech_paused = False
    speech_cancel = Event()
    speaker = None

    def show(text):
        display.configure(state="normal")
        display.delete("1.0", "end")
        display.insert("1.0", text)
        display.configure(state="disabled")

    def selected():
        indexes = listing.curselection()
        return indexes[0] if indexes else None

    def refresh():
        previous = selected()
        listing.delete(0, "end")
        for index, lesson in enumerate(course.lessons):
            marker = "✓" if index in completed else "□"
            listing.insert("end", f"{marker} {index + 1}. {lesson.title}")
        if previous is not None and previous < len(course.lessons):
            listing.selection_set(previous)
        status.configure(text=f"{len(completed)}/{len(course.lessons)} aulas marcadas "
                              "como concluídas nesta sessão.")

    def read_selected():
        nonlocal read_index, lesson_text, session, session_counted
        index = selected()
        if index is None:
            status.configure(text="Selecione uma aula.")
            return
        try:
            text = read_lesson(course, index)
        except CourseError as exc:
            status.configure(text=str(exc))
            return
        stop_speech()
        read_index = index
        lesson_text = text
        session = None
        session_counted = False
        show(f"{course.lessons[index].title}\n\n{text}")
        status.configure(text="Aula lida somente da pasta escolhida; nada foi salvo.")

    def mark_completed():
        index = selected()
        if index is None or index != read_index:
            status.configure(text="Leia a aula selecionada antes de concluí-la.")
            return
        completed.add(index)
        refresh()

    def next_lesson():
        nonlocal read_index, lesson_text, session
        index = selected()
        if index is None:
            return
        target = index + 1
        if target >= len(course.lessons):
            status.configure(text="Esta é a última aula do curso.")
            return
        stop_speech()
        listing.selection_clear(0, "end")
        listing.selection_set(target)
        listing.see(target)
        read_index = None
        lesson_text = ""
        session = None
        show("Próxima aula selecionada. Clique em Ler aula para abrir o material.")
        status.configure(text="Próxima aula pronta; nenhum arquivo aberto automaticamente.")

    def start_exercises():
        nonlocal session, session_counted
        if read_index is None or selected() != read_index:
            status.configure(text="Leia a aula selecionada antes de gerar exercícios.")
            return
        session = StudySession.from_text(lesson_text, limit=5)
        session_counted = False
        item = session.next_question()
        if item is None:
            status.configure(text="Esta aula não contém frases adequadas para lacunas.")
            return
        show(item.prompt)
        status.configure(text=f"{len(session.questions)} exercícios locais; respostas em memória.")

    def answer_exercise():
        nonlocal session_counted
        if session is None or session.completed:
            status.configure(text="Gere exercícios antes de responder.")
            return
        item = session.next_question()
        answer = simpledialog.askstring("Nexus Core — exercício local", item.prompt,
                                       parent=window)
        if answer is None:
            return
        try:
            attempt = session.submit(answer)
        except (ValueError, TypeError):
            status.configure(text="Resposta inválida ou acima do limite.")
            return
        right, done = session.score
        message = ("Resposta literal correta." if attempt.correct else
                   f"Resposta literal esperada: {item.expected_answer}")
        message += f"\nFonte: {item.source_excerpt}"
        next_item = session.next_question()
        if next_item:
            message += f"\n\nPróxima questão:\n{next_item.prompt}"
        else:
            message += f"\n\nSessão concluída: {right}/{done} acertos literais."
            if not session_counted:
                recent_scores.append((right, done))
                del recent_scores[:-10]
                session_counted = True
        show(message)
        status.configure(text=f"Exercícios respondidos: {done}/{len(session.questions)}.")

    def suggest_step():
        advice = recommend_study_step(recent_scores)
        show(f"Recomendação indicativa: {advice.level}\n"
             f"Taxa de acertos literais: {advice.accuracy_percent}% "
             f"({advice.questions} questões)\n\n{advice.action}\n\n"
             "Esta sugestão não altera automaticamente seu nível nem salva resultados.")
        status.configure(text="Sugestão calculada apenas com esta sessão local.")

    def run_progress(operation):
        nonlocal progress_busy
        if progress_busy:
            status.configure(text="Há outra operação de progresso em andamento.")
            return
        from tkinter import messagebox
        if operation == "save":
            if not messagebox.askyesno(
                "Nexus Core — progresso do curso",
                "Salvar apenas as aulas marcadas no PostgreSQL local? "
                "Nenhum conteúdo, caminho ou resposta será armazenado.",
                parent=window,
            ):
                return
        elif completed and not messagebox.askyesno(
            "Nexus Core — restaurar progresso",
            "Substituir as marcações atuais pelas que foram salvas anteriormente?",
            parent=window,
        ):
            return
        progress_busy = True
        snapshot = set(completed)
        status.configure(text="Acessando PostgreSQL local sob solicitação…")

        def worker():
            try:
                from nexus.study.offline_course_progress import PostgreSQLOfflineCourseProgress
                store = PostgreSQLOfflineCourseProgress(settings)
                result = (store.save(course, snapshot)
                          if operation == "save" else store.load(course))
                progress_events.put((operation, result, None))
            except Exception:
                progress_events.put((operation, None,
                                     "Progresso indisponível. Confira o PostgreSQL local."))

        Thread(target=worker, name="nexus-offline-course-progress", daemon=True).start()

    def poll_progress():
        nonlocal progress_busy
        if not window.winfo_exists():
            return
        try:
            operation, result, error = progress_events.get_nowait()
        except Empty:
            window.after(100, poll_progress)
            return
        progress_busy = False
        if error:
            status.configure(text=error)
        elif operation == "load":
            completed.clear()
            completed.update(result)
            refresh()
            status.configure(text=f"{len(completed)} aulas restauradas do PostgreSQL local.")
        else:
            status.configure(text=f"{result} aulas registradas no PostgreSQL local.")
        window.after(100, poll_progress)

    def search_lessons():
        nonlocal search_busy
        if search_busy:
            status.configure(text="A pesquisa local anterior ainda está em andamento.")
            return
        term = search_entry.get().strip()
        if not term or term == "Buscar nas aulas (2–120 caracteres)":
            term = simpledialog.askstring(
                "Nexus Core — pesquisa no curso",
                "Qual termo ou expressão deseja localizar nas aulas?",
                parent=window,
            )
        if term is None:
            return
        if not 2 <= len(term.strip()) <= 120 or "\n" in term or "\r" in term:
            status.configure(text="Digite de 2 a 120 caracteres em uma única linha.")
            return
        search_busy = True
        status.configure(text="Pesquisando somente as aulas autorizadas…")

        def worker():
            try:
                hits = search_course(course, term, limit=8)
                activity_events.put(("search", hits, None))
            except Exception:
                activity_events.put((
                    "search", None,
                    "Pesquisa indisponível; confira os arquivos da pasta escolhida.",
                ))

        Thread(target=worker, name="nexus-offline-course-search", daemon=True).start()

    def speak_lesson():
        nonlocal speech_busy, speech_paused, speaker, speech_cancel
        if speech_busy:
            status.configure(text="Já existe uma leitura de aula. Use Pausar ou Parar áudio.")
            return
        if read_index is None or selected() != read_index or not lesson_text:
            status.configure(text="Selecione e leia uma aula antes de iniciar a voz.")
            return
        from nexus.voice.local import LocalSpeaker
        if voice not in LocalSpeaker.VOICES:
            status.configure(text="Voz local inválida.")
            return
        # A lesson can be 64 KiB; narrate up to four sequential short segments.
        # Do not start multiple synthesizers or keep audio processes in parallel.
        from nexus.voice.text_segments import speech_segments
        segments = speech_segments(lesson_text, size=LocalSpeaker.MAX_SPEECH - 1, limit=4)
        if not segments:
            return
        speech_cancel = Event()
        speaker = LocalSpeaker()
        speech_busy = True
        speech_paused = False
        status.configure(
            text=f"Narrando {len(segments)} trechos, até 9.600 caracteres com voz local…"
        )
        options = {"cancelled": speech_cancel.is_set}
        if speed != 1.0 or volume != 100:
            options.update({"speed": speed, "volume": volume})

        def worker():
            try:
                for segment in segments:
                    if speech_cancel.is_set():
                        break
                    speaker.speak(segment, voice, **options)
                activity_events.put(("speech", None, None))
            except Exception:
                activity_events.put((
                    "speech", None,
                    "Leitura em voz indisponível; confira Piper/RHVoice/eSpeak.",
                ))

        Thread(target=worker, name="nexus-offline-course-speech", daemon=True).start()

    def toggle_speech_pause():
        nonlocal speech_paused
        if not speech_busy or speaker is None:
            status.configure(text="Nenhuma narração ativa para pausar.")
            return
        action = speaker.resume if speech_paused else speaker.pause
        try:
            changed = action()
        except Exception:
            changed = False
        if changed:
            speech_paused = not speech_paused
            status.configure(text="Narração pausada." if speech_paused
                             else "Narração retomada.")
        else:
            status.configure(text="Não foi possível alterar a pausa da voz.")

    def stop_speech():
        nonlocal speech_paused
        speech_paused = False
        speech_cancel.set()
        if speaker is not None:
            speaker.stop()

    def poll_activity():
        nonlocal speech_busy, speech_paused, search_busy
        if not window.winfo_exists():
            return
        try:
            kind, result, error = activity_events.get_nowait()
        except Empty:
            window.after(100, poll_activity)
            return
        if kind == "search":
            search_busy = False
            if error:
                status.configure(text=error)
            elif not result:
                show("Nenhum trecho corresponde à pesquisa neste curso.")
                status.configure(text="Nenhuma correspondência literal encontrada.")
            else:
                show("\n\n".join(
                    f"Aula {match.lesson_index + 1}: {match.lesson_title}\n"
                    f"{match.excerpt}" for match in result
                ))
                status.configure(
                    text=f"{len(result)} trechos encontrados nas aulas autorizadas."
                )
        elif kind == "speech":
            speech_busy = False
            speech_paused = False
            status.configure(text=error or "Narração concluída ou interrompida.")
        window.after(100, poll_activity)

    def close_course():
        stop_speech()
        window.destroy()

    # Single search control, reusing the existing row instead of adding
    # a fourth row of buttons at the minimum 600x450 window size.
    ttk.Button(
        search_row, text="Pesquisar no curso", command=search_lessons,
        style="Nexus.TButton",
    ).pack(side="right")

    buttons = (
        ("Ler aula", read_selected), ("Concluir aula", mark_completed),
        ("Próxima aula", next_lesson), ("Gerar exercícios", start_exercises),
        ("Responder exercício", answer_exercise), ("Sugerir próximo passo", suggest_step),
        ("Salvar progresso", lambda: run_progress("save")),
        ("Carregar progresso", lambda: run_progress("load")),
        ("Ouvir aula", speak_lesson),
        ("Pausar/retomar áudio", toggle_speech_pause),
        ("Parar áudio", stop_speech),
    )
    for column in range(3):
        controls.columnconfigure(column, weight=1)
    for index, (label, callback) in enumerate(buttons):
        ttk.Button(controls, text=label, command=callback,
                   style="Nexus.TButton").grid(
                       row=index // 3, column=index % 3,
                       sticky="ew", padx=3, pady=2,
                   )
    refresh()
    if course.lessons:
        listing.selection_set(0)
    window.protocol("WM_DELETE_WINDOW", close_course)
    window.after(100, poll_progress)
    window.after(100, poll_activity)
    return window
