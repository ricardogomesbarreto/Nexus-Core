# NEXUS CORE v0.9.5 — Spoken Reply Interruption

## Entrega

- `Ctrl+Shift+S` interrompe a reprodução da resposta atual pelo eSpeak NG sem desativar a leitura das próximas respostas.
- O histórico textual permanece disponível. A escuta volta ao fluxo normal se estiver habilitada, mas uma pausa explícita do microfone continua valendo.
- O atalho usa a geração de áudio já existente para descartar conclusão ou erro tardio de uma fala interrompida. Sem fala em curso, não muda a entrada ou a configuração.
- Testes Tk/Xvfb cobrem estado ocioso, interrupção durante resposta, evento tardio, próxima resposta e microfone pausado.

## Limites

Interromper a fala não desfaz uma ação, não cancela uma chamada ao Agent/Ollama e não equivale ao botão **Cancelar**. A parada do processo de áudio é solicitada localmente; os testes de display virtual não certificam alto-falantes ou latência em hardware Ubuntu Desktop 24.04 LTS. Nenhuma captura, autorização ou banco de dados é acionado pelo atalho.

## Integração e publicação

Branch de desenvolvimento sobre o PR #26 (v0.9.4), após a cadeia #15–#25. A `main` contém código até v0.8.2; última release oficial v0.7.2. Workflow de release v0.9.5 desabilitado. Publicação exige integração ordenada, CI no SHA final da `main` e aceite físico registrado.
