# Nexus Core v0.7.3 — Desktop Target Integrity

## Entregas implementadas na branch de desenvolvimento

- `desktop_window_info` consulta de forma pontual **ID, título, PID e WM_CLASS** da janela ativa em uma sessão X11 local.
- `desktop_type_text` e `desktop_navigate` exigem esses quatro campos no contrato estruturado e os exibem no diálogo de consentimento.
- Após uma confirmação humana por operação, o backend consulta novamente o título, o PID informado via `_NET_WM_PID` e a classe X11 para o ID autorizado, recusando a ação caso qualquer campo difira ou não possa ser obtido.
- Metadados ausentes, inválidos ou alterados bloqueiam a digitação e a navegação antes da chamada que envia eventos.
- Testes com subprocessos simulados exercitam troca de janela mesmo com ID preservado, PID ou classe diferentes, metadados inexistentes e contratos legados sem identidade.
- Continuam proibidos controle arbitrário do mouse, shell, atalhos não permitidos, navegação múltipla, captura automática e execução sem consentimento.
- A interface Tk, voz contínua local feminina/masculina, visão autorizada, Ollama local e PostgreSQL local não tiveram mudanças funcionais ou visuais.

## Limitações e compatibilidade

**A verificação de PID/WM_CLASS é uma defesa adicional, não autenticação criptográfica.** Clientes X11 podem anunciar metadados falsos, processos e IDs podem ser reutilizados e permanece uma pequena janela de tempo entre a última consulta e o envio. O evento sintético `xdotool` também pode ser ignorado pelo aplicativo de destino.

Aplicações que não disponibilizam PID ou classe X11 não serão controladas: comportamento **fail-closed**. Os campos `window_pid` e `window_class` tornam-se obrigatórios nas ferramentas de digitação/navegação; chamadas legadas serão recusadas. `nexus-core --desktop-check` continua passivo e não constitui validação real do display ou de um aplicativo específico.

## Critérios de aceite antes da tag/release

1. Instalação e compilação de todos os módulos Python com Python 3.12+.
2. Suíte completa `pytest` em Linux/Xvfb, com PostgreSQL, Docker e dependências opcionais usadas pela CI.
3. Homologação em desktop Linux X11 real com `xdotool`, incluindo janela que muda de identidade, ausência de PID/WM_CLASS, recusa de consentimento e aplicativo que não aceita `XSendEvent`.
4. Documentação, pacote e commits consistentes; tag/release somente após CI verde para o commit integrado à `main`.

**Estado nesta branch:** código e testes preparados; CI completa e homologação física não verificadas. Não declarar publicação estável apenas pela existência do PR.

## Próximos marcos

A linha `v0.8.x` do roadmap trata de dispositivos e arquitetura distribuída; a priorização depende do aceite da v0.7.3.
