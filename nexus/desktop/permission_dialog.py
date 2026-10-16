"""One-shot desktop consent by button, typed command or local voice."""

import unicodedata
from queue import Empty, Queue
from threading import Event

from nexus.voice import VoiceError


def permission_answer(text: str, *, spoken: bool = False) -> bool | None:
    """Accept only exact, unambiguous phrases; everything else is no decision."""
    if not isinstance(text, str) or len(text) > 80:
        return None
    normalized = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    normalized = " ".join(normalized.casefold().strip().rstrip(".!?")
                          .replace(",", " ").replace(":", " ").split())
    if spoken:
        if normalized == "nexus autorizo esta acao":
            return True
        if normalized in ("nexus nego esta acao", "nexus nao autorizo esta acao"):
            return False
    else:
        if normalized == "autorizar":
            return True
        if normalized in ("negar", "cancelar"):
            return False
    return None


class PermissionDialog:
    """GUI-thread modal. Its worker transcribes only; the model cannot consent."""

    def __init__(self, root, details: str, *, recognizer, listen: bool,
                 ready_to_listen, start_worker, cancelled):
        from tkinter import ttk
        import tkinter as tk

        self.root = root
        self.recognizer = recognizer
        self.listen = listen
        self.ready_to_listen = ready_to_listen
        self.start_worker = start_worker
        self.cancelled = cancelled
        self.result = False
        self._closed = Event()
        self._voice_worker = False
        self._voice_results: Queue[tuple[str, str]] = Queue()
        self._tick_id = None
        self._timeout_id = None

        self.window = tk.Toplevel(root)
        self.window.title("Nexus Core — autorização necessária")
        self.window.transient(root)
        self.window.geometry("640x450")
        self.window.minsize(500, 370)
        self.window.configure(bg="#f5f1f3")
        self.window.protocol("WM_DELETE_WINDOW", lambda: self._finish(False))
        frame = ttk.Frame(self.window, style="Nexus.App.TFrame", padding=16)
        frame.pack(fill="both", expand=True)
        ttk.Label(frame, text="Autorizar uma ação", style="Nexus.Section.TLabel").pack(anchor="w")
        description = tk.Text(frame, height=9, wrap="word", bg="#ffffff", fg="#292127",
                              relief="flat", padx=10, pady=10)
        description.insert("1.0", details)
        description.configure(state="disabled")
        description.pack(fill="both", expand=True, pady=(10, 12))
        ttk.Label(frame, text="Digite AUTORIZAR ou NEGAR e pressione Enter:",
                  style="Nexus.Caption.TLabel").pack(anchor="w")
        self.entry = ttk.Entry(frame)
        self.entry.pack(fill="x", pady=(4, 10))
        self.entry.bind("<Return>", self._typed_answer)
        voice_note = ("Voz: diga ‘Nexus, autorizo esta ação’ ou "
                      "‘Nexus, nego esta ação’." if listen else
                      "Escuta pausada: use texto ou botões para decidir.")
        self.status = ttk.Label(frame, text=voice_note, style="Nexus.Caption.TLabel",
                                wraplength=580)
        self.status.pack(anchor="w", fill="x", pady=(0, 12))
        buttons = ttk.Frame(frame, style="Nexus.App.TFrame")
        buttons.pack(fill="x")
        ttk.Button(buttons, text="Negar", command=lambda: self._finish(False),
                   style="Nexus.TButton").pack(side="right", padx=(8, 0))
        ttk.Button(buttons, text="Autorizar esta ação", command=lambda: self._finish(True),
                   style="Nexus.Primary.TButton").pack(side="right")
        self.window.bind("<Escape>", lambda event: self._finish(False))

    def _typed_answer(self, event=None):
        answer = permission_answer(self.entry.get())
        if answer is None:
            self.status.configure(text="Digite somente AUTORIZAR ou NEGAR.")
            return "break"
        self._finish(answer)
        return "break"

    def _listen_once(self):
        try:
            text = self.recognizer.recognize_continuous(
                lambda: self._closed.is_set() or self.cancelled()
            )
            self._voice_results.put(("heard", text))
        except VoiceError as exc:
            self._voice_results.put(("error", str(exc)))
        except Exception:
            self._voice_results.put(("error", "Microfone indisponível nesta autorização."))

    def _tick(self):
        if self._closed.is_set():
            return
        if self.cancelled():
            self._finish(False)
            return
        while True:
            try:
                kind, value = self._voice_results.get_nowait()
            except Empty:
                break
            self._voice_worker = False
            if kind == "error":
                self.listen = False
                self.status.configure(text=f"{value} Use texto ou botões.")
            elif value:
                answer = permission_answer(value, spoken=True)
                if answer is not None:
                    self._finish(answer)
                    return
                self.status.configure(text="Frase de voz não reconhecida. Use a frase exata ou digite a decisão.")
        if self.listen and not self._voice_worker and self.ready_to_listen():
            self._voice_worker = True
            self.start_worker(self._listen_once)
        self._tick_id = self.window.after(100, self._tick)

    def _finish(self, approved: bool):
        if self._closed.is_set():
            return
        self.result = approved and not self.cancelled()
        self._closed.set()
        for scheduled in (self._tick_id, self._timeout_id):
            if scheduled is not None:
                self.window.after_cancel(scheduled)
        if self._voice_worker:
            self.recognizer.stop()
        self.window.destroy()

    def ask(self) -> bool:
        self.window.wait_visibility()
        self.window.grab_set()
        self.entry.focus_set()
        self._tick_id = self.window.after(100, self._tick)
        # The bridge waits at most 300 seconds; expire the dialog earlier.
        self._timeout_id = self.window.after(290000, lambda: self._finish(False))
        self.root.wait_window(self.window)
        return self.result and not self.cancelled()
