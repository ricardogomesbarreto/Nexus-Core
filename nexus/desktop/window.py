"""Janela de conversa nativa para o desktop Linux."""

import sys
from queue import Empty, Queue
from threading import Thread

from nexus.agent import AgentOutcome
from nexus.config.settings import settings
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.conversation import ChatReply, ChatSession


class DesktopWindow:
    def __init__(self, root, app, confirmation: DesktopConfirmation):
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.root = root
        self.app = app
        self.confirmation = confirmation
        self.session = ChatSession(app.agent)
        self.tk = tk
        self.messagebox = messagebox
        self._replies: Queue[ChatReply] = Queue()
        self._busy = False
        self._closing = False

        root.title(f"Nexus Core {settings.version} — Conversa local")
        root.geometry("820x620")
        root.minsize(560, 420)
        root.configure(bg="#f7f4f5")
        style = ttk.Style(root)
        style.configure("Nexus.TButton", padding=(14, 9))

        frame = ttk.Frame(root, padding=18)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Nexus Core", font=("Sans", 20, "bold")).pack(anchor="w")
        ttk.Label(
            frame,
            text="Conversa local · ações mediadas · PostgreSQL no computador",
        ).pack(anchor="w", pady=(0, 12))

        transcript_frame = ttk.Frame(frame)
        transcript_frame.pack(fill="both", expand=True)
        self.transcript = tk.Text(
            transcript_frame, wrap="word", state="disabled", padx=14, pady=12,
            bg="#ffffff", fg="#252025", font=("Sans", 11), relief="flat",
        )
        scrollbar = ttk.Scrollbar(transcript_frame, command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        self.transcript.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.transcript.tag_configure("user", foreground="#722F37", font=("Sans", 11, "bold"))
        self.transcript.tag_configure("assistant", foreground="#242424", font=("Sans", 11, "bold"))

        ttk.Label(frame, text="Sua mensagem (Ctrl+Enter para enviar)").pack(
            anchor="w", pady=(12, 4)
        )
        self.input = tk.Text(frame, height=3, wrap="word", font=("Sans", 11))
        self.input.pack(fill="x")
        self.input.bind("<Control-Return>", self._send)
        controls = ttk.Frame(frame)
        controls.pack(fill="x", pady=(8, 0))
        self.status = ttk.Label(controls, text="Pronto para conversar")
        self.status.pack(side="left")
        self.send_button = ttk.Button(
            controls, text="Enviar", command=self._send, style="Nexus.TButton"
        )
        self.send_button.pack(side="right")
        root.protocol("WM_DELETE_WINDOW", self._close)
        self._append(
            "Nexus Core",
            "Posso responder perguntas e propor ações com as ferramentas disponíveis. "
            "Comandos no sandbox pedem sua autorização antes de executar.",
            "assistant",
        )
        self.input.focus_set()
        root.after(80, self._poll)

    def _append(self, speaker: str, message: str, tag: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{speaker}\n", tag)
        self.transcript.insert("end", f"{message}\n\n")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _send(self, event=None):
        if self._busy or self._closing:
            return "break"
        message = self.input.get("1.0", "end-1c").strip()
        if not message:
            return "break"
        if len(message) > ChatSession.MAX_MESSAGE:
            self.status.configure(text="Mensagem excede 4000 caracteres")
            return "break"
        self.input.delete("1.0", "end")
        self._append("Você", message, "user")
        self._busy = True
        self.send_button.configure(state="disabled")
        self.status.configure(text="Processando localmente…")
        Thread(target=self._answer, args=(message,), daemon=True).start()
        return "break"

    def _answer(self, message: str) -> None:
        try:
            reply = self.session.ask(message)
        except Exception:
            reply = ChatReply(
                "Não foi possível processar a solicitação.",
                AgentOutcome(False, error_code="SESSION_ERROR"),
            )
        self._replies.put(reply)

    @staticmethod
    def _display(value) -> str:
        return "".join(
            char if char.isprintable() else f"\\u{ord(char):04x}"
            for char in str(value)
        )

    def _confirm(self, request) -> bool:
        details = [
            f"Ferramenta: {self._display(request.tool_name or 'unknown')}",
            f"Ação: {self._display(request.description)}",
            f"Risco: {request.risk_level.name}",
        ]
        if isinstance(request.data, dict) and "command" in request.data:
            details.append(f"Comando: {self._display(request.data['command'])}")
        for resource in request.resources:
            details.append(
                f"Recurso {self._display(resource.name)}: {self._display(resource.path)}"
            )
        details.append("\nAutorizar somente esta execução?")
        return self.messagebox.askyesno(
            "Nexus Core — autorização necessária", "\n".join(details), parent=self.root
        )

    def _poll(self) -> None:
        self.confirmation.process(self._confirm)
        while True:
            try:
                reply = self._replies.get_nowait()
            except Empty:
                break
            self._busy = False
            if not self._closing:
                self._append("Nexus Core", reply.text, "assistant")
                self.send_button.configure(state="normal")
                self.status.configure(text="Pronto para conversar")
        if self._closing and not self._busy:
            self.app.shutdown()
            self.root.destroy()
            return
        self.root.after(80, self._poll)

    def _close(self) -> None:
        self._closing = True
        self.session.close()
        self.confirmation.close()
        self.send_button.configure(state="disabled")
        if self._busy:
            self.status.configure(text="Encerrando após a solicitação atual…")
        else:
            self.app.shutdown()
            self.root.destroy()


def launch_desktop() -> int:
    try:
        import tkinter as tk
    except ImportError:
        print("Interface Tk indisponível. Instale o suporte Tk do Python.", file=sys.stderr)
        return 2

    try:
        root = tk.Tk()
    except tk.TclError:
        print("Não foi possível abrir a janela. Verifique a sessão gráfica Linux.", file=sys.stderr)
        return 2

    from nexus.main import build_application

    confirmation = DesktopConfirmation()
    app = None
    try:
        app = build_application(confirmation_handler=confirmation)
        app.initialize()
        DesktopWindow(root, app, confirmation)
        root.mainloop()
    except Exception as exc:
        print(
            f"Não foi possível iniciar o Nexus Core ({type(exc).__name__}). "
            "Verifique os serviços locais e os logs.", file=sys.stderr,
        )
        return 1
    finally:
        confirmation.close()
        if app is not None:
            app.shutdown()
        try:
            root.destroy()
        except tk.TclError:
            pass
    return 0
