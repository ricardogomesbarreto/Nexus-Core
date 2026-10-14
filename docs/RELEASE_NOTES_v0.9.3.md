# NEXUS CORE v0.9.3 — Typed Privacy Status

## Entrega

- A caixa de conversa reconhece as frases explícitas de consulta de privacidade da v0.9.2. A resposta é gerada localmente com os estados de Escuta, Voz e Visão, inclusive quando a escuta está pausada.
- O histórico recebe a pergunta e a resposta. Com a saída de voz habilitada, a resposta usa a voz selecionada; com a saída desligada, permanece textual.
- A consulta interrompe a escuta ou a fala anterior antes da resposta, sem reativar o microfone pausado. Não chama Agent/Ollama, banco de dados ou captura visual, nem altera permissões ou cria um turno de contexto no modelo.
- Perguntas diferentes seguem ao assistente normalmente. Durante outra operação, a caixa mantém o texto digitado para envio posterior; o diálogo `Ctrl+Shift+I` permanece acessível.
- Testes Tk/Xvfb cobrem pausa, voz, isolamento do Agent e a pergunta comum.

## Limites

Estados do software não certificam microfone, alto-falantes ou câmera. O fluxo textual não substitui homologação física de áudio, X11 e acessibilidade no Ubuntu Desktop 24.04 LTS. Autorizações de imagem, tela, câmera e ferramentas permanecem individuais.

## Integração e publicação

Branch de desenvolvimento sobre o PR #24 (v0.9.2), após a cadeia #15–#23. A `main` contém código até v0.8.2; última release oficial v0.7.2. O workflow de release v0.9.3 fica desabilitado. A publicação exige integração ordenada, CI no SHA final da `main` e aceite físico registrado.
