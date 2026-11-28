# Nexus Core v0.9.21-rc.3

A janela acrescenta apenas o texto novo durante a geração e preserva mensagens posteriores quando a prévia é cancelada. As perguntas conversacionais usam instruções mais curtas. O perfil compacto processa a entrada textual em lotes de até 32 tokens com duas threads, contexto de 768 e até 128 tokens de saída. O modelo continua sendo descarregado após a solicitação.

O ensaio de aceitação envia dez perguntas, cancela duas após a primeira prévia, verifica o histórico limitado e encerra a janela. Mede tempo de CPU do conjunto, primeiro texto, duração e intervalo máximo do loop gráfico. Ubuntu 24.04, Tk/Xvfb, PostgreSQL e Ollama com qwen3:1.7b compartilham 4 GB, duas CPUs e zero swap. Voz, câmera e Wayland no Ubuntu 26.04 dependem de homologação física.

Para repetir no notebook, instale a tag com `python3 scripts/install_linux.py` e inicie `NEXUS_RESOURCE_PROFILE=eco python3 scripts/observe_desktop.py`.
