"""Janela de conversa nativa para o desktop Linux."""

import sys
import gc
import io
import os
import re
import unicodedata
from difflib import SequenceMatcher
from pathlib import Path
from queue import Empty, Queue
from threading import Thread
from time import monotonic

from nexus.agent import AgentOutcome
from nexus.agent.planner import _simple_app_request
from nexus.config.settings import settings
from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.permission_dialog import PermissionDialog
from nexus.desktop.conversation import ChatReply, ChatSession
from nexus.desktop.preferences import (
    DesktopPreferences, DesktopPreferenceStore, PreferenceStoreError,
)
from nexus.desktop.chat_archive import ChatArchive, ChatArchiveError
from nexus.desktop.connectivity_indicator import PassiveConnectivityWatcher
from nexus.desktop.multimodal_status import MultimodalStatus
from nexus.desktop.welcome import desktop_spoken_welcome, desktop_startup_message
from nexus.desktop.image_picker import image_filetypes, image_start_directory
from nexus.desktop.image_preview import load_image_preview, PREVIEW_EXTENSIONS
from nexus.desktop.microphone_indicator import MicrophoneIndicator
from nexus.desktop.runtime_log import live_event
from nexus.desktop.tool_labels import action_label, resource_label
from nexus.desktop.workbench import open_notes, open_data_tools, open_benchmark
from nexus.desktop.library_panel import open_library
from nexus.desktop.maps_panel import open_maps
from nexus.desktop.presentation import (
    COLORS, DEFAULT_FONT, configure_presentation, message_size,
    composer_count, activity_state,
)
from nexus.models.resource_budget import ResourceBudget
from nexus.security.paths import PathSecurity
from nexus.voice import LocalRecognizer, LocalSpeaker, VoiceError
from nexus.voice.speech_text import readable_model_text, speech_from_model_text
from nexus.voice.wake import extract_utterance
from nexus.vision import LocalVision, VisionError, VisionInputError
from nexus.vision.camera_stream import CameraStream


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
    # Limit the Text widget independently of the six-turn model context and
    # the optional on-disk archive. A long voice session must not retain every
    # rendered message in Tk's edit buffer.
    MAX_VISIBLE_TRANSCRIPT_CHARS = 32_000

    def __init__(
        self, root, app, confirmation: DesktopConfirmation,
        speaker=None, recognizer=None, vision=None,
        startup_voice: bool | None = None,
        preference_store: DesktopPreferenceStore | None = None,
        chat_archive: ChatArchive | None = None,
    ):
        import tkinter as tk
        from tkinter import messagebox, ttk

        self.root = root
        self.app = app
        self.confirmation = confirmation
        # Production uses XDG config/state on this Linux account; injected
        # test speakers retain ephemeral behavior unless a store is supplied.
        self._preference_store = (
            preference_store if preference_store is not None
            else (DesktopPreferenceStore() if speaker is None else None)
        )
        self._preference_load_warning = None
        self._history_load_warning = None
        self._saved_preferences = None
        if self._preference_store is not None:
            try:
                self._saved_preferences = self._preference_store.load()
            except PreferenceStoreError:
                self._preference_load_warning = (
                    "As configurações locais não puderam ser restauradas."
                )
        self._chat_archive_store = (
            chat_archive if chat_archive is not None else (
                ChatArchive() if self._preference_store is not None else None
            )
        )
        chosen_archive = (
            self._chat_archive_store
            if self._saved_preferences is not None
            and self._saved_preferences.remember_history else None
        )
        try:
            self.session = ChatSession(app.agent, archive=chosen_archive)
        except ChatArchiveError:
            self._history_load_warning = (
                "O histórico local está inválido; as conversas anteriores não foram apagadas."
            )
            self.session = ChatSession(app.agent)
        self.tk = tk
        self.messagebox = messagebox
        self.speaker = speaker if speaker is not None else LocalSpeaker()
        # Production (real LocalSpeaker) welcomes by voice automatically.
        # Injected speakers in existing UI tests retain their original
        # quiet-start semantics; targeted voice tests opt in explicitly.
        self._startup_voice_enabled = (
            speaker is None if startup_voice is None else bool(startup_voice)
        )
        self.recognizer = recognizer if recognizer is not None else LocalRecognizer()
        self._replies: Queue[ChatReply] = Queue()
        self._audio_events: Queue[tuple[str, str, int]] = Queue()
        self._vision_events: Queue[tuple[str, str, str]] = Queue()
        self._camera_frames: Queue[bytes] = Queue()
        self._network_events: Queue[str] = Queue()
        self._network_watcher: PassiveConnectivityWatcher | None = None
        self._network_state = None
        self._camera_preview = None
        self._created_image_path: str | None = None
        self._created_image_window = None
        self._created_image_photo = None
        self._preview_policy = (getattr(getattr(app, "security_gate", None),
                                        "path_security", None) or PathSecurity())
        self._live_camera: CameraStream | None = None
        self._live_camera_window = None
        self._live_camera_label = None
        self._live_camera_sequence = 0
        self.vision = vision
        self._vision_buttons = []
        self._vision_source = None
        self._privacy_last = None
        self._busy = False
        self._operation_kind = None
        self._operation_started = 0.0
        self._last_progress_interval = 0
        self._chat_source = "texto"
        self._listen_started = 0.0
        self._speak_started = 0.0
        self._cancel_requested = False
        self._listening = False
        self._voice_active = (
            self._saved_preferences.listening_enabled
            if self._saved_preferences is not None else True
        )
        self._listen_generation = 0
        self._listen_pending_generations: set[int] = set()
        self._audio_peaks = 0
        self._audio_level_samples = 0
        self._mic_last_signal = 0.0
        self._recognition_failures = 0
        self._listen_retries = 0
        self._test_voice_turns_remaining = 0
        self._test_voice_reply_pending = False
        self._test_voice_speech_generation = None
        self._resource_budget = ResourceBudget.detect()
        self._speak_generation = 0
        self._speaking = False
        self._startup_welcome_generation = None
        self._closing = False
        self._permission_dialog: PermissionDialog | None = None
        self._workers: list[Thread] = []

        root.title(f"Nexus Core {settings.version} — Conversa local")
        root.geometry(
            self._saved_preferences.geometry
            if self._saved_preferences is not None else "980x720"
        )
        root.minsize(770, 570)
        root.configure(bg="#f5f1f3")
        menu = tk.Menu(root)
        resources = tk.Menu(menu, tearoff=False)
        resources.add_command(label="Anotações locais…", command=lambda: open_notes(root))
        resources.add_command(label="Biblioteca local…", command=lambda: open_library(root, app))
        resources.add_command(label="Mapas locais…", command=lambda: open_maps(root))
        resources.add_command(label="Ferramentas de dados…", command=lambda: open_data_tools(root))
        resources.add_command(label="Medir CPU local…", command=lambda: open_benchmark(root))
        menu.add_cascade(label="Recursos", menu=resources)
        root.configure(menu=menu)
        welcome_text, readiness_caption = desktop_startup_message(app)

        # Use the portable 'clam' theme for dependable branded button colors
        # on Ubuntu, while preserving native keyboard and ttk accessibility.
        style = ttk.Style(root)
        if "clam" in style.theme_names():
            style.theme_use("clam")
        style.configure("Nexus.App.TFrame", background="#f5f1f3")
        style.configure("Nexus.Header.TFrame", background="#241c24")
        style.configure("Nexus.Header.TLabel", background="#241c24",
                        foreground="#ffffff")
        style.configure("Nexus.HeaderHint.TLabel", background="#241c24",
                        foreground="#e9b4c4", font=("Sans", 9))
        for state, color in (("Online", "#246747"),
                             ("Offline", "#9d3947"),
                             ("Unknown", "#675761")):
            style.configure(f"Nexus.Network{state}.TLabel", background="#ffffff",
                            foreground=color, font=("Sans", 10, "bold"))
        style.configure("Nexus.Subtitle.TLabel", background="#f5f1f3",
                        foreground="#75646e", font=("Sans", 10))
        style.configure("Nexus.Section.TLabel", background="#f5f1f3",
                        foreground="#49333d", font=("Sans", 10, "bold"))
        style.configure("Nexus.Creative.TLabel", background="#ebe2e7",
                        foreground="#573b48", font=("Sans", 10),
                        padding=(12, 8))
        style.configure("Nexus.Caption.TLabel", background="#f5f1f3",
                        foreground="#584751", font=("Sans", 9))
        style.configure("Nexus.Status.TLabel", background="#ebe2e7",
                        foreground="#573b48", font=("Sans", 10),
                        padding=(12, 9))
        style.configure("Nexus.TCheckbutton", background="#f5f1f3",
                        foreground="#42323a", font=("Sans", 10))
        style.map("Nexus.TCheckbutton",
                  background=[("active", "#f5f1f3")])
        style.configure("Nexus.TButton", background="#eee6ea",
                        foreground="#382631", borderwidth=1,
                        padding=(12, 9), font=("Sans", 10))
        style.map("Nexus.TButton",
                  background=[("active", "#e4d9df"), ("pressed", "#d7c8d0")],
                  foreground=[("disabled", "#8e8189")])
        style.configure("Nexus.Primary.TButton", background="#722F37",
                        foreground="#ffffff", borderwidth=1,
                        padding=(12, 10), font=("Sans", 10, "bold"))
        style.map("Nexus.Primary.TButton",
                  background=[("active", "#8f3d4b"), ("pressed", "#59232f"),
                              ("disabled", "#cfb9c1")],
                  foreground=[("disabled", "#f6eef1")])
        style.configure("Nexus.Quiet.TButton", background="#f5f1f3",
                        foreground="#5e3a47", padding=(12, 9),
                        font=("Sans", 10))
        style.map("Nexus.Quiet.TButton",
                  background=[("active", "#ebdce2"), ("pressed", "#decbd4")])
        style.configure("Nexus.Danger.TButton", background="#e7d9df",
                        foreground="#672f40", padding=(12, 9),
                        font=("Sans", 10))
        style.map("Nexus.Danger.TButton",
                  background=[("active", "#dbc3cd"), ("pressed", "#cba7b6")])
        configure_presentation(style)
        style.configure("Nexus.Status.TLabel", background=COLORS.surface)

        frame = ttk.Frame(root, style="Nexus.App.TFrame", padding=14)
        frame.pack(fill="both", expand=True)

        # Keep the approved NEXUS CORE logo, only refine its container.
        self._brand_image = None
        brand = Path(__file__).resolve().parents[1] / "assets" / "brand" / "nexus-core-logo.png"
        if brand.is_file():
            try:
                self._brand_image = tk.PhotoImage(file=str(brand)).subsample(8, 8)
            except tk.TclError:
                self._brand_image = None
        header = ttk.Frame(frame, style="Nexus.Header.TFrame", padding=(14, 7))
        header.pack(fill="x", pady=(0, 5))
        if self._brand_image is not None:
            ttk.Label(header, image=self._brand_image,
                      style="Nexus.Header.TLabel").pack(side="left", anchor="center")
        else:
            ttk.Label(header, text="NEXUS CORE", font=("Sans", 20, "bold"),
                      style="Nexus.Header.TLabel").pack(side="left", anchor="center")
        ttk.Label(header, text="ASSISTENTE LOCAL\nCONVERSA · VISÃO · CRIAÇÃO",
                  justify="right", style="Nexus.HeaderHint.TLabel").pack(
                      side="right", anchor="center", padx=(8, 0))
        readiness_row = ttk.Frame(frame, style="Nexus.App.TFrame")
        readiness_row.pack(fill="x", pady=(0, 3))
        ttk.Label(readiness_row, text=readiness_caption,
                  style="Nexus.Subtitle.TLabel").pack(side="left")
        self.clear_history_button = ttk.Button(
            readiness_row, text="Apagar histórico",
            command=self._clear_saved_history, style="Nexus.Quiet.TButton")
        self.clear_history_button.pack(side="right", padx=(5, 0))
        self.archive_toggle = ttk.Checkbutton(
            readiness_row, text="Salvar conversas",
            command=self._toggle_archive, style="Nexus.TCheckbutton")
        if (self._saved_preferences is not None
                and self._saved_preferences.remember_history):
            self.archive_toggle.state(("selected",))
        self.archive_toggle.pack(side="right", padx=(8, 0))
        self.archive_enabled = _WidgetBoolean(self.archive_toggle)


        # Pack footer before the expanding transcript. All actions have their
        # own equal-width grid row; status never competes for button space.
        footer = ttk.Frame(frame, style="Nexus.App.TFrame")
        footer.pack(side="bottom", fill="x")

        transcript_frame = ttk.Frame(frame, padding=(2, 2), style="Nexus.Card.TFrame")
        transcript_frame.pack(fill="both", expand=True)
        conversation_toolbar = ttk.Frame(transcript_frame, style="Nexus.Card.TFrame")
        conversation_toolbar.pack(fill="x", padx=12, pady=(3, 2))
        ttk.Label(conversation_toolbar, text="CONVERSA LOCAL",
                  style="Nexus.CardTitle.TLabel").pack(side="left")
        self.test_button = ttk.Button(
            conversation_toolbar, text="Testar funções", command=self._show_test_panel,
            style="Nexus.Inline.TButton")
        self.test_button.pack(side="right", padx=(7, 0))
        self.quick_guide_button = ttk.Button(
            conversation_toolbar, text="Guia rápido", command=self._show_quick_guide,
            style="Nexus.Inline.TButton")
        self.quick_guide_button.pack(side="right", padx=(5, 0))
        self.zoom_in_button = ttk.Button(
            conversation_toolbar, text="A+", command=lambda: self._zoom_conversation(1),
            style="Nexus.Inline.TButton")
        self.zoom_in_button.pack(side="right", padx=(4, 0))
        self.zoom_out_button = ttk.Button(
            conversation_toolbar, text="A−", command=lambda: self._zoom_conversation(-1),
            style="Nexus.Inline.TButton")
        self.zoom_out_button.pack(side="right", padx=(4, 0))
        self.preview_image_button = ttk.Button(
            conversation_toolbar, text="Ver imagem criada", command=self._show_created_image,
            style="Nexus.Inline.TButton", state="disabled")
        self.preview_image_button.pack(side="right", padx=(7, 0))
        self.network_badge = ttk.Label(
            conversation_toolbar, text="● NÃO VERIFICADO",
            style="Nexus.NetworkUnknown.TLabel")
        self.network_badge.pack(side="right", anchor="center", padx=(12, 0))
        self._conversation_font_size = DEFAULT_FONT
        self.transcript = tk.Text(
            transcript_frame, height=5, wrap="word", state="disabled",
            padx=16, pady=14, bg="#ffffff", fg="#2c242a",
            font=("Sans", DEFAULT_FONT), relief="flat", borderwidth=0,
            highlightthickness=1, highlightbackground=COLORS.card_border,
            highlightcolor=COLORS.wine,
        )
        scrollbar = ttk.Scrollbar(transcript_frame, command=self.transcript.yview)
        self.transcript.configure(yscrollcommand=scrollbar.set)
        self.transcript.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.transcript.tag_configure(
            "user", foreground="#722F37", font=("Sans", 11, "bold"),
            spacing1=8)
        self.transcript.tag_configure(
            "assistant", foreground="#34232d", font=("Sans", DEFAULT_FONT, "bold"),
            spacing1=8)
        self.transcript.tag_configure(
            "message-user", foreground=COLORS.ink, background=COLORS.user_surface,
            font=("Sans", DEFAULT_FONT), spacing1=3, spacing3=3,
            lmargin1=12, lmargin2=12, rmargin=12)
        self.transcript.tag_configure(
            "message-assistant", foreground=COLORS.ink,
            font=("Sans", DEFAULT_FONT), spacing1=3, spacing3=3,
            lmargin1=12, lmargin2=12, rmargin=12)

        # Compact first row: speech preferences are distinct from listening.
        voice_controls = ttk.Frame(footer, style="Nexus.App.TFrame")
        voice_controls.pack(fill="x", pady=(3, 0))
        self.speech_toggle = ttk.Checkbutton(
            voice_controls, text="Responder em voz",
            command=self._toggle_speech, style="Nexus.TCheckbutton",
        )
        self.speech_toggle.state(("selected",))
        self.speech_toggle.pack(side="left")
        self.speech_enabled = _WidgetBoolean(self.speech_toggle)
        if (self._saved_preferences is not None
                and not self._saved_preferences.speech_enabled):
            self.speech_enabled.set(False)
        ttk.Label(voice_controls, text="Voz:", style="Nexus.Caption.TLabel").pack(
            side="left", padx=(15, 5))
        self.voice_selector = ttk.Combobox(
            voice_controls, values=("Feminina", "Masculina"),
            state="readonly", width=12,
        )
        self.voice_selector.set(
            self._saved_preferences.voice
            if self._saved_preferences is not None
            else ("Masculina" if LocalSpeaker.neural_voice_ready() else "Feminina")
        )
        self.voice_selector.pack(side="left")
        self.voice_choice = _WidgetChoice(self.voice_selector)
        self.voice_selector.bind("<<ComboboxSelected>>", self._save_desktop_preferences)
        ttk.Label(voice_controls, text="Entrada:", style="Nexus.Caption.TLabel").pack(
            side="left", padx=(11, 4))
        self.audio_input_choice = ttk.Combobox(
            voice_controls, values=("Automático", "PipeWire", "ALSA"),
            state="readonly", width=10,
        )
        preferred_backend = (
            self._saved_preferences.audio_backend
            if self._saved_preferences is not None else "auto"
        )
        self.audio_input_choice.set({
            "auto": "Automático", "pipewire": "PipeWire",
            "alsa": "ALSA",
        }[preferred_backend])
        if isinstance(self.recognizer, LocalRecognizer):
            self.recognizer.audio_backend = preferred_backend
        self.audio_input_choice.pack(side="left")
        self.audio_input_choice.bind("<<ComboboxSelected>>", self._select_audio_input)
        self.wake_toggle = ttk.Checkbutton(
            voice_controls, text='Ativar por "Nexus"',
            command=self._toggle_wake, style="Nexus.TCheckbutton",
        )
        self.wake_toggle.pack(side="left", padx=(9, 0))
        self.wake_required = _WidgetBoolean(self.wake_toggle)
        if self._saved_preferences is not None and self._saved_preferences.wake_required:
            self.wake_required.set(True)

        # Photo and live video are separate actions; neither opens a device
        # before its own explicit authorization.
        vision_controls = ttk.Frame(footer, style="Nexus.App.TFrame")
        vision_controls.pack(fill="x", pady=(3, 0))
        ttk.Label(vision_controls, text="VISÃO SOB AUTORIZAÇÃO",
                  style="Nexus.Section.TLabel").pack(side="left", padx=(0, 10))
        vision_actions = ttk.Frame(vision_controls, style="Nexus.App.TFrame")
        vision_actions.pack(side="left", fill="x", expand=True)
        for column in range(4):
            vision_actions.columnconfigure(column, weight=1, uniform="vision")
        for column, (title, callback) in enumerate((
            ("Imagem", self._vision_file),
            ("Tela", self._vision_screen),
            ("Foto da câmera", self._vision_camera_photo),
            ("Câmera ao vivo", self._vision_camera),
        )):
            button = ttk.Button(vision_actions, text=title,
                                command=callback, style="Nexus.TButton")
            button.grid(row=0, column=column, sticky="ew",
                        padx=(0, 6) if column < 3 else (0, 0))
            self._vision_buttons.append(button)

        # Signals describe SOFTWARE activity, never hardware certification.
        privacy_row = ttk.Frame(footer, style="Nexus.App.TFrame")
        privacy_row.pack(fill="x", pady=(2, 0))
        self.microphone_indicator = MicrophoneIndicator(privacy_row)
        self.microphone_indicator.widget.pack(side="left", padx=(0, 7))
        self._audio_level_label = ttk.Label(
            privacy_row, text="Entrada: aguardando",
            style="Nexus.Caption.TLabel")
        self._audio_level_label.pack(side="left", padx=(0, 10))
        self._privacy_labels = []
        for label_text in ("Escuta: aguardando", "Voz: habilitada",
                           "Visão: sem captura"):
            widget = ttk.Label(
                privacy_row, text=label_text, style="Nexus.Caption.TLabel")
            widget.pack(side="left", padx=(0, 10))
            self._privacy_labels.append(widget)

        composer_title = ttk.Frame(footer, style="Nexus.App.TFrame")
        composer_title.pack(fill="x", pady=(3, 2))
        ttk.Label(composer_title,
                  text="SUA MENSAGEM  ·  Enter envia  •  Shift+Enter quebra linha",
                  style="Nexus.Section.TLabel").pack(side="left")
        self.composer_counter = ttk.Label(
            composer_title, text="0 / 4000 caracteres",
            style="Nexus.Counter.TLabel")
        self.composer_counter.pack(side="right", padx=(8, 0))
        self.input = tk.Text(
            footer, height=2, wrap="word", font=("Sans", 11),
            bg="#ffffff", fg="#292127", relief="flat",
            padx=11, pady=8, borderwidth=0,
            highlightthickness=1, highlightbackground="#d7c5cd",
            highlightcolor="#722F37",
        )
        self.input.pack(fill="x")
        self.input.bind("<Control-Return>", self._send)
        self.input.bind("<Return>", self._send)
        # Shift+Enter retains normal multiline text entry.
        self.input.bind("<Shift-Return>", lambda event: None)
        self.input.bind("<KeyRelease>", self._refresh_composer_count)
        self.input.bind("<<Paste>>", lambda event: self.root.after_idle(self._refresh_composer_count))

        # Each action gets an equal, responsive column. Keep original
        # attributes, shortcuts and state transitions for compatibility.
        controls = ttk.Frame(footer, style="Nexus.App.TFrame")
        controls.pack(fill="x", pady=(3, 0))
        for column in range(5):
            controls.columnconfigure(column, weight=1, uniform="actions")
        self.suggest_button = ttk.Button(
            controls, text="Sugerir", command=self._suggest,
            style="Nexus.Quiet.TButton")
        self.suggest_button.grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.send_button = ttk.Button(
            controls, text="Enviar", command=self._send,
            style="Nexus.Primary.TButton")
        self.send_button.grid(row=0, column=1, sticky="ew", padx=(0, 6))
        self.cancel_button = ttk.Button(
            controls, text="Cancelar", command=self._cancel_current,
            style="Nexus.TButton", state="disabled")
        self.cancel_button.grid(row=0, column=2, sticky="ew", padx=(0, 6))
        self.mic_button = ttk.Button(
            controls, text=("Pausar escuta" if self._voice_active else "Retomar escuta"),
            command=self._toggle_listening,
            style="Nexus.TButton")
        self.mic_button.grid(row=0, column=3, sticky="ew", padx=(0, 6))
        self.shutdown_button = ttk.Button(
            controls, text="Desligar assistente", command=self._close,
            style="Nexus.Danger.TButton")
        self.shutdown_button.grid(row=0, column=4, sticky="ew")

        # Full-width status strip: long diagnostics never hide Send/Cancel.
        status_strip = ttk.Frame(footer, style="Nexus.Soft.TFrame")
        status_strip.pack(fill="x", pady=(2, 0))
        self.activity_badge = ttk.Label(
            status_strip, text="● PRONTO", style="Nexus.LiveReady.TLabel")
        self.activity_badge.pack(side="left")
        self._activity_last = ("● PRONTO", "Nexus.LiveReady.TLabel")
        self.status = ttk.Label(
            status_strip, text="Inicializando a escuta local…",
            style="Nexus.Status.TLabel", anchor="w")
        self.status.pack(side="left", fill="x", expand=True)
        root.protocol("WM_DELETE_WINDOW", self._close)
        root.bind("<Control-Shift-M>", self._shortcut_toggle_listening)
        root.bind("<Control-Shift-I>", self._show_privacy_status)
        root.bind("<Control-Shift-X>", self._shortcut_cancel_current)
        root.bind("<Control-Shift-S>", self._shortcut_stop_speaking)
        root.bind("<Control-Shift-V>", self._shortcut_toggle_speech)
        root.bind("<Control-Shift-F>", self._shortcut_vision_file)
        root.bind("<Control-Shift-T>", self._shortcut_vision_screen)
        root.bind("<Control-Shift-K>", self._shortcut_vision_camera)
        root.bind("<Control-Shift-P>", self._shortcut_camera_photo)
        root.bind("<Control-plus>", lambda event: self._zoom_conversation(1))
        root.bind("<Control-equal>", lambda event: self._zoom_conversation(1))
        root.bind("<Control-minus>", lambda event: self._zoom_conversation(-1))
        root.bind("<Control-l>", self._focus_composer)
        # Welcome text is displayed immediately. Its short spoken version
        # uses the existing local TTS worker before microphone listening starts.
        # Restore only normal text conversation. Never replay raw device
        # captures, tool outputs, consent decisions or microphone recordings.
        for saved_question, saved_answer in self.session.history:
            self._append("Você", saved_question, "user")
            self._append("Nexus Core", saved_answer, "assistant")
        self._append("Nexus Core", welcome_text, "assistant")
        if self._preference_load_warning:
            self._append("Nexus Core", self._preference_load_warning, "assistant")
        if self._history_load_warning:
            self._append("Nexus Core", self._history_load_warning, "assistant")
        self.input.focus_set()
        self._refresh_privacy_status()
        # In forced offline mode, read only NetworkManager's cached OS state.
        # The existing active monitor is used when the runtime permits probes.
        if (hasattr(app, "connectivity_manager")
                and getattr(app, "connectivity_monitor", None) is None):
            self._network_watcher = PassiveConnectivityWatcher(self._network_events.put)
            self._network_watcher.start()
        self._refresh_network_status()
        live_event("interface", "pronto")
        live_event(
            "recurso", "pronto", profile=self._resource_budget.mode,
            threads=self._resource_budget.num_thread,
            memory_mib=self._resource_budget.available_ram_mib,
        )
        root.after(80, self._poll)
        root.after(120, self._start_spoken_welcome)

    def _start_voice_diagnostic(self) -> None:
        """Require two answered, spoken turns followed by resumed listening."""
        if self._closing:
            return
        self._test_voice_turns_remaining = 2
        self._test_voice_reply_pending = False
        self._test_voice_speech_generation = None
        live_event("teste", "iniciado", source="voz")
        self._append(
            "Nexus Core",
            "Teste de escuta contínua iniciado. Faça duas perguntas em voz "
            "alta, aguardando o fim de cada resposta. O terminal mostrará "
            "recebido após a primeira resposta falada e concluido após a segunda, "
            "quando a escuta recomeçar. Nenhuma transcrição será gravada no log.",
            "assistant",
        )
        if not self._voice_active:
            self._toggle_listening()
        else:
            self._start_listening()

    def _show_test_panel(self) -> None:
        """Human-operated checks; nothing sensitive runs without consent."""
        if self._closing:
            return
        from tkinter import ttk
        panel = self.tk.Toplevel(self.root)
        panel.title("NEXUS CORE — testes locais")
        panel.transient(self.root)
        panel.resizable(False, False)
        body = ttk.Frame(panel, padding=16, style="Nexus.App.TFrame")
        body.pack(fill="both", expand=True)
        ttk.Label(
            body, text="Teste cada função na janela e acompanhe os logs.",
            style="Nexus.Section.TLabel",
        ).pack(anchor="w", pady=(0, 10))
        steps = (
            ("Voz: testar duas falas", self._start_voice_diagnostic),
            ("Câmera: abrir com consentimento", self._vision_camera),
            ("Pasta: como testar", lambda: self._show_test_instructions(
                "Pasta", "Digite no chat: Crie uma pasta chamada NexusCoreTeste. "
                "Negue uma tentativa, repita e autorize. A pasta só deve "
                "ser criada após sua aprovação.")),
            ("Aplicativo: como testar", lambda: self._show_test_instructions(
                "Aplicativo", "Digite no chat: Abra o navegador. "
                "Negue uma tentativa, repita e autorize. Confira o "
                "registro de autorização e a execução da ferramenta.")),
            ("Imagem: selecionar com consentimento",
             lambda: self._request_vision("file")),
            ("Arquivo: inspeção estática local", lambda: self._show_test_instructions(
                "Inspeção local", "Copie um arquivo de teste para sua pasta pessoal. "
                "Digite no chat: Analise o arquivo /home/usuario/NexusTestes/teste.elf "
                "(substitua pelo caminho verdadeiro). Negue uma vez; depois "
                "autorize a leitura. Nenhum executável será iniciado e "
                "nenhum dado será enviado à rede.")),
        )
        for label, action in steps:
            ttk.Button(body, text=label, style="Nexus.Quiet.TButton",
                       command=action).pack(fill="x", pady=3)
        ttk.Label(body, text=(
            "Resultados reais: evento=teste, escuta, reconhecimento, "
            "camera, visao, autorizacao e ferramenta. Nenhuma ação "
            "sem consentimento."
        ), style="Nexus.Caption.TLabel", wraplength=420).pack(
            fill="x", pady=(12, 0))
        live_event("teste", "solicitado", source="texto")

    def _show_test_instructions(self, title: str, message: str) -> None:
        live_event("teste", "solicitado", source="texto")
        self.messagebox.showinfo(
            f"NEXUS CORE — Teste de {title.lower()}", message, parent=self.root,
        )

    def _save_desktop_preferences(self, event=None) -> None:
        """Persist only user choices on this Linux account, never credentials."""
        if self._preference_store is None or self._closing:
            return
        backend = {
            "Automático": "auto", "PipeWire": "pipewire", "ALSA": "alsa",
        }.get(self.audio_input_choice.get(), "auto")
        geometry = self.root.geometry().split("+", 1)[0].split("-", 1)[0]
        try:
            preferences = DesktopPreferences(
                voice=self.voice_choice.get(),
                speech_enabled=self.speech_enabled.get(),
                wake_required=self.wake_required.get(),
                audio_backend=backend,
                listening_enabled=self._voice_active,
                geometry=geometry,
                remember_history=self.archive_enabled.get(),
            )
            # In the brief period before the Tk window is mapped, geometry
            # may still be 1x1. Never destroy a valid stored size for that.
            try:
                preferences.validate()
            except PreferenceStoreError:
                from dataclasses import replace
                preferences = replace(
                    preferences,
                    geometry=(self._saved_preferences.geometry
                              if self._saved_preferences is not None else "980x720"),
                )
            self._preference_store.save(preferences)
            self._saved_preferences = preferences
        except PreferenceStoreError:
            self.status.configure(
                text="Não foi possível salvar configurações. Confira a pasta local."
            )

    def _toggle_archive(self) -> None:
        if self._closing:
            return
        if self._chat_archive_store is None:
            self.archive_enabled.set(False)
            self.status.configure(text="Histórico local indisponível nesta sessão.")
            return
        self.session.set_archive(
            self._chat_archive_store if self.archive_enabled.get() else None
        )
        self._save_desktop_preferences()
        self.status.configure(
            text=("Salvamento local de conversas ativado."
                  if self.archive_enabled.get()
                  else "Salvamento de novas conversas desativado.")
        )

    def _clear_saved_history(self) -> None:
        """Explicit, one-time consent; never delete history on app startup."""
        if self._closing or self._busy or self._chat_archive_store is None:
            return
        if not self.messagebox.askyesno(
            "Apagar histórico do Nexus Core",
            "Apagar permanentemente as conversas textuais salvas neste "
            "computador? A operação não pode ser desfeita.",
            parent=self.root,
        ):
            return
        try:
            self._chat_archive_store.clear()
        except ChatArchiveError:
            self.status.configure(text="Não foi possível apagar o histórico local.")
            return
        self.session.forget_context()
        self.transcript.configure(state="normal")
        self.transcript.delete("1.0", "end")
        self.transcript.configure(state="disabled")
        self._append("Nexus Core", "Histórico de conversas locais apagado.", "assistant")
        self.status.configure(text="Histórico local apagado.")

    def _privacy_snapshot(self) -> MultimodalStatus:
        """Capture presentation state on the Tk thread, without probing devices."""
        return MultimodalStatus(
            listening_allowed=self._voice_active,
            listening_requested=self._listening,
            speech_enabled=self.speech_enabled.get(),
            speech_requested=self._speaking,
            vision_busy=self._busy and self._operation_kind == "vision",
            vision_source=self._vision_source,
            camera_active=self._live_camera is not None,
            camera_starting=(self._live_camera is not None
                             and self._live_camera_sequence == 0),
            cancellation_requested=self._cancel_requested,
            closing=self._closing,
        )

    def _refresh_privacy_status(self) -> None:
        """Update only labels for changed state; run exclusively on Tk thread."""
        labels = self._privacy_snapshot().labels()
        if labels != self._privacy_last:
            for widget, label in zip(self._privacy_labels, labels):
                widget.configure(text=label)
            self._privacy_last = labels

    def _show_privacy_status(self, event=None):
        """Explicit, keyboard-accessible snapshot; no capture or Agent call."""
        if not self._closing:
            labels = self._privacy_snapshot().labels()
            self.messagebox.showinfo(
                "Nexus Core — estado de privacidade",
                "\n".join(labels) + "\n\nEstados do aplicativo; não verificam hardware.",
                parent=self.root,
            )
        return "break"

    def _answer_privacy_status(self, utterance: str) -> None:
        """Answer an explicit voice or text request using only current Tk state."""
        labels = self._privacy_snapshot().labels()
        response = ". ".join(labels) + ". Estados do aplicativo; não verificam hardware."
        self._append("Você", utterance, "user")
        self._append("Nexus Core", response, "assistant")
        self.status.configure(text="Estado de privacidade informado")
        if not self._say_response(response):
            self._start_listening()

    def _shortcut_toggle_listening(self, event=None):
        """Keyboard access to the same mic toggle, never to visual capture."""
        if not self._closing:
            self._toggle_listening()
        return "break"

    def _shortcut_cancel_current(self, event=None):
        """Use the existing Cancel action for the current operation only."""
        self._cancel_current()
        return "break"

    def _shortcut_stop_speaking(self, event=None):
        """Stop only the current TTS output, keeping future speech enabled."""
        if not self._closing and self._speaking:
            self._stop_speaking()
            self.status.configure(text="Leitura em voz interrompida")
            self._start_listening()
        return "break"

    def _shortcut_toggle_speech(self, event=None):
        """Use the speech checkbutton policy without changing microphone state."""
        if not self._closing:
            self.speech_enabled.set(not self.speech_enabled.get())
            self._toggle_speech()
            self._refresh_privacy_status()
        return "break"

    def _show_quick_guide(self) -> None:
        """A local description of available flows, not a claim of device readiness."""
        self.messagebox.showinfo(
            "Nexus Core — guia rápido",
            "Converse por texto ou voz quando o modelo local estiver disponível.\n\n"
            "• Imagem, tela e câmera exigem autorização por captura.\n"
            "• Edição de fotos e operações disponíveis de documento/PDF geram cópias novas.\n"
            "• Inspeção estática lê apenas arquivos autorizados.\n"
            "• Algumas conversões e operações em PDF exigem componentes locais opcionais.\n\n"
            "Atalhos: Enter envia; Shift+Enter quebra linha;\n"
            "Ctrl+L foca a mensagem; Ctrl++ / Ctrl+- ajustam a leitura;\n"
            "Ctrl+Shift+M pausa/retoma a escuta;\n"
            "Ctrl+Shift+I informa o estado de privacidade;\n"
            "Ctrl+Shift+X solicita cancelamento.\n\n"
            "Nenhuma função realiza capturas ou ações sem as permissões exigidas.",
            parent=self.root,
        )

    def _remember_created_image(self, result) -> None:
        """Offer a preview only after a mediated image action succeeded."""
        if (not result.success or result.tool_name not in {
                "edit_image_local", "image_geometry_local", "create_graphic_local",
                "craft_convert_local"} or not isinstance(result.data, dict)):
            return
        path = result.data.get("path")
        if isinstance(path, str) and Path(path).suffix.lower() in PREVIEW_EXTENSIONS:
            self._created_image_path = path
            self.preview_image_button.configure(state="normal")

    def _close_created_image(self) -> None:
        if self._created_image_window is not None:
            self._created_image_window.destroy()
            self._created_image_window = None
        self._created_image_photo = None

    def _show_created_image(self) -> None:
        """Display a bounded copy inside Nexus; never launch an external app."""
        if self._closing or self._created_image_path is None:
            return
        try:
            from PIL import ImageTk
            image = load_image_preview(self._created_image_path, self._preview_policy)
            image.thumbnail((max(1, min(720, self.root.winfo_screenwidth() - 80)),
                             max(1, min(480, self.root.winfo_screenheight() - 180))))
            self._close_created_image()
            preview = self.tk.Toplevel(self.root)
            self._created_image_window = preview
            preview.title("Nexus Core — imagem criada")
            preview.configure(bg=COLORS.header)
            preview.transient(self.root)
            preview.protocol("WM_DELETE_WINDOW", self._close_created_image)
            head = self.tk.Frame(preview, bg=COLORS.header, padx=16, pady=12)
            head.pack(fill="x")
            self.tk.Label(head, text="PRÉVIA LOCAL", bg=COLORS.header,
                          fg="#ffffff", font=("Sans", 12, "bold")).pack(side="left")
            self.tk.Label(head, text=f"{image.width} × {image.height} px",
                          bg=COLORS.header, fg="#e9b4c4",
                          font=("Sans", 10)).pack(side="right")
            self._created_image_photo = ImageTk.PhotoImage(image, master=preview)
            self.tk.Label(preview, image=self._created_image_photo,
                          bg=COLORS.paper, padx=12, pady=12).pack(padx=12, pady=(0, 10))
            self.tk.Button(preview, text="Fechar prévia", command=self._close_created_image,
                           bg=COLORS.wine, fg="white", activebackground=COLORS.wine_hover,
                           activeforeground="white", relief="flat", padx=16, pady=8,
                           cursor="hand2").pack(pady=(0, 12))
            self.status.configure(text="Prévia local da imagem criada")
        except (ImportError, OSError, ValueError, PermissionError, self.tk.TclError):
            self._close_created_image()
            self.status.configure(text="Prévia indisponível; a imagem original não foi alterada")

    def _zoom_conversation(self, delta: int):
        """Improve legibility without changing persisted layout or permissions."""
        size = message_size(self._conversation_font_size, delta)
        if size != self._conversation_font_size:
            self._conversation_font_size = size
            self.transcript.configure(font=("Sans", size))
            for label in ("user", "assistant"):
                self.transcript.tag_configure(
                    label, font=("Sans", size, "bold"))
            for label in ("message-user", "message-assistant"):
                self.transcript.tag_configure(label, font=("Sans", size))
        return "break"

    def _focus_composer(self, event=None):
        if not self._closing:
            self.input.focus_set()
        return "break"

    def _refresh_composer_count(self, event=None) -> None:
        length = len(self.input.get("1.0", "end-1c"))
        label, style = composer_count(length, limit=ChatSession.MAX_MESSAGE)
        self.composer_counter.configure(text=label, style=style)

    def _refresh_activity_badge(self) -> None:
        state = activity_state(busy=self._busy, closing=self._closing)
        if state != self._activity_last:
            self.activity_badge.configure(text=state[0], style=state[1])
            self._activity_last = state

    def _append(self, speaker: str, message: str, tag: str) -> None:
        self.transcript.configure(state="normal")
        self.transcript.insert("end", f"{speaker}\n", tag)
        self.transcript.insert("end", f"{message}\n",
                               "message-user" if tag == "user" else "message-assistant")
        self.transcript.insert("end", "\n")
        total = self.transcript.count("1.0", "end-1c", "chars")[0]
        if total > self.MAX_VISIBLE_TRANSCRIPT_CHARS:
            cutoff = self.transcript.index(
                f"end-1c - {self.MAX_VISIBLE_TRANSCRIPT_CHARS} chars"
            )
            # Prefer removing complete old messages. If the newest message
            # itself is very long, retain its last 32k characters instead.
            paragraph = self.transcript.search("\n\n", cutoff, stopindex="end")
            if paragraph and self.transcript.compare(paragraph, "<", "end-3c"):
                cutoff = self.transcript.index(f"{paragraph}+2c")
            self.transcript.delete("1.0", cutoff)
        self.transcript.configure(state="disabled")
        self.transcript.see("end")

    def _start_worker(self, target, *args) -> None:
        """Retain workers; collect stale Tk widgets on the GUI thread first."""
        # Tk/Tcl objects finalized by Python GC in a worker can abort the
        # interpreter. Flush cycles from closed dialogs/windows on this Tk
        # thread before starting a new voice or vision worker.
        gc.collect()
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
        self.microphone_indicator.release()
        self._workers.clear()
        self._vision_buttons.clear()
        self._privacy_labels.clear()
        self.vision = None
        if self._camera_preview is not None:
            self._camera_preview.destroy()
            self._camera_preview = None
        self.app.shutdown()
        self.root.destroy()
        # A destroyed Tcl interpreter must not be collected later on an audio
        # or vision thread; finalize its remaining widget cycles here.
        gc.collect()

    def _suggest(self):
        if self._busy or self._closing:
            return
        self.input.delete("1.0", "end")
        self.input.insert(
            "1.0", "Considerando a conversa, sugira próximos passos práticos "
                   "que eu possa escolher. Apenas aconselhe, sem executar ações.",
        )
        self._refresh_composer_count()
        self._send(advisory_only=True)

    def _cancel_current(self):
        """Cancel pending answer presentation and block future tool execution.

        It cannot undo an already executed action or interrupt every Ollama call.
        """
        if not self._busy or self._closing or self._cancel_requested:
            return
        self._cancel_requested = True
        self._test_voice_reply_pending = False
        self._test_voice_speech_generation = None
        live_event("cancelamento", "solicitado")
        if self._operation_kind == "chat":
            self.session.cancel_current()
            # Release threads blocked on tool consent immediately.
            self.confirmation.cancel_pending()
            if self._permission_dialog is not None:
                self._permission_dialog._finish(False)
        self.cancel_button.configure(state="disabled")
        self.status.configure(text="Cancelamento solicitado; finalizando operação…")

    def _finish_operation(self):
        self._busy = False
        self._cancel_requested = False
        self._operation_kind = None
        self._vision_source = None
        self.send_button.configure(state="normal")
        self.suggest_button.configure(state="normal")
        self.cancel_button.configure(state="disabled")
        for button in self._vision_buttons:
            button.configure(state="normal")
        self._refresh_activity_badge()

    def _say_response(self, text: str) -> bool:
        """Speak normal and visual answers through the same local TTS channel."""
        if not self.speech_enabled.get() or not text.strip():
            return False
        if " executada.\n{" in text or " executada.\n[" in text:
            text = "A ação foi concluída. Confira os detalhes na conversa."
        # Model outputs may contain Markdown (bold, bullets, links, code).
        # Convert only the TTS copy; do not modify the source turn or logs.
        text = speech_from_model_text(
            text, max_characters=(
                450 if self._resource_budget.mode == "eco" else 1300
            ),
        )
        if not text:
            return False
        self._speak_generation += 1
        generation = self._speak_generation
        self._speaking = True
        self._speak_started = monotonic()
        live_event("fala", "iniciado")
        self._start_worker(self._speak, text, self.voice_choice.get(), generation)
        return True

    def _send(self, event=None, *, advisory_only=False, channel="texto"):
        if self._busy or self._closing:
            return "break"
        message = self.input.get("1.0", "end-1c").strip()
        if not message:
            return "break"
        if len(message) > ChatSession.MAX_MESSAGE:
            self.status.configure(text="Mensagem excede 4000 caracteres")
            return "break"
        command = self._voice_command(message) if not advisory_only else None
        if command == "camera_photo":
            self.input.delete("1.0", "end")
            self._vision_camera_photo()
            return "break"
        if command in ("camera_on", "camera_off"):
            self.input.delete("1.0", "end")
            self._append("Você", message, "user")
            if command == "camera_off":
                self._stop_live_camera()
            elif self._live_camera is None:
                self._start_live_camera()
            return "break"
        if not advisory_only and self._live_camera is not None and self._camera_question(message):
            self.input.delete("1.0", "end")
            self._ask_live_camera(message)
            return "break"
        if command == "privacy_status":
            # A typed status request is local, even while the microphone is
            # paused. Stop active recognition/playback before replying so TTS
            # cannot be picked up as a second user turn.
            self.input.delete("1.0", "end")
            if self._listening:
                self._listen_generation += 1
                self.recognizer.stop()
            if self._speaking:
                self._stop_speaking()
            self._answer_privacy_status(message)
            return "break"
        self.input.delete("1.0", "end")
        self._refresh_composer_count()
        self._append("Você", message, "user")
        self.session.prepare_turn()
        self.microphone_indicator.show_peak(0, listening=False)
        self._mic_last_signal = 0.0
        self._busy = True
        self._operation_kind = "chat"
        self._operation_started = monotonic()
        self._last_progress_interval = 0
        self._chat_source = channel
        self._cancel_requested = False
        live_event("chat", "iniciado", source=channel)
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
        self._refresh_activity_badge()
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

    def _start_spoken_welcome(self) -> None:
        """Say the startup welcome once using the chosen local voice.

        Tk schedules this after the window appears, never during __init__.
        Keep microphone recognition stopped until synthesis/playback ends, so
        it cannot recognize its own speech. Respect user mute and active work.
        """
        if self._closing or self._busy or self._speaking or self._listening:
            return
        if not self._startup_voice_enabled:
            self._start_listening()
            return
        if self._say_response(desktop_spoken_welcome()):
            self._startup_welcome_generation = self._speak_generation
            self.status.configure(text="Reproduzindo boas-vindas em voz…")
        else:
            self._start_listening()

    def _start_listening(self) -> None:
        if (not self._voice_active or self._busy or self._listening
                or self._listen_pending_generations or self._speaking or self._closing):
            return
        self._listening = True
        self._listen_generation += 1
        generation = self._listen_generation
        self._listen_pending_generations.add(generation)
        self._audio_peaks = 0
        self._audio_level_samples = 0
        self._mic_last_signal = 0.0
        self._listen_started = monotonic()
        live_event("escuta", "iniciado", source="voz")
        self.microphone_indicator.show_peak(0, listening=True)
        self._audio_level_label.configure(text="Entrada: aguardando")
        self.status.configure(text="Ouvindo… diga sua pergunta")
        self._start_worker(self._listen, generation)

    def _select_audio_input(self, event=None) -> None:
        """Change only this recognizer's backend; keep OS defaults intact."""
        if self._closing:
            return
        selected = {
            "Automático": "auto",
            "PipeWire": "pipewire",
            "ALSA": "alsa",
        }.get(self.audio_input_choice.get(), "auto")
        if isinstance(self.recognizer, LocalRecognizer):
            self.recognizer.audio_backend = selected
            if self._listening:
                self._listen_generation += 1
                self.recognizer.stop()
            self.status.configure(
                text=f"Microfone: {self.audio_input_choice.get()}. "
                     "Fale uma frase para testar a transcrição."
            )
        else:
            self.status.configure(text="Seleção de entrada indisponível neste reconhecedor.")
        self._save_desktop_preferences()

    def _toggle_listening(self) -> None:
        if self._closing:
            return
        self._voice_active = not self._voice_active
        live_event("escuta", "retomado" if self._voice_active else "pausado", source="voz")
        self.mic_button.configure(
            text="Pausar escuta" if self._voice_active else "Retomar escuta"
        )
        if self._voice_active:
            self._start_listening()
        else:
            self._listen_generation += 1
            self.recognizer.stop()
            self.microphone_indicator.show_peak(0, listening=False)
            self._mic_last_signal = 0.0
            self._audio_level_label.configure(text="Entrada: pausada")
            self.status.configure(text="Escuta pausada; use Retomar escuta")
        self._save_desktop_preferences()

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
        if normalized in {"qual o estado da privacidade", "qual e o estado da privacidade",
                          "como esta minha privacidade", "informe o estado da privacidade"}:
            return "privacy_status"
        if normalized in {"ative a voz", "ligue a voz", "ativar voz",
                          "ligar voz", "leia as respostas em voz alta"}:
            return "speech_on"
        if normalized in {"desative a voz", "desligue a voz", "desativar voz",
                          "desligar voz", "responda somente por texto"}:
            return "speech_off"
        if normalized in {"use voz feminina", "mude para voz feminina",
                          "selecione voz feminina"}:
            return "voice_female"
        if normalized in {"use voz masculina", "mude para voz masculina",
                          "selecione voz masculina"}:
            return "voice_male"
        if normalized in {"analisar imagem", "analise uma imagem",
                          "analisar arquivo de imagem"}:
            return "vision_file"
        if normalized in {"analisar tela", "analise a tela", "mostre a tela"}:
            return "vision_screen"
        if normalized in {"analisar tela inteira", "analise a tela inteira",
                          "analisar monitor", "analise o monitor"}:
            return "vision_display"
        if normalized in {"analisar janela", "analise a janela", "analisar pagina",
                          "analise a pagina", "listar janelas", "mostre as janelas"}:
            return "vision_window"
        # Named capture requests require an explicit target. Do not turn
        # compound speech (e.g. "analisar tela e executar comando") into a
        # capture request; actions must remain under the normal SecurityGate.
        if (" e " not in normalized and re.fullmatch(
            r"(?:analise|analisar|mostre) (?:a |uma )?(?:janela|pagina|tela) "
            r"(?:do|da|de) [a-z0-9][a-z0-9 ._-]{0,79}", normalized
        )):
            return "vision_window"
        if normalized in {"feche a camera", "desligue a camera", "pare a camera",
                          "fechar camera", "desligar camera"}:
            return "camera_off"
        if normalized in {"abra a camera", "abrir camera", "mostre a camera",
                          "ligue a camera"}:
            return "camera_on"
        if normalized in {"analisar camera", "analise a camera"}:
            return "vision_camera"
        if normalized in {"tire uma foto", "tire foto", "foto da camera",
                          "fotografe a camera", "analise uma foto da camera",
                          "tire um print da camera"}:
            return "camera_photo"
        return None

    def _spoken_speech_control(self, command: str, utterance: str) -> None:
        """Apply a recognized local setting without involving the model."""
        enabled = command == "speech_on"
        if self.speech_enabled.get() != enabled:
            self.speech_enabled.set(enabled)
            self._toggle_speech()
        self._refresh_privacy_status()
        answer = "Leitura em voz ativada." if enabled else "Leitura em voz desativada."
        self._append("Você", utterance, "user")
        self._append("Nexus Core", answer, "assistant")
        self.status.configure(text=answer)
        if not self._say_response(answer):
            self._start_listening()

    def _spoken_voice_selection(self, command: str, utterance: str) -> None:
        """Change only the local TTS choice; preserve microphone and mute state."""
        voice = "Feminina" if command == "voice_female" else "Masculina"
        self.voice_choice.set(voice)
        self._save_desktop_preferences()
        answer = f"Voz {voice.lower()} selecionada."
        self._append("Você", utterance, "user")
        self._append("Nexus Core", answer, "assistant")
        self.status.configure(text=answer)
        if not self._say_response(answer):
            self._start_listening()

    def _toggle_wake(self) -> None:
        if self._closing:
            return
        if self.wake_required.get():
            self.status.configure(text='Diga "Nexus, ..." antes de cada pergunta')
        else:
            self.status.configure(text="Conversa contínua sem palavra de ativação")
        self._save_desktop_preferences()

    def _stop_speaking(self) -> None:
        """Invalidate a superseded TTS worker before its completion event."""
        if self._test_voice_speech_generation == self._speak_generation:
            self._test_voice_speech_generation = None
            live_event("teste", "falhou", source="voz")
        self._speak_generation += 1
        self._speaking = False
        self.speaker.stop()

    def _toggle_speech(self) -> None:
        self._save_desktop_preferences()
        if not self.speech_enabled.get() and self._speaking:
            self._stop_speaking()
            self.status.configure(text="Leitura em voz desativada")
            self._start_listening()

    def _vision_file(self) -> None:
        self._request_vision("file")

    def _vision_screen(self) -> None:
        self._request_vision("screen")

    def _vision_window(self) -> None:
        self._request_vision("window")

    def _vision_camera(self) -> None:
        if self._live_camera is not None:
            self._stop_live_camera()
        else:
            self._start_live_camera()

    def _vision_camera_photo(self) -> None:
        if self._closing or self._busy:
            return
        if self._live_camera is None:
            self._request_vision("camera")
            return
        if self.messagebox.askyesno(
            "Nexus Core — foto da câmera",
            "Usar um quadro da câmera ligada para analisar uma foto no Ollama local? "
            "A imagem não será salva. Esta autorização vale somente para esta análise.",
            parent=self.root,
        ):
            self._ask_live_camera(LocalVision.DEFAULT_PROMPT, still=True)

    def _retry_camera_photo(self) -> None:
        """A new photo requires a new user action and a fresh capture consent."""
        if self._busy:
            self.status.configure(text="Aguarde a análise atual ou cancele antes de tentar novamente")
            return
        self._vision_camera_photo()

    @staticmethod
    def _unclear_browser_command(utterance: str) -> bool:
        """Ask to repeat a likely misheard command; never infer an action."""
        if _simple_app_request(utterance) is not None:
            return False
        plain = unicodedata.normalize("NFKD", utterance).encode(
            "ascii", "ignore").decode("ascii").lower()
        plain = re.sub(r"^nexus[,:]?\s+", "", " ".join(plain.split()))
        return (len(plain.split()) <= 5 and
                re.match(r"^(?:abra|abre|abrir)\b", plain) is not None and
                SequenceMatcher(None, plain, "abrir o navegador").ratio() >= 0.69)

    def _start_live_camera(self) -> None:
        """Authorize one live session; each spoken question selects one frame."""
        if self._closing or self._busy:
            return
        live_event("camera", "solicitado", source="camera_live")
        from tkinter import simpledialog
        devices = LocalVision.cameras()
        if not devices:
            live_event("camera", "falhou", source="camera_live")
            self._vision_notice("Nenhuma câmera local foi encontrada. "
                                + LocalVision.camera_discovery_hint())
            return
        index = devices[0][0]
        if len(devices) > 1:
            choices = "\n".join(f"{number}: {name}" for number, name in devices)
            index = simpledialog.askinteger(
                "Selecionar câmera", f"Câmeras encontradas:\n{choices}\n\nNúmero da câmera:",
                parent=self.root, initialvalue=index, minvalue=0,
                maxvalue=LocalVision.MAX_CAMERA_INDEX,
            )
            if index is None:
                return
            if index not in dict(devices):
                self._vision_notice("A câmera escolhida não está mais disponível.")
                return
        if not self.messagebox.askyesno(
            "Nexus Core — câmera contínua",
            f"Ligar a câmera {index} e mostrar vídeo local até você desligá-la? "
            "Quando você perguntar sobre a câmera, um quadro atual será "
            "enviado somente ao Ollama local. Nenhum vídeo será gravado. "
            "Use 'Feche a câmera' ou o botão para parar.", parent=self.root,
        ) or self._closing:
            live_event("camera", "negado", source="camera_live")
            return
        stream = CameraStream(index)
        try:
            stream.start()
            preview = self.tk.Toplevel(self.root)
            preview.title(f"NEXUS CORE — câmera {index} ao vivo")
            preview.configure(background="#241c24")
            label = self.tk.Label(
                preview, text="Iniciando câmera…", bg="#241c24", fg="white",
                width=80, height=25,
            )
            label.pack(padx=8, pady=8)
            self.tk.Button(preview, text="Desligar câmera",
                           command=self._stop_live_camera).pack(pady=(0, 8))
            self.tk.Button(preview, text="Analisar foto deste vídeo",
                           command=self._vision_camera_photo).pack(pady=(0, 8))
            preview.protocol("WM_DELETE_WINDOW", self._stop_live_camera)
        except VisionError as exc:
            stream.stop()
            live_event("camera", "falhou", source="camera_live")
            self._vision_notice(str(exc))
            return
        except Exception:
            stream.stop()
            live_event("camera", "falhou", source="camera_live")
            self._vision_notice("Não foi possível abrir a prévia da câmera.")
            return
        self._live_camera = stream
        self._live_camera_window = preview
        self._live_camera_label = label
        self._live_camera_sequence = 0
        live_event("camera", "iniciado", source="camera_live")
        self._vision_buttons[3].configure(text="Desligar câmera")
        self._append("Nexus Core", "Abrindo câmera. Aguarde a primeira imagem na prévia.", "assistant")
        self.status.configure(text="Abrindo câmera; aguardando a primeira imagem…")

    def _stop_live_camera(self) -> None:
        stream = self._live_camera
        if stream is None:
            return
        self._live_camera = None
        live_event("camera", "desligado", source="camera_live")
        stream.stop()
        preview = self._live_camera_window
        self._live_camera_window = None
        self._live_camera_label = None
        if preview is not None:
            try:
                preview.destroy()
            except self.tk.TclError:
                pass
        self._vision_buttons[3].configure(text="Câmera ao vivo")
        if self._busy and self._vision_source == "camera_live":
            self._cancel_requested = True
        if not self._closing:
            self.status.configure(text="Câmera desligada")

    @staticmethod
    def _camera_question(text: str) -> bool:
        normalized = unicodedata.normalize("NFKD", text).encode(
            "ascii", "ignore").decode("ascii").lower()
        return bool(re.search(r"\b(?:na camera|pela camera|da camera|no video|"
                              r"voce ve|voce enxerga|esta vendo|consegue ver|"
                              r"aparece|visivel|mostrando|o que tem ai|"
                              r"o que estou segurando|na minha mao|nas minhas maos|"
                              r"quantos dedos|que cor e isso)\b", normalized))

    def _ask_live_camera(self, question: str, *, still: bool = False) -> None:
        stream = self._live_camera
        if stream is None or self._busy or self._closing:
            return
        _, frame, error = stream.latest(max_age=3.0)
        if error or frame is None:
            self._vision_notice(error or "A câmera ainda está iniciando. Pergunte novamente em instantes.")
            return
        try:
            question = LocalVision.validate_question(question)
        except VisionInputError:
            self._vision_notice("Pergunta visual inválida (máximo 2000 caracteres).")
            return
        if still:
            self._camera_frames.put(("camera", frame))
        self._append("Você", f"[{'Foto da câmera' if still else 'Câmera ao vivo'}] {question}", "user")
        self._busy = True
        self._operation_kind = "vision"
        self._vision_source = "camera_live"
        self._operation_started = monotonic()
        self._last_progress_interval = 0
        live_event("visao", "iniciado", source="camera_live")
        self._cancel_requested = False
        self.send_button.configure(state="disabled")
        self.suggest_button.configure(state="disabled")
        self.cancel_button.configure(state="normal")
        for button in self._vision_buttons[:3]:
            button.configure(state="disabled")
        if self._listening:
            self._listen_generation += 1
            self.recognizer.stop()
        if self._speaking:
            self._stop_speaking()
        self.status.configure(text="Analisando quadro atual no Ollama local…")
        self._start_worker(self._describe_live_frame, frame, question)

    def _describe_live_frame(self, frame: bytes, question: str) -> None:
        try:
            if self._cancel_requested or self._closing:
                raise VisionError("Análise cancelada.")
            service = self.vision if self.vision is not None else LocalVision(settings)
            result = self._describe_authorized_image(service, frame, question)
            description = result.get("description") if isinstance(result, dict) else None
            if not isinstance(description, str) or not description.strip():
                raise VisionError("Resposta visual local inválida.")
            self._vision_events.put(("success", question, description[:12000]))
        except VisionError as exc:
            self._vision_events.put(("error", question, str(exc)))
        except Exception:
            self._vision_events.put(("error", question, "Falha ao analisar quadro local."))

    def _shortcut_vision_file(self, event=None):
        self._vision_file()
        return "break"

    def _shortcut_vision_screen(self, event=None):
        self._vision_screen()
        return "break"

    def _shortcut_vision_camera(self, event=None):
        self._vision_camera()
        return "break"

    def _shortcut_camera_photo(self, event=None):
        self._vision_camera_photo()
        return "break"

    def _request_vision(self, source: str) -> None:
        """Capture once only following user action and explicit per-shot consent."""
        if self._closing or self._busy or source not in ("file", "screen", "display", "window", "camera"):
            return
        from tkinter import filedialog, simpledialog

        selection = None
        label = {"file": "imagem selecionada", "screen": "tela atual",
                 "display": "monitor selecionado", "window": "janela selecionada",
                 "camera": "câmera"}[source]
        if source == "file":
            selection = filedialog.askopenfilename(
                parent=self.root,
                title="Escolha uma imagem (PNG, JPG, WEBP, GIF, BMP, TIFF, AVIF)",
                initialdir=str(image_start_directory()),
                # Every format has a readable entry, not an incomprehensible
                # truncated list of glob patterns. File validation follows.
                filetypes=image_filetypes(),
            )
            if not selection:
                return
        elif source == "camera":
            devices = LocalVision.cameras()
            if not devices:
                self._vision_notice("Nenhuma câmera local foi encontrada. "
                                    + LocalVision.camera_discovery_hint())
                return
            if len(devices) == 1:
                selection = devices[0][0]
            else:
                choices = "\n".join(f"{index}: {name}" for index, name in devices)
                selection = simpledialog.askinteger(
                    "Selecionar câmera", f"Câmeras encontradas:\n{choices}\n\nNúmero da câmera:",
                    parent=self.root, initialvalue=devices[0][0], minvalue=0,
                    maxvalue=LocalVision.MAX_CAMERA_INDEX,
                )
                if selection is None:
                    return
                if selection not in dict(devices):
                    self._vision_notice("A câmera escolhida não está mais disponível.")
                    return
            label = f"câmera {selection}"
        elif source in ("screen", "window") and os.environ.get("WAYLAND_DISPLAY"):
            label = "janela selecionada pelo portal"
        # The Camera button is a direct request to open a camera. Use a
        # useful default question so it does not stall behind a text dialog.
        question = (LocalVision.DEFAULT_PROMPT if source == "camera" else
                    simpledialog.askstring(
                        "Pergunta sobre a imagem", "Qual pergunta deseja fazer ao modelo visual?",
                        parent=self.root, initialvalue=LocalVision.DEFAULT_PROMPT,
                    ))
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
            live_event("visao", "negado", source=source)
            return
        self._busy = True
        self._operation_kind = "vision"
        self._operation_started = monotonic()
        self._last_progress_interval = 0
        self._vision_source = source
        live_event("visao", "iniciado", source=source)
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

    def _vision_notice(self, message: str) -> None:
        self._append("Nexus Core", message, "assistant")
        self.status.configure(text=message[:90])
        if self._listening:
            self._listen_generation += 1
            self.recognizer.stop()
        if not self._say_response(message):
            self._start_listening()

    def _show_camera_frame(self, frame: bytes, source: str = "camera") -> None:
        """Show the one-shot image selected with explicit user authorization.

        This is not a live stream and does not persist captured pixels.
        Preview works for file imports, screen screenshots and webcams.
        """
        try:
            from PIL import Image, ImageTk
            with Image.open(io.BytesIO(frame)) as raw:
                picture = raw.copy()
            picture.thumbnail((660, 420))
            photo = ImageTk.PhotoImage(picture, master=self.root)
        except (ImportError, OSError, ValueError):
            return
        if self._camera_preview is not None:
            try:
                self._camera_preview.destroy()
            except self.tk.TclError:
                pass
        label = {
            "file": "imagem importada", "camera": "foto da câmera",
            "screen": "tela capturada", "display": "monitor capturado",
            "window": "janela selecionada",
        }.get(source, "imagem autorizada")
        preview = self.tk.Toplevel(self.root)
        preview.title(f"NEXUS CORE — prévia de {label}")
        preview.configure(background="#f5f1f3")
        title = self.tk.Label(
            preview, text=f"Prévia: {label}",
            font=("Sans", 12, "bold"), fg="#722F37", bg="#f5f1f3",
        )
        title.pack(padx=12, pady=(12, 5))
        holder = self.tk.Label(preview, image=photo, bd=0)
        holder.image = photo
        holder.pack(padx=12, pady=8)
        self.tk.Label(
            preview, text="Captura única autorizada. Análise no Ollama local em andamento.",
            bg="#f5f1f3", fg="#503943",
        ).pack(pady=(0, 5))
        if source in ("camera", "camera_live"):
            self.tk.Button(
                preview, text="Tentar novamente",
                command=self._retry_camera_photo,
            ).pack(pady=(4, 5))
        self.tk.Button(
            preview, text="Fechar prévia", command=preview.destroy,
        ).pack(pady=(4, 12))
        self._camera_preview = preview

    def _analyze_vision(self, source: str, selection, question: str) -> None:
        """Worker only: never touch Tk from this thread or persist image bytes."""
        try:
            if self._cancel_requested or self._closing:
                raise VisionError("Análise cancelada.")
            service = self.vision if self.vision is not None else LocalVision(settings)
            if source == "file":
                image = service.image_from_file(selection)
            elif source == "camera":
                image = service.camera(selection)
            elif source == "window":
                image = service.selected_screen(window=True)
            elif source == "display":
                image = service.selected_screen(window=False)
            else:
                image = service.screen()
            # Portal selection and hardware capture can take seconds. If the
            # user cancelled meanwhile, do not preview or send the frame.
            if self._cancel_requested or self._closing:
                raise VisionError("Análise cancelada.")
            # Only user-authorized captures reach the GUI preview queue.
            # No image is retained in the conversation history.
            self._camera_frames.put((source, image))
            result = self._describe_authorized_image(service, image, question)
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

    def _describe_authorized_image(self, service, image: bytes, question: str) -> dict:
        """Check cancellation during preparation in the built-in vision engine."""
        if isinstance(service, LocalVision):
            return service.describe(
                image, question=question,
                is_cancelled=lambda: self._cancel_requested or self._closing,
            )
        return service.describe(image, question=question)

    def _listen(self, generation: int) -> None:
        try:
            cancelled = (lambda: self._closing or self._busy or not self._voice_active
                         or generation != self._listen_generation)
            if isinstance(self.recognizer, LocalRecognizer):
                text = self.recognizer.recognize_continuous(
                    cancelled, on_audio_level=lambda level: self._audio_events.put(
                        ("input_level", str(level), generation)
                    ),
                )
            else:
                text = self.recognizer.recognize_continuous(cancelled)
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
            if type(self.speaker) is LocalSpeaker:
                # The real eSpeak process must recheck after Popen: stop()
                # can race with process registration. Injected speakers keep
                # their original two-argument interface.
                self.speaker.speak(
                    text, voice,
                    cancelled=lambda: self._closing or generation != self._speak_generation,
                )
            else:
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
        live_event("autorizacao", "solicitado", tool=request.tool_name)
        details = [
            f"Função Nexus Core: {action_label(request.tool_name or '')}",
            f"Ação: {self._display(request.description)}",
            f"Risco: {request.risk_level.name}",
        ]
        if isinstance(request.data, dict) and "command" in request.data:
            details.append(f"Comando: {self._display(request.data['command'])}")
        if request.tool_name == "pdf_extract_pages_local" and isinstance(request.data, dict):
            details.append(f"Páginas solicitadas: {self._display(request.data.get('pages', ''))}")
        if request.tool_name == "pdf_organize_local" and isinstance(request.data, dict):
            data = request.data
            action = "Girar" if data.get("operation") == "rotate" else "Mover"
            unit = "graus" if data.get("operation") == "rotate" else "posição"
            details.append(f"{action} páginas: {self._display(data.get('pages', ''))}; "
                           f"{self._display(data.get('value', ''))} {unit}")
        if request.tool_name == "launch_application" and isinstance(request.data, dict):
            details.append(f"Aplicativo: {self._display(request.data.get('application', ''))}")
        if request.tool_name == "desktop_type_text" and isinstance(request.data, dict):
            # Display the exact target and bounded text before user consent.
            details.append(
                f"Janela X11: {self._display(request.data.get('window_title', ''))}"
                f" (ID {self._display(request.data.get('window_id', ''))})"
            )
            details.append(
                f"Texto a digitar (não envia Enter): "
                f"{self._display(request.data.get('text', ''))}"
            )
        if request.tool_name == "desktop_navigate" and isinstance(request.data, dict):
            # A precise one-shot navigation preview, never a generic shortcut.
            details.append(
                f"Janela X11: {self._display(request.data.get('window_title', ''))}"
                f" (ID {self._display(request.data.get('window_id', ''))})"
            )
            details.append(
                f"Navegação (uma tecla): {self._display(request.data.get('action', ''))}"
            )
        if request.tool_name in ("desktop_type_text", "desktop_navigate") and isinstance(request.data, dict):
            details.append(
                f"Identidade X11: PID {self._display(request.data.get('window_pid', ''))}"
                f", classe {self._display(request.data.get('window_class', ''))}"
            )
        for resource in request.resources:
            details.append(
                f"{resource_label(resource.name)}: {self._display(resource.path)}"
            )
        details.append("\nEsta autorização vale somente para a ação acima.")
        dialog = PermissionDialog(
            self.root, "\n".join(details), recognizer=self.recognizer,
            listen=self._voice_active,
            ready_to_listen=lambda: not self._listening and not self._listen_pending_generations,
            start_worker=self._start_worker,
            cancelled=lambda: self._closing or self._cancel_requested,
            speaker=self.speaker if self.speech_enabled.get() else None,
            voice=self.voice_choice.get(),
            spoken_question=(
                "Nexus Core precisa da sua autorização para: "
                f"{' '.join(str(request.description).split())[:140]}. "
                "Confira a ação, o alvo e o risco na janela. "
                + (
                    "Você pode usar os botões, digitar sua decisão ou dizer: "
                    "Nexus, autorizo esta ação; ou Nexus, nego esta ação."
                    if self._voice_active else
                    "Use os botões ou digite sua decisão; a escuta está pausada."
                )
            ),
        )
        self._permission_dialog = dialog
        try:
            approved = dialog.ask()
            live_event("autorizacao", "aprovado" if approved else "negado",
                       tool=request.tool_name)
            return approved
        except Exception:
            live_event("autorizacao", "falhou", tool=request.tool_name)
            raise
        finally:
            self._permission_dialog = None

    def _set_network_status(self, state: str) -> None:
        if self._network_state == state:
            return
        presentation = {
            "online": ("● ONLINE", "Nexus.NetworkOnline.TLabel", "online"),
            "offline": ("● OFFLINE", "Nexus.NetworkOffline.TLabel", "offline"),
            "unknown": ("● NÃO VERIFICADO", "Nexus.NetworkUnknown.TLabel", "nao_verificado"),
        }
        label, style, event_state = presentation.get(state, presentation["unknown"])
        self._network_state = state if state in presentation else "unknown"
        self.network_badge.configure(text=label, style=style)
        live_event("rede", event_state)

    def _refresh_network_status(self) -> None:
        try:
            while True:
                self._set_network_status(self._network_events.get_nowait())
        except Empty:
            pass
        if getattr(self.app, "connectivity_monitor", None) is not None:
            try:
                snapshot = self.app.status().runtime_snapshot()
                self._set_network_status("online" if snapshot.network_online else "offline")
            except (AttributeError, RuntimeError):
                self._set_network_status("unknown")

    def _poll(self) -> None:
        self._refresh_network_status()
        self._refresh_activity_badge()
        # Prune completed workers on every GUI tick; otherwise a long-running
        # voice conversation would retain every prior thread indefinitely.
        self._workers_running()
        # A stalled input stream must not leave an illuminated microphone.
        if self._mic_last_signal and monotonic() - self._mic_last_signal > 1.4:
            self.microphone_indicator.show_peak(0, listening=False)
            self._mic_last_signal = 0.0
        if self._busy and not self._cancel_requested:
            elapsed = int(monotonic() - self._operation_started)
            if elapsed >= 10:
                self.status.configure(text=f"Ollama processando há {elapsed} s · Cancelar disponível")
                interval = elapsed // 10
                if interval > self._last_progress_interval:
                    self._last_progress_interval = interval
                    if self._operation_kind == "chat":
                        live_event("chat", "processando", source=self._chat_source,
                                   elapsed_ms=elapsed * 1000)
                    elif self._operation_kind == "vision":
                        live_event("visao", "processando", source=self._vision_source,
                                   elapsed_ms=elapsed * 1000)
        self.confirmation.process(self._confirm)
        stream = self._live_camera
        if stream is not None:
            sequence, frame, error = stream.latest()
            if error:
                self._stop_live_camera()
                self._vision_notice(error)
            elif frame is not None and sequence != self._live_camera_sequence:
                first_frame = self._live_camera_sequence == 0
                self._live_camera_sequence = sequence
                try:
                    from PIL import Image, ImageTk
                    with Image.open(io.BytesIO(frame)) as original:
                        picture = original.copy()
                    picture.thumbnail((640, 480))
                    photo = ImageTk.PhotoImage(picture, master=self._live_camera_window)
                    self._live_camera_label.configure(image=photo, text="", width=0, height=0)
                    self._live_camera_label.image = photo
                    if first_frame:
                        live_event("camera", "pronto", source="camera_live")
                        self.status.configure(text="Câmera ao vivo pronta · pergunte sobre o vídeo")
                except (ImportError, OSError, ValueError, self.tk.TclError):
                    self._stop_live_camera()
                    self._vision_notice("Não foi possível exibir o vídeo local da câmera.")
        while True:
            try:
                kind, value, generation = self._audio_events.get_nowait()
            except Empty:
                break
            if kind == "input_level":
                if (generation == self._listen_generation and self._listening
                        and not self._closing):
                    self._audio_level_samples += 1
                    level = max(0, min(100, int(value)))
                    if level >= 2 and self._audio_peaks < 2:
                        live_event("escuta", "recebido", source="voz")
                    self._audio_peaks = max(self._audio_peaks, level)
                    self._mic_last_signal = monotonic()
                    self.microphone_indicator.show_peak(level, listening=self._voice_active)
                    self._audio_level_label.configure(text=f"Entrada: {level}%")
                    if level >= 2:
                        self.status.configure(text=f"Áudio {level}% captado; aguardando transcrição Vosk…")
                    elif self._audio_level_samples >= 4 and self._audio_peaks < 2:
                        self.status.configure(text="Microfone sem sinal; confira a entrada de áudio")
                continue
            if kind in ("transcript", "silence", "listen_error"):
                if generation not in self._listen_pending_generations:
                    continue
                self._listen_pending_generations.discard(generation)
                self._listening = False
                self.microphone_indicator.show_peak(0, listening=False)
                self._mic_last_signal = 0.0
                self._audio_level_label.configure(text="Entrada: aguardando")
                if self._closing:
                    continue
                if generation != self._listen_generation:
                    self._start_listening()
                    continue
                if kind == "transcript" and value:
                    live_event("reconhecimento", "concluido", source="voz",
                               elapsed_ms=int((monotonic() - self._listen_started) * 1000))
                elif kind == "silence":
                    live_event("reconhecimento", "sem_transcricao" if self._audio_peaks >= 2 else "sem_sinal",
                               source="voz", elapsed_ms=int((monotonic() - self._listen_started) * 1000),
                               peak_percent=self._audio_peaks, samples=self._audio_level_samples)
                if kind == "listen_error":
                    live_event("reconhecimento", "falhou", source="voz")
                    transient = (
                        "capturar áudio" in value
                        or "Fluxo de áudio interrompido" in value
                        or "iniciar a gravação" in value
                    )
                    if (transient and self._voice_active and not self._busy
                            and self._listen_retries < 2):
                        self._listen_retries += 1
                        self.status.configure(
                            text="Reconectando o microfone local "
                                 f"({self._listen_retries}/2)…"
                        )
                        self.root.after(450, self._start_listening)
                    else:
                        self._voice_active = False
                        self.mic_button.configure(text="Retomar escuta")
                        self.status.configure(text=value)
                        self._append(
                            "Nexus Core", f"Escuta indisponível: {value} "
                            "Teste PipeWire ou ALSA no seletor de microfone; "
                            "a conversa por texto continua disponível.", "assistant",
                        )
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
                    elif command == "privacy_status":
                        self._answer_privacy_status(utterance)
                    elif command in ("speech_on", "speech_off"):
                        self._spoken_speech_control(command, utterance)
                    elif command in ("voice_female", "voice_male"):
                        self._spoken_voice_selection(command, utterance)
                    elif command == "camera_off":
                        self._stop_live_camera()
                        self._start_listening()
                    elif command == "camera_photo":
                        self._vision_camera_photo()
                        if not self._busy:
                            self._start_listening()
                    elif command in ("camera_on", "vision_camera"):
                        if self._live_camera is None:
                            if command == "vision_camera":
                                self._vision_camera_photo()
                            else:
                                self._start_live_camera()
                        elif command == "vision_camera":
                            self._ask_live_camera(LocalVision.DEFAULT_PROMPT)
                        if not self._busy:
                            self._start_listening()
                    elif command in ("vision_file", "vision_screen", "vision_display", "vision_window"):
                        self._request_vision(command.removeprefix("vision_"))
                        # Selection or consent may be cancelled. Only then
                        # resume listening; a running analysis will resume it.
                        if not self._busy:
                            self._start_listening()
                    elif kind == "transcript" and utterance:
                        self._listen_retries = 0
                        self._recognition_failures = 0
                        if self._unclear_browser_command(utterance):
                            self._append("Você", utterance, "user")
                            note = ("Não entendi o comando com segurança. "
                                    "Se deseja abrir o navegador padrão, diga: "
                                    "Nexus, abra o navegador. Você também pode digitar o pedido.")
                            self._append("Nexus Core", note, "assistant")
                            self.status.configure(text="Comando impreciso; repita ou digite")
                            if not self._say_response(note):
                                self._start_listening()
                        elif self._live_camera is not None and self._camera_question(utterance):
                            self._ask_live_camera(utterance)
                        else:
                            if self._test_voice_turns_remaining > 0:
                                self._test_voice_reply_pending = True
                            self.input.delete("1.0", "end")
                            self.input.insert("1.0", utterance)
                            self._send(channel="voz")
                    else:
                        if kind == "silence":
                            self._recognition_failures += 1
                            if self._recognition_failures == 2:
                                if self._audio_peaks >= 2:
                                    note = (
                                        "O microfone recebeu áudio, mas o Vosk não "
                                        "transcreveu na janela. Teste uma frase no "
                                        "--recognition-test e experimente ALSA no "
                                        "seletor de microfone; confira a entrada "
                                        "padrão e seu volume no Ubuntu."
                                    )
                                else:
                                    note = (
                                        "A captura está sem sinal. Verifique a "
                                        "entrada do Ubuntu ou alterne entre "
                                        "Automático, PipeWire e ALSA."
                                    )
                                self._append("Nexus Core", note, "assistant")
                        self._start_listening()
            elif kind in ("speak_done", "speak_error"):
                # A cancelled/disabled older voice must not clobber new TTS.
                if generation != self._speak_generation:
                    continue
                self._speaking = False
                live_event("fala", "concluido" if kind == "speak_done" else "falhou",
                           elapsed_ms=int((monotonic() - self._speak_started) * 1000))
                if not self._closing and not self._busy:
                    if kind == "speak_error" and self.speech_enabled.get():
                        self.status.configure(text=value)
                        if generation == self._startup_welcome_generation:
                            # TTS cannot fail silently: keep textual access.
                            self._append(
                                "Nexus Core",
                                f"Não foi possível falar as boas-vindas: {value} "
                                "Você pode continuar usando a conversa por texto.",
                                "assistant",
                            )
                    if generation == self._startup_welcome_generation:
                        self._startup_welcome_generation = None
                    self._start_listening()
                    if generation == self._test_voice_speech_generation:
                        self._test_voice_speech_generation = None
                        if kind == "speak_done" and self._listening and self._voice_active:
                            self._test_voice_turns_remaining -= 1
                            live_event(
                                "teste",
                                ("concluido" if self._test_voice_turns_remaining == 0
                                 else "recebido"), source="voz",
                            )
                        else:
                            live_event("teste", "falhou", source="voz")
        while True:
            try:
                reply = self._replies.get_nowait()
            except Empty:
                break
            cancelled = self._cancel_requested
            if not self._closing:
                elapsed_ms = int((monotonic() - self._operation_started) * 1000)
                live_event("chat", "cancelado" if cancelled or reply.outcome.error_code == "CANCELLED"
                           else "concluido" if reply.outcome.success else "falhou",
                           source=self._chat_source, elapsed_ms=elapsed_ms)
                if reply.outcome.tool_result is not None:
                    tool_result = reply.outcome.tool_result
                    live_event("ferramenta", "concluido" if tool_result.success else "falhou",
                               tool=tool_result.tool_name)
                self._finish_operation()
                if cancelled or reply.outcome.error_code == "CANCELLED":
                    self._test_voice_reply_pending = False
                    self._append("Nexus Core", "Solicitação cancelada.", "assistant")
                    self.status.configure(text="Solicitação cancelada")
                    self._start_listening()
                else:
                    self._append("Nexus Core", reply.text, "assistant")
                    if reply.outcome.tool_result is not None:
                        self._remember_created_image(reply.outcome.tool_result)
                    self.status.configure(
                        text=(self.session.last_archive_error
                              or ("Escuta pausada" if not self._voice_active
                                  else "Pronto para conversar"))
                    )
                    spoken = (reply.outcome.success or
                              reply.outcome.error_code == "RESOURCE_PRESSURE") and self._say_response(reply.text)
                    if self._test_voice_reply_pending:
                        self._test_voice_reply_pending = False
                        if spoken:
                            self._test_voice_speech_generation = self._speak_generation
                        else:
                            live_event("teste", "falhou", source="voz")
                    if not spoken:
                        self._start_listening()
            else:
                self._busy = False
        while True:
            try:
                frame = self._camera_frames.get_nowait()
            except Empty:
                break
            if not self._closing and not self._cancel_requested:
                if isinstance(frame, tuple) and len(frame) == 2:
                    self._show_camera_frame(frame[1], frame[0])
                else:
                    self._show_camera_frame(frame)
        while True:
            try:
                kind, question, result = self._vision_events.get_nowait()
            except Empty:
                break
            cancelled = self._cancel_requested
            if self._closing:
                self._busy = False
                continue
            live_event("visao", "cancelado" if cancelled else "concluido" if kind == "success" else "falhou",
                       source=self._vision_source,
                       elapsed_ms=int((monotonic() - self._operation_started) * 1000))
            self._finish_operation()
            if cancelled:
                self._append("Nexus Core", "Análise visual cancelada.", "assistant")
                self.status.configure(text="Análise visual cancelada")
                self._start_listening()
            elif kind == "success":
                # Show natural Portuguese rather than raw Markdown markers.
                natural = readable_model_text(result) or result
                self.session.note_visual(question, natural)
                self._append("Nexus Core", natural, "assistant")
                self.status.configure(text="Análise visual concluída")
                # File, screen and camera all use the same voice output path.
                if not self._say_response(natural):
                    self._start_listening()
            else:
                self._vision_notice(f"Análise visual indisponível: {result}")
        if (self._closing and not self._busy and not self._listening
                and not self._speaking and not self._workers_running()):
            self._finish_close()
            return
        self._refresh_privacy_status()
        self.root.after(80, self._poll)

    def _close(self) -> None:
        if self._closing:
            return
        if self._network_watcher is not None:
            self._network_watcher.stop()
        live_event("interface", "desligado")
        self._save_desktop_preferences()
        self._closing = True
        self._refresh_activity_badge()
        self._audio_level_label.configure(text="Entrada: desligada")
        self.microphone_indicator.show_peak(0, listening=False)
        self._mic_last_signal = 0.0
        # The original photo asset must be released on the Tk thread even
        # when tests or users destroy the root before audio workers exit.
        self._brand_image = None
        self._close_created_image()
        self._created_image_path = None
        if self._camera_preview is not None:
            self._camera_preview.destroy()
            self._camera_preview = None
        self._stop_live_camera()
        self._voice_active = False
        self._listen_generation += 1
        self.session.close()
        self.confirmation.close()
        if self._permission_dialog is not None:
            self._permission_dialog._finish(False)
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
