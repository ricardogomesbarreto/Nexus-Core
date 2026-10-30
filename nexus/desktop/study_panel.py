"""Prática nativa de cartões locais. Sem download, servidor ou modelo extra."""

from queue import Empty, Queue
from threading import Thread

from nexus.config.settings import settings
from nexus.study.store import PostgreSQLStudyCards, StudyError


def open_study(root, source_hit=None):
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
        nonlocal exercise_session
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

    buttons = (("Criar cartão", create), ("Atualizar revisões", lambda: run("refresh")),
               ("Mostrar resposta", reveal), ("Acertei", lambda: grade(True)),
               ("Repetir", lambda: grade(False)), ("Excluir cartão", remove),
               ("Gerar exercícios do trecho", generate_exercises),
               ("Responder exercício", answer_exercise))
    for column in range(3):
        controls.columnconfigure(column, weight=1)
    for index, (label, action) in enumerate(buttons):
        ttk.Button(controls, text=label, command=action,
                   style="Nexus.TButton").grid(row=index // 3, column=index % 3,
                                               sticky="ew", padx=3, pady=2)
    due_list.bind("<<ListboxSelect>>", select)

    def poll():
        nonlocal busy, cards, current, revealed
        if not window.winfo_exists():
            return
        try:
            operation, result, due, error = messages.get_nowait()
        except Empty:
            window.after(80, poll)
            return
        busy = False
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

    run("refresh")
    window.after(80, poll)
    return window
