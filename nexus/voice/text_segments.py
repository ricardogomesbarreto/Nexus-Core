"""Planejamento limitado de leitura em voz, sem modelos nem subprocessos.

Divide texto em até quatro trechos de 2.400 caracteres; os motores locais
permanecem responsáveis pela síntese e pela reprodução. Não persiste texto.
"""
from __future__ import annotations

import re


def speech_segments(text: str, *, size: int = 2400, limit: int = 4) -> tuple[str, ...]:
    """Preserva palavras quando possível; limita o plano a 9.600 caracteres.

    O corte duro é permitido apenas em palavras individuais maiores que o
    trecho, de modo que nenhum subprocesso receba texto acima de seu limite.
    """
    if not isinstance(text, str) or not text.strip():
        return ()
    if type(size) is not int or not 100 <= size <= 2400:
        raise ValueError("Tamanho de trecho de fala inválido.")
    if type(limit) is not int or not 1 <= limit <= 4:
        raise ValueError("Quantidade de trechos de fala inválida.")
    source = re.sub(r"\s+", " ", text[:size * limit]).strip()
    chunks = []
    while source and len(chunks) < limit:
        if len(source) <= size:
            chunks.append(source)
            break
        cut = source.rfind(" ", 0, size + 1)
        if cut < size // 2:
            cut = size
        chunks.append(source[:cut].strip())
        source = source[cut:].strip()
    return tuple(segment for segment in chunks if segment)
