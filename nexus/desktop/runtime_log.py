"""Structured live desktop events safe to copy from the terminal.

Only fixed categories are accepted. Never forward model output, microphone
transcripts, paths, window titles, camera frames or arbitrary exceptions.
"""

import logging


EVENTS = frozenset({
    "interface", "chat", "escuta", "reconhecimento", "fala",
    "camera", "visao", "autorizacao", "ferramenta", "cancelamento",
    "teste", "recurso", "rede",
})
STATES = frozenset({
    "iniciado", "concluido", "falhou", "pausado", "retomado",
    "solicitado", "aprovado", "negado", "cancelado", "pronto",
    "desligado", "sem_sinal", "sem_transcricao", "recebido", "processando",
    "online", "offline", "nao_verificado",
})
SOURCES = frozenset({
    "texto", "voz", "file", "screen", "display", "window",
    "camera", "camera_live",
})
TOOLS = frozenset({
    "create_directory", "launch_application", "open_default_browser", "desktop_type_text",
    "desktop_navigate", "terminal_sandbox", "system_info",
    "edit_image_local", "image_geometry_local", "create_graphic_local", "craft_convert_local",
    "pdf_extract_pages_local",
})
PROFILES = frozenset({"eco", "balanced"})



def live_event(event: str, state: str, *, source: str | None = None,
               tool: str | None = None, elapsed_ms: int | None = None,
               profile: str | None = None, threads: int | None = None,
               memory_mib: int | None = None, peak_percent: int | None = None,
               samples: int | None = None) -> None:
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
    if profile is not None:
        fields.append(f"perfil={profile if profile in PROFILES else 'outra'}")
    if threads is not None:
        if type(threads) is not int:
            raise ValueError("Quantidade de threads inválida")
        fields.append(f"threads={max(1, min(threads, 64))}")
    if memory_mib is not None:
        if type(memory_mib) is not int:
            raise ValueError("Quantidade de memória inválida")
        fields.append(f"ram_disponivel_mib={max(0, min(memory_mib, 1_000_000))}")
    if peak_percent is not None or samples is not None:
        if event != "reconhecimento" or type(peak_percent) is not int or type(samples) is not int:
            raise ValueError("Métricas de áudio inválidas")
        fields.append(f"pico={max(0, min(peak_percent, 100))}%")
        fields.append(f"amostras={max(0, min(samples, 1_000_000))}")
    logging.getLogger("nexus.desktop_runtime").info("TESTE-LOCAL %s", " ".join(fields))
