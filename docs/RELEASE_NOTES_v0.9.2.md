# NEXUS CORE v0.9.2 — Spoken Privacy Status

## Entrega

- Pedidos explícitos de estado de privacidade feitos na conversa contínua recebem resposta local com Escuta, Voz e Visão; o modo opcional de palavra de ativação continua exigindo “Nexus”.
- A resposta aparece na transcrição e usa a voz feminina ou masculina selecionada quando a saída de voz está ligada. Com a saída desligada, fica somente no texto.
- A consulta não envolve Agent/Ollama, PostgreSQL, captura visual ou concessão de permissão. Usa a mesma fotografia de estado de software do painel e do diálogo nativo.
- Testes cobrem frases aceitas, rejeição de frases diferentes, áudio de saída, voz desligada e filtro de ativação sob Tk/Xvfb.

## Limites

O estado de software não certifica que microfone, alto-falantes ou câmera funcionem. A consulta exige que o reconhecimento de fala local já esteja ativo; uma escuta pausada só pode ser retomada pelo controle explícito. Não há homologação física de áudio, câmera, X11 ou acessibilidade em Ubuntu Desktop 24.04 LTS. O consentimento para imagem, tela e câmera permanece individual por operação.

## Integração e publicação

Branch de desenvolvimento sobre o PR #23 (v0.9.1), depois da cadeia #15–#22. A `main` contém código até v0.8.2; última release oficial v0.7.2. O workflow de release v0.9.2 segue desabilitado. Integração ordenada, CI do SHA final da `main` e aceite físico registrado são exigidos antes de tag/release estável.
