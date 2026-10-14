# NEXUS CORE v0.9.9 — Spoken Desktop Controls

## Entrega

- Frases completas em português solicitam análise de **imagem**, **tela** ou **câmera** na janela desktop. O reconhecimento local abre o mesmo fluxo já usado pelos botões e atalhos: seleção, pergunta e consentimento explícito para uma única análise. Recusa ou cancelamento não captura nem envia imagem e retoma a escuta se ela estiver habilitada.
- **"Desative a voz"** e **"Ative a voz"** alteram somente a saída falada. O desligamento responde por texto; a ativação confirma também por voz. As frases são tratadas localmente, sem chamada ao agente ou execução de ferramentas.
- O modo opcional de frase de ativação continua valendo: com ele ligado, o usuário precisa iniciar o pedido por **"Nexus"**. Testes Tk em Xvfb verificam frases aceitas/rejeitadas, as três fontes sem consentimento, seleção cancelada, captura autorizada única e alternância de voz.

## Limites

Com escuta pausada, comandos de voz não são recebidos; retome pelo botão ou `Ctrl+Shift+M`. Durante reprodução de áudio e operações em andamento, o reconhecimento fica suspenso para evitar eco e concorrência; use os atalhos e controles da janela. A escolha da imagem/pergunta e a autorização visual continuam na interface Tk, não são aprovações faladas. Os testes simulam dispositivos e não homologam microfone, câmera, áudio, Ollama multimodal ou teclado físico no Ubuntu Desktop 24.04 LTS.

## Integração e publicação

Branch de desenvolvimento sobre o PR #30 (v0.9.8), após a cadeia #15–#29. A `main` contém código até v0.8.2; a última release oficial é v0.7.2. O workflow de release v0.9.9 permanece desabilitado. Integração ordenada, CI no SHA final da `main` e aceite físico registrado precedem tag/release estável.
