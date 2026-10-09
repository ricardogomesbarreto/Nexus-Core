# Nexus Core v0.7.1 — Controlled Desktop Navigation

## Entregas

- Ferramenta `desktop_navigate` integrada ao Agent, ToolRegistry, ToolExecutor e SecurityGate, sem alterar a identidade visual existente.
- Quatro ações permitidas, cada uma equivalente a **uma tecla**: `next_field` (Tab), `previous_field` (ISO_Left_Tab), `page_up` (Prior) e `page_down` (Next).
- `MEDIUM`: confirmação explícita por operação; a janela nativa Tk exibe ID, título e nome da navegação antes do consentimento.
- Bloqueio de teclas arbitrárias, Enter, Escape, Ctrl/Alt, atalhos, macros, repetições, shell e cliques.
- Revalidação do título do ID de janela autorizado **após consentimento**, execução direcionada ao ID X11 com `xdotool`, timeout e erros sanitizados.
- Wayland/XWayland e DISPLAY remoto continuam não suportados e são recusados.
- Sem capturas novas, execução agendada ou monitoramento visual por iniciativa do modelo.
- Testes para contratos, recusa de confirmação, validação dos argumentos antes do diálogo, IDs/títulos alterados, lista de teclas, Wayland/remote display, subprocesso sem shell, exceções e visualização da autorização.
- README atualizado com a descrição completa da v0.7.1, histórico contínuo v0.1.x–v0.7.1 e planejamento de v0.7.2.

## Continuidade de versões anteriores

Permanecem os recursos das versões v0.6.x: análise pontual autorizada de **Imagem, Tela e Câmera**, resposta em texto e por **voz masculina ou feminina** (se leitura habilitada), conversa por turnos, sugestões apenas consultivas, cancelamento cooperativo e auditoria. A v0.7.0 mantém leitura da janela ativa e digitação pontual, ambas estritamente limitadas. Linux desktop local, MIT, PostgreSQL e Ollama permanecem as diretrizes de distribuição.

## Limitações

Os eventos X11 `XSendEvent` podem ser ignorados pelo aplicativo de destino, e o processo concluído não prova que a navegação ocorreu. É uma operação host X11 fora de isolamento Docker, por isso depende de consentimento individual. Não deve ser usada em formulários sensíveis antes da validação no equipamento físico. Sem suporte Wayland, automação de macros ou plena autonomia. Hardware real de áudio, vídeo e X11 não é verificado pela CI; os testes usam subprocessos simulados.

## Próximo marco

v0.7.2 — Desktop Interaction Safety & Diagnostics (planejado, não implementado).

## Publicação

Tag e release v0.7.1 somente após CI aprovada no commit exato integrado à main.
