"""Render model Markdown into natural, local voice narration.

No dependency on network, NLP service or image capture. The original text
is kept separately for the chat and ephemeral conversation context.
"""

import html
import re

MAX_SPOKEN_CHARACTERS = 2600

_FENCE = re.compile(r"(?ms)^[ \t]*```[^\n]*\n.*?^[ \t]*```[ \t]*$")
_LINK = re.compile(r"!?\[([^\]\n]{1,200})\]\((?:[^\s)]|%[0-9A-Fa-f]{2}){1,2048}\)")
_INLINE_CODE = re.compile(r"`([^`\n]{1,240})`")
_HEADINGS = re.compile(r"(?m)^\s{0,3}#{1,6}\s+")
_BULLETS = re.compile(r"(?m)^\s{0,3}[-*+]\s+(?:\[[xX ]\]\s*)?")
_RULES = re.compile(r"(?m)^\s*(?:[-*_]\s*){3,}$")
_MARKER = re.compile(r"(?<!\w)(\*\*|__|~~)(?=\S)|(?<=\S)(\*\*|__|~~)(?!\w)")
_EMPHASIS = re.compile(r"(?<!\w)[*_](?=[\wÀ-ÿ])|(?<=[\wÀ-ÿ])[*_](?!\w)")


def readable_model_text(text: str) -> str:
    """Remove presentation markup but keep actual facts and paragraph breaks."""
    if not isinstance(text, str):
        return ""
    result = html.unescape(text.replace("\r\n", "\n").replace("\r", "\n"))
    result = _FENCE.sub("Há um trecho de código na conversa.", result)
    result = _LINK.sub(lambda match: match.group(1), result)
    result = _INLINE_CODE.sub(lambda match: match.group(1), result)
    result = _RULES.sub("", result)
    result = _HEADINGS.sub("", result)
    result = _BULLETS.sub("", result)
    result = _MARKER.sub("", result)
    result = _EMPHASIS.sub("", result)
    # Some local multimodal models emit entire sequences of separators.
    result = re.sub(r"\*{2,}", "", result)
    result = re.sub(r"(?m)[ \t]+$", "", result)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def speech_from_model_text(text: str, *, max_characters: int = MAX_SPOKEN_CHARACTERS) -> str:
    """Short, punctuation-aware speech; never pronounce Markdown tokens."""
    if type(max_characters) is not int or not 120 <= max_characters <= MAX_SPOKEN_CHARACTERS:
        raise ValueError("Limite de voz inválido.")
    clean = readable_model_text(text)
    if not clean:
        return ""
    # Preserve sentence stops between lines, without reading list symbols.
    parts = []
    for line in clean.splitlines():
        line = " ".join(line.split())
        if not line:
            continue
        if parts and parts[-1][-1:] not in ".!?;:":
            parts[-1] += "."
        parts.append(line)
    spoken = " ".join(parts)
    spoken = re.sub(r"\s{2,}", " ", spoken)
    if len(spoken) > max_characters:
        cut = spoken[:max_characters].rfind(" ")
        spoken = spoken[:cut if cut >= max_characters // 2 else max_characters]
        spoken = spoken.rstrip(" ,;:") + ". Consulte o restante na conversa."
    return spoken.strip()
