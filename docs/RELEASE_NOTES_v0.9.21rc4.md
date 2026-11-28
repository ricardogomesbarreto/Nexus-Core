# Nexus Core v0.9.21-rc.4

Ao conversar no perfil compacto, o Ollama pode conservar o modelo de texto por quatro segundos após uma resposta para atender à próxima pergunta. A janela curta depende de memória disponível equivalente ao tamanho do modelo mais 1.536 MiB. A cada turno, o Nexus confere novamente a reserva para uma carga completa. Se a sessão anterior ainda estiver liberando memória, a espera é limitada e cancelável no trabalhador de texto. A visão continua com descarregamento imediato no perfil eco.

O teste inclui dez turnos, dois cancelamentos, consulta aos modelos residentes e confirmação de que o modelo sai da memória após a conversa. Para testar no notebook Ubuntu, instale a tag e execute `NEXUS_RESOURCE_PROFILE=eco python3 scripts/observe_desktop.py`. Voz, câmera e Wayland seguem na homologação física.
