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
