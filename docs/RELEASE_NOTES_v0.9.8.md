# NEXUS CORE v0.9.8 — Accessible Speech Output Toggle

## Entrega

- `Ctrl+Shift+V`, quando a janela está em foco, alterna o mesmo controle **Ler respostas em voz alta**. O indicador de privacidade **Voz** acompanha a alteração.
- Desativar durante uma resposta falada solicita a parada ao sintetizador local e descarta a conclusão tardia daquela geração. As próximas respostas, inclusive análises visuais autorizadas, permanecem em texto. Reativar permite falar as próximas respostas com a voz selecionada, sem reproduzir a anterior.
- Testes da janela Tk sob display virtual cobrem o evento de teclado, o estado do microfone e do texto digitado, a parada durante fala, o evento tardio, a próxima voz e a resposta visual pendente.

## Limites

O atalho é local à janela e não liga ou desliga a escuta. Uma fala já emitida não pode ser desfeita; a parada do sintetizador é cooperativa. A CI simula o áudio e não substitui teste de teclado, microfone ou alto-falante físico no Ubuntu Desktop 24.04 LTS. Nenhum consentimento visual é concedido por este controle.

## Integração e publicação

Branch de desenvolvimento sobre o PR #29 (v0.9.7), após a cadeia #15–#28. A `main` contém código até v0.8.2; última release oficial v0.7.2. Workflow de release v0.9.8 desabilitado. Integração ordenada, CI no SHA final da `main` e aceite físico registrado precedem tag/release estável.
