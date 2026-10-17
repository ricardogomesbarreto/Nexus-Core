"""Structured live desktop events safe to copy from the terminal.

Only fixed categories are accepted. Never forward model output, microphone
transcripts, paths, window titles, camera frames or arbitrary exceptions.
"""

import logging


EVENTS = frozenset({
    "interface", "chat", "escuta", "reconhecimento", "fala",
    "camera", "visao", "autorizacao", "ferramenta", "cancelamento",
})
STATES = frozenset({
    "iniciado", "concluido", "falhou", "pausado", "retomado",
    "solicitado", "aprovado", "negado", "cancelado", "pronto",
    "desligado", "sem_sinal", "sem_transcricao", "recebido", "processando",
})
SOURCES = frozenset({
    "texto", "voz", "file", "screen", "display", "window",
    "camera", "camera_live",
})
TOOLS = frozenset({
    "create_directory", "launch_application", "desktop_type_text",
    "desktop_navigate", "terminal_sandbox", "system_info",
})


def live_event(event: str, state: str, *, source: str | None = None,
               tool: str | None = None, elapsed_ms: int | None = None) -> None:
    """Emit a single bounded status via the existing console/file logger."""
    if event not in EVENTS or state not in STATES:
        raise ValueError("Evento de execução inválido")
    fields = [f"evento={event}", f"estado={state}"]
    if source is not None:
        fields.append(f"origem={source if source in SOURCES else 'outra'}")
    if tool is not None:
        fields.append(f"ferramenta={tool if tool in TOOLS else 'outra'}")
    if elapsed_ms is not None:
        if type(elapsed_ms) is not int:
            raise ValueError("Duração inválida")
        fields.append(f"duracao_ms={max(0, min(elapsed_ms, 3_600_000))}")
    logging.getLogger("nexus.desktop_runtime").info("TESTE-LOCAL %s", " ".join(fields))
