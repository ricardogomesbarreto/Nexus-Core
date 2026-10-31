"""Baixo consumo no desktop Tk: taxa de sondagem proporcional à atividade.

A política é pura, sem threads, imports opcionais, acesso a arquivos ou rede.
"""
from __future__ import annotations


def next_desktop_poll_ms(*, busy: bool, listening: bool, speaking: bool,
                         camera: bool, closing: bool, pending_voice: bool) -> int:
    """Atualiza rapidamente durante voz/câmera/tarefas e pouco em repouso.

    O widget responde a eventos normais do Tk independentemente deste poll.
    """
    return (80 if (busy or listening or speaking or camera or closing
                   or pending_voice) else 250)
