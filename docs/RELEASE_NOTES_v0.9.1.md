# NEXUS CORE v0.9.1 — On-Demand Privacy Status

## Entrega

- `Ctrl+Shift+I` abre um diálogo nativo com o estado atual de Escuta, Voz e Visão. O atalho não modifica os controles existentes nem o layout principal.
- O diálogo lê uma fotografia imutável do estado de software no momento do pedido, inclusive após pausar a escuta e durante análise visual autorizada ou cancelamento solicitado.
- O texto usa rótulos curtos e fixos, não expõe caminho de imagem, pergunta, transcrição ou pixels. Nenhuma captura, inferência, consulta ao banco ou autorização nova é iniciada.
- Testes Tk sob Xvfb verificam ausência de chamadas ao Agent/captura não autorizada, estado imediatamente atualizado e visualização durante análise autorizada.

## Limites

Os estados do aplicativo não comprovam microfone, alto-falantes ou câmera funcionando. O diálogo nativo oferece acesso por teclado, mas não certifica suporte a leitores de tela nem substitui homologação física no Ubuntu Desktop 24.04 LTS. Cancelamento de análise visual permanece cooperativo. PostgreSQL e Ollama locais, identidade visual e consentimento por operação permanecem como documentados.

## Integração e publicação

Desenvolvida sobre o PR #22 (v0.9.0), após a cadeia #15–#21. A `main` ainda contém código até v0.8.2; última release oficial v0.7.2. O workflow de publicação v0.9.1 permanece desabilitado. Integração ordenada, CI no SHA final da `main` e aceite físico registrado são condições antes de uma tag/release estável.
