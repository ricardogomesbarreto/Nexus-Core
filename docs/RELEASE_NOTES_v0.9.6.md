# NEXUS CORE v0.9.6 — TTS Startup Cancellation Safety

## Entrega

- A síntese local de voz verifica se a requisição continua atual antes de criar o processo e novamente após registrá-lo. Se a parada ocorreu durante a criação do eSpeak NG, o processo é encerrado sem receber o texto antigo.
- A janela fornece essa verificação apenas ao `LocalSpeaker`; sintetizadores injetados para testes e integrações preservam a interface de dois argumentos.
- Testes simulam cancelamento antes da abertura do processo e exatamente entre a criação e o registro; conferem término, ausência de texto enviado e descarte do evento tardio pela geração de áudio.

## Limites

Uma fala já emitida antes da solicitação não pode ser desfeita. A alteração reforça a parada da saída local; não cancela ações, não desliga respostas futuras e não modifica escuta ou consentimento visual. A CI simula o processo; a latência do áudio real ainda requer homologação física no Ubuntu Desktop 24.04 LTS.

## Integração e publicação

Branch de desenvolvimento sobre o PR #27 (v0.9.5), após a cadeia #15–#26. A `main` contém código até v0.8.2; última release oficial v0.7.2. Workflow de release v0.9.6 desabilitado. Integração ordenada, CI no SHA final da `main` e aceite físico registrado precedem tag/release estável.
