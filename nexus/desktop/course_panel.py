"""Leitor nativo de cursos TXT/Markdown locais, sem servidor ou novas dependências.

O progresso e as respostas vivem só na memória desta janela. Não há leitura
automática de materiais antes do clique nem criação de arquivos ou banco.
"""
from __future__ import annotations

from nexus.study.offline_course import OfflineCourse, CourseError, read_lesson
from nexus.study.recommendations import recommend_study_step
from nexus.study_session import StudySession


def open_course(root, course: OfflineCourse):
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

    def show(text):
        display.configure(state="normal")
        display.delete("1.0", "end")
        display.insert("1.0", text)
        display.configure(state="disabled")

    def selected():
        indexes = listing.curselection()
        return indexes[0] if indexes else None

    def refresh():
        listing.delete(0, "end")
        for index, lesson in enumerate(course.lessons):
            marker = "✓" if index in completed else "□"
            listing.insert("end", f"{marker} {index + 1}. {lesson.title}")
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

    buttons = (
        ("Ler aula", read_selected), ("Concluir aula", mark_completed),
        ("Próxima aula", next_lesson), ("Gerar exercícios", start_exercises),
        ("Responder exercício", answer_exercise), ("Sugerir próximo passo", suggest_step),
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
    return window
