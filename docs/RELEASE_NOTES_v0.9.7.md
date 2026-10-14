# NEXUS CORE v0.9.7 — Keyboard-Gated Vision Requests

## Entrega

- A janela desktop oferece `Ctrl+Shift+F` para escolher um arquivo de imagem, `Ctrl+Shift+T` para a tela atual e `Ctrl+Shift+K` para escolher uma câmera. Os três atalhos chamam o fluxo visual existente dos respectivos botões.
- Para cada pedido, o usuário escolhe a pergunta e confirma a autorização individual de uma leitura/captura destinada ao Ollama local. Escolha cancelada, consentimento negado ou operação em andamento impedem a captura.
- Testes da janela Tk em display virtual verificam cada atalho e fonte com consentimento, cada recusa, a seleção cancelada e o bloqueio de uma nova solicitação durante operação.

## Limites

Os atalhos dependem de foco na janela Nexus Core; não são globais do sistema. A autorização vale para uma análise, sem acesso visual contínuo. Os testes usam fontes simuladas e não validam a câmera, a captura da tela, o teclado físico ou o hardware de áudio no Ubuntu Desktop 24.04 LTS.

## Integração e publicação

Branch de desenvolvimento sobre o PR #28 (v0.9.6), após a cadeia #15–#27. A `main` contém código até v0.8.2; última release oficial v0.7.2. Workflow de release v0.9.7 desabilitado. Integração ordenada, CI no SHA final da `main` e aceite físico registrado precedem tag/release estável.
