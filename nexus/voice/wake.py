"""Offline optional activation phrase for Vosk speech transcription.

This is NOT a dedicated low-power keyword detector. The speech recognizer
remains active while listening and completes a local transcription first.
"""
import re
import unicodedata


# Match at the start of an utterance only, never within a quoted sentence.
# Keep the literal text of the request to preserve original language/accent.
_ACTIVATION = re.compile(r"^\s*(?:(?:ei|ola|hey)\s+)?nexus(?=$|[\s,.:;!?-])", re.I)


def extract_utterance(transcript: str, *, require_wake: bool = False) -> str | None:
    """Return a request or None if the optional activation prefix is missing.

    A bare activation without a request is not sent to the assistant.
    """
    if not isinstance(transcript, str) or len(transcript) > 4000:
        return None
    spoken = transcript.strip()
    if not spoken or "\x00" in spoken:
        return None
    if not require_wake:
        return spoken
    # Accent normalization allows "olá nexus" and "ola nexus" alike.
    decomposed = unicodedata.normalize("NFKD", spoken)
    normalized = "".join(c for c in decomposed if not unicodedata.combining(c))
    match = _ACTIVATION.match(normalized)
    if match is None:
        return None
    request = spoken[match.end():].strip(" ,.:;!?-\t\r\n")
    return request or None
