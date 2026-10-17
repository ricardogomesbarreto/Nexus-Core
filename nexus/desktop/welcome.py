"""Honest, friendly welcome for the local-first Nexus Core desktop.

Application initialization confirms only the local services that report their
state. It cannot certify microphones, cameras, Vosk transcription, Ollama model
inference, or audio playback without explicit real-device checks.
"""


def desktop_startup_message(app) -> tuple[str, str]:
    """Return (welcome message, compact readiness caption), without I/O."""
    health = None
    status = getattr(app, "status", None)
    if callable(status):
        try:
            health = status()
        except Exception:
            # A welcome must not crash the desktop or conceal runtime errors.
            health = None

    database_ready = getattr(health, "database", False) is True
    if database_ready:
        message = (
            "Bem-vindo ao NEXUS CORE!\n\n"
            "O aplicativo iniciou e o PostgreSQL local está inicializado. "
            "Sua conversa e as ferramentas autorizadas estão disponíveis na janela. "
            "O funcionamento do modelo Ollama, da transcrição Vosk, da câmera e "
            "da saída de voz depende de verificação real no computador.\n\n"
            "Escreva uma pergunta ou utilize os controles de voz e visão. "
            "Ações no computador continuam sujeitas às permissões e confirmações."
        )
        caption = "Aplicativo iniciado  •  PostgreSQL local pronto  •  Mídia a verificar"
    else:
        message = (
            "Bem-vindo ao NEXUS CORE!\n\n"
            "A interface foi aberta. A prontidão dos serviços locais ainda "
            "não foi confirmada nesta janela; não é possível afirmar que "
            "todos os recursos estejam funcionando.\n\n"
            "Use a conversa e os controles disponíveis. Ferramentas que "
            "interagem com o computador exigem as autorizações aplicáveis."
        )
        caption = "Interface iniciada  •  Serviços e dispositivos a verificar"
    return message, caption


def desktop_spoken_welcome(name: str | None = None) -> str:
    """Greet briefly so the microphone can start listening sooner.

    Linux account information is only read locally. The detailed operational
    caveats remain in the written welcome, rather than holding the microphone
    for a long spoken introduction.
    """
    if name is None:
        try:
            import os
            import pwd
            account = pwd.getpwuid(os.getuid())
            name = account.pw_gecos.partition(",")[0].strip() or account.pw_name
        except (KeyError, OSError, ImportError):
            name = ""
    # Treat display names as text, never markup or voice-engine instructions.
    if not isinstance(name, str):
        name = ""
    name = " ".join(name.split())
    # Spoken greeting uses only the first name, never the full GECOS field.
    # Reject markup, shell-like tokens and unusually long account labels.
    if (len(name) > 120 or not name or
            any(not (character.isalpha() or character in " '-") for character in name)):
        name = ""
    else:
        name = name.split(" ", 1)[0]
        if len(name) > 40 or not any(character.isalpha() for character in name):
            name = ""
    return f"Bem-vindo ao Nexus Core{', ' + name if name else ''}."
