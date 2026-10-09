# Nexus Core v0.7.0 — Controlled Desktop Automation Foundation

## Entregas

- Primeira integração controlada de interação desktop Linux X11, com dois contratos de ferramenta registrados no Agent, ToolRegistry e ToolExecutor.
- \`desktop_window_info\`: consulta read-only da janela X11 ativa (ID e título, sem screenshot).
- \`desktop_type_text\`: tenta enviar até 300 caracteres imprimíveis a uma janela X11 identificada por ID e título **após aprovação humana específica para cada chamada** (risco MEDIUM). Não envia Enter, shell, clique ou atalho livre.
- Revalidação de título e ID **após o diálogo de consentimento** e antes da digitação. Saída do xdotool por ID fixo; sem shell ou interpretação de scripts, com timeout e mensagens de erro sanitizadas.
- Rejeição de Wayland/XWayland e DISPLAY remoto; dependência gratuita opcional xdotool.
- Diálogo de autorização Tk exibe título/ID da janela e texto exato autorizado.
- \`nexus-core --desktop-check\`: diagnóstico passivo de compatibilidade e instalação, sem capturas, acessos à área gráfica, banco ou modelo.
- Testes de mediação por SecurityGate, contrato tipado, aprovação/recusa, janela alterada, limitações de entrada, subprocessos sem shell, ausência de dependências e diagnóstico sem efeitos.
- README atualizado com seção completa da v0.7.0 e índice das versões iniciais v0.1.0–v0.3.9; notas de todas as versões modernas preservadas, sem redesenho da GUI.

## Garantias e limitações

A automação escreve **no host X11, fora do Docker**; ações MEDIUM exigem confirmação. O usuário deve revisar a janela e o texto. Não foram habilitados cliques, atalhos livres, macros, shell não isolado, captura contínua ou controle irrestrito. Alguns aplicativos X11 rejeitam eventos XSendEvent enviados à janela por ID; mesmo sucesso do subprocesso não prova a digitação no programa. Não usar para dados sensíveis. A CI simula subprocessos e dispositivo gráfico, sem homologação física de xdotool/compositor/software alvo.

NEXUS CORE continua o único produto NEXUS gratuito, open source, local Linux; PostgreSQL permanece único banco. Voz Vosk/eSpeak NG feminina/masculina e respostas visuais faladas são preservadas. Todas as ferramentas continuam auditáveis e submetidas às políticas de acesso.

## Próxima versão

v0.7.1 — Controlled Desktop Navigation (planejada, não entregue nesta release).

## Publicação

Tag e release v0.7.0 somente após CI aprovada para o commit exato na main.
