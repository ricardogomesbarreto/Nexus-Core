# Nexus Core v0.6.1 — Vision Desktop Integration

## Entregas

- Integração opt-in da visão local à janela Linux existente, mantendo identidade e layout principais: botões Imagem, Tela e Câmera.
- Seleção pontual de fonte, pergunta limitada, **consentimento explícito por captura/leitura** e processamento em worker, sem bloqueio do loop Tk.
- Pausa da captura de áudio enquanto visão processa; retomada após resposta ou falha, se habilitada.
- Exibição da descrição no transcript e leitura opcional pela voz local configurada.
- Integração temporária de **texto da descrição** com histórico de até seis turnos, sem armazenamento de imagens em PostgreSQL ou disco pela aplicação.
- Orientações de diálogo natural, respostas e sugestões consultivas. Autonomia restrita: nenhuma ferramenta ou captura sem pedido atual e mediação do SecurityGate.
- Testes em Tk/Xvfb de consentimento recusado/aprovado, câmera e arquivos, cancelamento, erros, encerramento e conversa de acompanhamento.

## Limitações

A voz é por turnos, não full-duplex ou de latência instantânea. A captura continua exclusivamente sob clique e confirmação específicos. A CI usa serviços/sensores simulados; testes com equipamentos físicos, modelo visual Ollama real e Wayland/X11 específicos permanecem pendentes.

## Publicação

A release e a tag v0.6.1 devem ser criadas somente se a CI passar no commit exato da main.
