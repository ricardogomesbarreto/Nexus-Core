# Nexus Core v0.6.3 — Conversation Reliability

## Correções de bugs

- Impede que transcrições e erros antigos do Vosk sobrescrevam o estado de uma nova escuta. Evita iniciar simultaneamente capturas do microfone ao alternar rapidamente pausa/retomada.
- Usa gerações independentes para síntese eSpeak NG: uma fala interrompida ou silenciada não pode finalizar indevidamente a próxima reprodução nem reativar o microfone em momento incorreto.
- Recusa iniciar áudio enfileirado depois de cancelamento ou fechamento da janela.
- Recusa autorizações de ferramenta pendentes ao cancelar solicitação, mesmo quando uma resposta positiva chega depois de um diálogo já invalidado.
- Preserva a seleção feminina/masculina e as respostas faladas de Imagem, Tela e Câmera; interface existente não foi redesenhada.

## Auditoria e testes

- Inventário de **191 arquivos rastreados** na main v0.6.2: módulos, testes, documentação, SVG, PNG, configurações e GitHub Actions.
- Nova verificação automatizada percorre código-fonte e ativos textuais no checkout: sintaxe Python, UTF-8, JSON, SVG, manifesto de ícones e histórico de releases.
- Regressões específicas simulam capturas concorrentes, eventos antigos de TTS, silenciamento, cancelamento de consentimento e confirmação tardia.
- Build e testes completos são executados na CI Linux com Python 3.12, PostgreSQL 16, Docker, Xvfb e extras opcionais de voz e visão.

## Escopo, segurança e limitações

O cancelamento é cooperativo e não reverte ações já iniciadas ou concluídas. As respostas de visão por voz continuam condicionadas à opção de leitura e instalação do eSpeak NG. As capturas visuais exigem consentimento por ação e utilizam somente o Ollama local. A auditoria é estática e automatizada, não uma revisão manual semântica individual de todos os arquivos. Câmera, microfone, reprodução de som e GPU/modelo multimodal físico ainda exigem homologação no Linux real.

## Próximo macro-marco

v0.7.x — Controlled Desktop Automation. Sem hospedagem, serviços pagos, mudanças de layout ou autonomia irrestrita.

## Publicação

A tag v0.6.3 e a release são criadas somente se a CI passar no commit exato publicado na main.
