# NEXUS CORE v0.9.4 — Accessible Cancellation Shortcut

## Entrega

- `Ctrl+Shift+X` usa o cancelamento existente da janela para o turno atual de conversa ou análise visual autorizada.
- Em conversa pendente, bloqueia execução futura do turno e libera pedidos de autorização ainda aguardando decisão. Em visão, marca cancelamento solicitado e descarta a resposta ao terminar, sem afirmar parada imediata da captura ou da inferência.
- Em estado ocioso ou após início do encerramento, o atalho não altera entrada, microfone, permissões ou histórico. Repetições durante o mesmo cancelamento não repetem a solicitação.
- Testes Tk/Xvfb cobrem inércia ociosa, turno de Agent bloqueado e análise visual autorizada com resultado descartado.

## Limites

O cancelamento permanece cooperativo. Ações já executadas não são desfeitas; uma chamada Ollama ou captura iniciada pode concluir antes da finalização. O atalho não inicia escuta, captura ou autorização. Os testes simulados não substituem homologação física Ubuntu Desktop 24.04 LTS, inclusive acessibilidade, áudio e visão.

## Integração e publicação

Branch de desenvolvimento sobre o PR #25 (v0.9.3), após a cadeia #15–#24. A `main` contém código até v0.8.2; última release oficial v0.7.2. Workflow de release v0.9.4 desabilitado. Publicação exige integração ordenada, CI no SHA final da `main` e aceite físico registrado.
