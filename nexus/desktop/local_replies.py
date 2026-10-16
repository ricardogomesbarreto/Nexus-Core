"""Small deterministic answers that do not require Ollama or computer tools.

Only strictly matched, read-only questions are answered locally. User command
requests still use the existing SecurityGate and planner.
"""

from datetime import datetime
import re
import unicodedata


def _normalize_question(message: str) -> str:
    normalized = unicodedata.normalize("NFKD", message).encode(
        "ascii", "ignore"
    ).decode("ascii").lower().strip()
    return re.sub(r"\\s+", " ", normalized).rstrip(" ?!.")


def local_conversation_answer(message: str, *, now: datetime | None = None) -> str | None:
    if not isinstance(message, str):
        return None
    question = _normalize_question(message)
    current = now if now is not None else datetime.now().astimezone()
    if question in {
        "que horas sao", "qual e a hora", "que horas sao agora",
        "me diga as horas", "qual horario agora", "qual e o horario agora",
    }:
        return f"Agora são {current:%H:%M}, no horário local deste computador."
    if question in {
        "que dia e hoje", "qual e a data de hoje", "qual a data de hoje",
        "qual e a data atual",
    }:
        return f"Hoje é {current:%d/%m/%Y}, conforme a data deste computador."
    return None
