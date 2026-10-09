"""Janela de conversa nativa para o desktop Linux."""

import sys
import re
import unicodedata
from queue import Empty, Queue
from threading import Thread

from nexus.agent import AgentOutcome
from nexus.config.settings import PROJECT_ROOT, settings
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.conversation import ChatReply, ChatSession
from nexus.voice import LocalRecognizer, LocalSpeaker, VoiceError
from nexus.voice.wake import extract_utterance
from nexus.vision import LocalVision, VisionError, VisionInputError


class _WidgetBoolean:
    """Expose the selected widget state without allocating a Tk Variable."""

    def __init__(self, widget):
        self.widget = widget

    def get(self) -> bool:
        return bool(self.widget.instate(("selected",)))

    def set(self, value: bool) -> None:
        self.widget.state(("selected",) if value else ("!selected",))


class _WidgetChoice:
    """Small adapter matching get/set while keeping the value in the widget."""

    def __init__(self, widget):
        self.widget = widget

    def get(self) -> str:
        return self.widget.get()

    def set(self, value: str) -> None:
        self.widget.set(value)


class DesktopWindow:
    def __init__(
        self, root, app, confirmation: DesktopConfirmation,
        speaker=None, recognizer=None, vision=None,
    ):
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.root = root
        self.app = app
        self.confirmation = confirmation
        self.session = ChatSession(app.agent)
        self.tk = tk
        self.messagebox = messagebox
        self.speaker = speaker if speaker is not None else LocalSpeaker()
        self.recognizer = recognizer if recognizer is not None else LocalRecognizer()
        self._replies: Queue[ChatReply] = Queue()
        self._audio_events: Queue[tuple[str, str, int]] = Queue()
        self._vision_events: Queue[tuple[str, str, str]] = Queue()
        self.vision = vision
        self._vision_buttons = []
        self._busy = False
        self._operation_kind = None
        self._cancel_requested = False
        self._listening = False
        self._voice_active = True
        self._listen_generation = 0
        self._listen_pending_generations: set[int] = set()
        self._speak_generation = 0
        self._speaking = False
        self._closing = False
        self._workers: list[Thread] = []

        root.title(f"Nexus Core {settings.version} — Conversa local")
        root.geometry("820x620")
        root.minsize(560, 420)
        root.configure(bg="#f7f4f5")
        style = ttk.Style(root)
        style.configure("Nexus.TButton", padding=(14, 9))

        frame = ttk.Frame(root, padding=18)
        frame.pack(fill="both", expand=True)
        # Keep visual assets local. Tk can display the bundled transparent PNG
        # without requiring a browser, SVG runtime or third-party GUI package.
        self._brand_image = None
        brand = PROJECT_ROOT / "assets" / "brand" / "nexus-core-logo.png"
        if brand.is_file():
            try:
                self._brand_image = tk.PhotoImage(file=str(brand)).subsample(12, 12)
            except tk.TclError:
                self._brand_image = None
        if self._brand_image is not None:
            ttk.Label(frame, image=self._brand_image).pack(anchor="w")
        else:
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

        voice_controls = ttk.Frame(frame)
        voice_controls.pack(fill="x", pady=(10, 0))
        self.speech_toggle = ttk.Checkbutton(
            voice_controls, text="Ler respostas em voz alta",
            command=self._toggle_speech,
        )
        self.speech_toggle.state(("selected",))
        self.speech_toggle.pack(side="left")
        self.speech_enabled = _WidgetBoolean(self.speech_toggle)
        ttk.Label(voice_controls, text="Voz:").pack(side="left", padx=(14, 4))
        self.voice_selector = ttk.Combobox(
            voice_controls,
            values=("Feminina", "Masculina"), state="readonly", width=12,
        )
        self.voice_selector.set("Feminina")
        self.voice_selector.pack(side="left")
        self.voice_choice = _WidgetChoice(self.voice_selector)
        # Optional activation never changes default continuous listening.
        self.wake_toggle = ttk.Checkbutton(
            voice_controls, text='Exigir "Nexus" para ativar',
            command=self._toggle_wake,
        )
        self.wake_toggle.pack(side="left", padx=(12, 0))
        self.wake_required = _WidgetBoolean(self.wake_toggle)
        vision_controls = ttk.Frame(frame)
        vision_controls.pack(fill="x", pady=(8, 0))
        ttk.Label(vision_controls, text="Visão local sob autorização:").pack(side="left", padx=(0, 8))
        for title, callback in (
            ("Imagem", self._vision_file),
            ("Tela", self._vision_screen),
            ("Câmera", self._vision_camera),
        ):
            button = ttk.Button(
                vision_controls, text=title, command=callback, style="Nexus.TButton",
            )
            button.pack(side="left", padx=(0, 6))
            self._vision_buttons.append(button)

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
        self.mic_button = ttk.Button(
            controls, text="Pausar escuta", command=self._toggle_listening,
            style="Nexus.TButton",
        )
        self.mic_button.pack(side="right", padx=(8, 0))
        ttk.Button(
            controls, text="Desligar assistente", command=self._close,
            style="Nexus.TButton",
        ).pack(side="right", padx=(8, 0))
        self.send_button = ttk.Button(
            controls, text="Enviar", command=self._send, style="Nexus.TButton"
        )
        self.send_button.pack(side="right")
        self.suggest_button = ttk.Button(
            controls, text="Sugerir", command=self._suggest, style="Nexus.TButton",
        )
        self.suggest_button.pack(side="right", padx=(0, 6))
        self.cancel_button = ttk.Button(
            controls, text="Cancelar", command=self._cancel_current,
            style="Nexus.TButton", state="disabled",
        )
        self.cancel_button.pack(side="right", padx=(0, 6))
        root.protocol("WM_DELETE_WINDOW", self._close)
        self._append(
            "Nexus Core",
            "Posso responder perguntas e propor ações com as ferramentas disponíveis. "
            "A escuta começa automaticamente. Diga 'pare de escutar' ou use "
            "Pausar escuta; use o botão para retomá-la. "
            "Comandos no sandbox pedem sua autorização antes de executar.",
            "assistant",
        )
        self.input.focus_set()
        root.after(80, self._poll)
        root.after(120, self._start_listening)

    def _append(self, speaker: str, message: str, tag: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{speaker}\n", tag)
        self.transcript.insert("end", f"{message}\n\n")
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _start_worker(self, target, *args) -> None:
        """Retain worker references until they exit, including during shutdown."""
        worker = Thread(target=target, args=args, daemon=True)
        self._workers.append(worker)
        worker.start()

    def _workers_running(self) -> bool:
        self._workers = [worker for worker in self._workers if worker.is_alive()]
        return bool(self._workers)

    def _finish_close(self) -> None:
        """Destroy Tk resources only on the GUI thread, after all workers exit."""
        self.speech_enabled = None
        self.voice_choice = None
        self.wake_required = None
        self._brand_image = None
        self._workers.clear()
        self._vision_buttons.clear()
        self.vision = None
        self.app.shutdown()
        self.root.destroy()

    def _suggest(self):
        if self._busy or self._closing:
            return
        self.input.delete("1.0", "end")
        self.input.insert(
            "1.0", "Considerando a conversa, sugira próximos passos práticos "
                   "que eu possa escolher. Apenas aconselhe, sem executar ações.",
        )
        self._send(advisory_only=True)

    def _cancel_current(self):
        """Cancel pending answer presentation and block future tool execution.

        It cannot undo an already executed action or interrupt every Ollama call.
        """
        if not self._busy or self._closing:
            return
        self._cancel_requested = True
        if self._operation_kind == "chat":
            self.session.cancel_current()
            # Release threads blocked on tool consent immediately.
            self.confirmation.cancel_pending()
        self.cancel_button.configure(state="disabled")
        self.status.configure(text="Cancelamento solicitado; finalizando operação…")

    def _finish_operation(self):
        self._busy = False
        self._cancel_requested = False
        self._operation_kind = None
        self.send_button.configure(state="normal")
        self.suggest_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        for button in self._vision_buttons:
            button.configure(state="normal")

    def _say_response(self, text: str) -> bool:
        """Speak normal and visual answers through the same local TTS channel."""
        if not self.speech_enabled.get() or not text.strip():
            return False
        self._speak_generation += 1
        generation = self._speak_generation
        self._speaking = True
        self._start_worker(self._speak, text, self.voice_choice.get(), generation)
        return True

    def _send(self, event=None, *, advisory_only=False):
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
        self.session.prepare_turn()
        self._busy = True
        self._operation_kind = "chat"
        self._cancel_requested = False
        self.send_button.configure(state="disabled")
        self.suggest_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        for button in self._vision_buttons:
            button.configure(state="disabled")
        if self._listening:
            self._listen_generation += 1
            self.recognizer.stop()
        if self._speaking:
            self._stop_speaking()
        self.status.configure(text="Processando localmente…")
        self._start_worker(self._answer, message, advisory_only)
        return "break"

    def _answer(self, message: str, advisory_only: bool = False) -> None:
        try:
            reply = self.session.ask(message, advisory_only=advisory_only)
        except Exception:
            reply = ChatReply(
                "Não foi possível processar a solicitação.",
                AgentOutcome(False, error_code="SESSION_ERROR"),
            )
        self._replies.put(reply)

    def _start_listening(self) -> None:
        if (not self._voice_active or self._busy or self._listening
                or self._listen_pending_generations or self._speaking or self._closing):
            return
        self._listening = True
        self._listen_generation += 1
        generation = self._listen_generation
        self._listen_pending_generations.add(generation)
        self.status.configure(text="Ouvindo… diga sua pergunta")
        self._start_worker(self._listen, generation)

    def _toggle_listening(self) -> None:
        if self._closing:
            return
        self._voice_active = not self._voice_active
        self.mic_button.configure(
            text="Pausar escuta" if self._voice_active else "Retomar escuta"
        )
        if self._voice_active:
            self._start_listening()
        else:
            self._listen_generation += 1
            self.recognizer.stop()
            self.status.configure(text="Escuta pausada; use Retomar escuta")

    @staticmethod
    def _voice_command(text: str) -> str | None:
        normalized = " ".join(unicodedata.normalize("NFKD", text).encode(
            "ascii", "ignore"
        ).decode("ascii").lower().split())
        normalized = re.sub(r"^nexus[,:]?\s+", "", normalized).rstrip(".!?")
        if normalized in {"pare de escutar", "pare de me escutar", "pause a escuta",
                          "pausar escuta", "desative o microfone", "desligue o microfone",
                          "fique em silencio", "pare de ouvir", "pare de me ouvir"}:
            return "pause"
        if normalized in {"desligue o assistente", "feche o nexus core"}:
            return "shutdown"
        return None

    def _toggle_wake(self) -> None:
        if self._closing:
            return
        if self.wake_required.get():
            self.status.configure(text='Diga "Nexus, ..." antes de cada pergunta')
        else:
            self.status.configure(text="Conversa contínua sem palavra de ativação")

    def _stop_speaking(self) -> None:
        """Invalidate a superseded TTS worker before its completion event."""
        self._speak_generation += 1
        self._speaking = False
        self.speaker.stop()

    def _toggle_speech(self) -> None:
        if not self.speech_enabled.get() and self._speaking:
            self._stop_speaking()
            self.status.configure(text="Leitura em voz desativada")
            self._start_listening()

    def _vision_file(self) -> None:
        self._request_vision("file")

    def _vision_screen(self) -> None:
        self._request_vision("screen")

    def _vision_camera(self) -> None:
        self._request_vision("camera")

    def _request_vision(self, source: str) -> None:
        """Capture once only following user action and explicit per-shot consent."""
        if self._closing or self._busy or source not in ("file", "screen", "camera"):
            return
        from tkinter import filedialog, simpledialog

        selection = None
        label = {"file": "imagem selecionada", "screen": "tela atual",
                 "camera": "câmera"}[source]
        if source == "file":
            selection = filedialog.askopenfilename(
                parent=self.root, title="Escolher imagem local para análise",
                filetypes=[("Imagens", "*.png *.jpg *.jpeg *.webp")],
            )
            if not selection:
                return
        elif source == "camera":
            selection = simpledialog.askinteger(
                "Selecionar câmera", "Índice da câmera (0 a 9):",
                parent=self.root, initialvalue=0, minvalue=0, maxvalue=9,
            )
            if selection is None:
                return
            label = f"câmera {selection}"
        question = simpledialog.askstring(
            "Pergunta sobre a imagem", "Qual pergunta deseja fazer ao modelo visual?",
            parent=self.root, initialvalue=LocalVision.DEFAULT_PROMPT,
        )
        if question is None:
            return
        try:
            question = LocalVision.validate_question(question)
        except VisionInputError:
            self.status.configure(text="Pergunta visual inválida (máximo 2000 caracteres)")
            return
        if self._closing or self._busy:
            return
        consent = self.messagebox.askyesno(
            "Nexus Core — autorização visual",
            f"Autorizar UMA captura/leitura de {label} e enviar esta imagem "
            "somente ao Ollama local para responder sua pergunta?\n\n"
            "A imagem pode conter dados privados. Nenhum acesso contínuo "
            "será iniciado. Esta autorização vale apenas para esta análise.",
            parent=self.root,
        )
        if not consent or self._closing or self._busy:
            return
        self._busy = True
        self._operation_kind = "vision"
        self._cancel_requested = False
        self.send_button.configure(state="disabled")
        self.suggest_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        for button in self._vision_buttons:
            button.configure(state="disabled")
        if self._listening:
            self._listen_generation += 1
            self.recognizer.stop()
        if self._speaking:
            self._stop_speaking()
        self.status.configure(text="Analisando imagem no Ollama local…")
        self._append("Você", f"[Visão autorizada: {label}] {question}", "user")
        self._start_worker(self._analyze_vision, source, selection, question)

    def _analyze_vision(self, source: str, selection, question: str) -> None:
        """Worker only: never touch Tk from this thread or persist image bytes."""
        try:
            service = self.vision if self.vision is not None else LocalVision(settings)
            if source == "file":
                image = service.image_from_file(selection)
            elif source == "camera":
                image = service.camera(selection)
            else:
                image = service.screen()
            result = service.describe(image, question=question)
            if not isinstance(result, dict) or not isinstance(
                result.get("description"), str
            ) or not result["description"].strip():
                raise VisionError("Resposta visual local inválida.")
            self._vision_events.put(("success", question, result["description"][:12000]))
        except VisionError as exc:
            self._vision_events.put(("error", question, str(exc)))
        except Exception:
            self._vision_events.put(
                ("error", question, "Falha ao capturar ou analisar imagem local.")
            )

    def _listen(self, generation: int) -> None:
        try:
            text = self.recognizer.recognize_continuous(
                lambda: self._closing or self._busy or not self._voice_active
                or generation != self._listen_generation
            )
            self._audio_events.put(("transcript" if text else "silence", text, generation))
        except VoiceError as exc:
            self._audio_events.put(("listen_error", str(exc), generation))
        except Exception:
            self._audio_events.put(("listen_error", "Falha ao reconhecer a fala local.", generation))

    def _speak(self, text: str, voice: str, generation: int) -> None:
        # A queued speech worker may start after the user has cancelled
        # or muted it. Do not start playback from such a stale request.
        if self._closing or generation != self._speak_generation:
            return
        try:
            self.speaker.speak(text, voice)
            self._audio_events.put(("speak_done", "", generation))
        except VoiceError as exc:
            self._audio_events.put(("speak_error", str(exc), generation))
        except Exception:
            self._audio_events.put((
                "speak_error", "Falha ao reproduzir a voz local.", generation
            ))

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
        # Prune completed workers on every GUI tick; otherwise a long-running
        # voice conversation would retain every prior thread indefinitely.
        self._workers_running()
        self.confirmation.process(self._confirm)
        while True:
            try:
                kind, value, generation = self._audio_events.get_nowait()
            except Empty:
                break
            if kind in ("transcript", "silence", "listen_error"):
                if generation not in self._listen_pending_generations:
                    continue
                self._listen_pending_generations.discard(generation)
                self._listening = False
                if self._closing:
                    continue
                if generation != self._listen_generation:
                    self._start_listening()
                    continue
                if kind == "listen_error":
                    self._voice_active = False
                    self.mic_button.configure(text="Retomar escuta")
                    self.status.configure(text=value)
                elif self._voice_active and not self._busy:
                    utterance = (
                        extract_utterance(value, require_wake=self.wake_required.get())
                        if kind == "transcript" else None
                    )
                    command = self._voice_command(utterance) if utterance else None
                    if command == "pause":
                        self._toggle_listening()
                        self._append("Você", value, "user")
                        self._append("Nexus Core", "Escuta pausada. Retome pelo botão.", "assistant")
                    elif command == "shutdown":
                        self._close()
                    elif kind == "transcript" and utterance:
                        self.input.delete("1.0", "end")
                        self.input.insert("1.0", utterance)
                        self._send()
                    else:
                        self._start_listening()
            elif kind in ("speak_done", "speak_error"):
                # A cancelled/disabled older voice must not clobber new TTS.
                if generation != self._speak_generation:
                    continue
                self._speaking = False
                if not self._closing and not self._busy:
                    if kind == "speak_error" and self.speech_enabled.get():
                        self.status.configure(text=value)
                    self._start_listening()
        while True:
            try:
                reply = self._replies.get_nowait()
            except Empty:
                break
            cancelled = self._cancel_requested
            if not self._closing:
                self._finish_operation()
                if cancelled or reply.outcome.error_code == "CANCELLED":
                    self._append("Nexus Core", "Solicitação cancelada.", "assistant")
                    self.status.configure(text="Solicitação cancelada")
                    self._start_listening()
                else:
                    self._append("Nexus Core", reply.text, "assistant")
                    self.status.configure(
                        text="Escuta pausada" if not self._voice_active
                        else "Pronto para conversar"
                    )
                    if not (reply.outcome.success and self._say_response(reply.text)):
                        self._start_listening()
            else:
                self._busy = False
        while True:
            try:
                kind, question, result = self._vision_events.get_nowait()
            except Empty:
                break
            cancelled = self._cancel_requested
            if self._closing:
                self._busy = False
                continue
            self._finish_operation()
            if cancelled:
                self._append("Nexus Core", "Análise visual cancelada.", "assistant")
                self.status.configure(text="Análise visual cancelada")
                self._start_listening()
            elif kind == "success":
                self.session.note_visual(question, result)
                self._append("Nexus Core", result, "assistant")
                self.status.configure(text="Análise visual concluída")
                # File, screen and camera all use the same voice output path.
                if not self._say_response(result):
                    self._start_listening()
            else:
                self._append("Nexus Core", f"Análise visual indisponível: {result}", "assistant")
                self.status.configure(text="Falha na análise visual")
                self._start_listening()
        if (self._closing and not self._busy and not self._listening
                and not self._speaking and not self._workers_running()):
            self._finish_close()
            return
        self.root.after(80, self._poll)

    def _close(self) -> None:
        if self._closing:
            return
        self._closing = True
        # The original photo asset must be released on the Tk thread even
        # when tests or users destroy the root before audio workers exit.
        self._brand_image = None
        self._voice_active = False
        self._listen_generation += 1
        self.session.close()
        self.confirmation.close()
        self.recognizer.stop()
        self._stop_speaking()
        self.send_button.configure(state="disabled")
        self.suggest_button.configure(state="disabled")
        self.cancel_button.configure(state="disabled")
        self.mic_button.configure(state="disabled")
        for button in self._vision_buttons:
            button.configure(state="disabled")
        if self._busy or self._listening or self._speaking or self._workers_running():
            self.status.configure(text="Encerrando após a solicitação atual…")
        else:
            self._finish_close()


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
