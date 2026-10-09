# Nexus Core v0.6.2 — Guided Autonomy & Conversation

## Entregas

- **Resposta por voz para Imagem, Tela e Câmera** no desktop Tk, usando a voz local feminina ou masculina selecionada (eSpeak NG) sempre que `Ler respostas em voz alta` estiver habilitado (padrão: habilitado).
- Integração unificada do caminho de leitura em voz alta para conversas normais e respostas visuais; texto exibido sempre, mesmo com som desabilitado.
- Botão discreto `Sugerir` com aconselhamento a partir do histórico efêmero. O `AgentPlanner` **impede a execução de ferramentas** em modo consultivo, inclusive se o Ollama propuser uma ação.
- Botão `Cancelar` para descartar respostas de texto/visão ainda pendentes; cancelamento cooperativo antes de novas ações do Agent, sem acumular histórico visual cancelado.
- Testes Tk/Xvfb cobrindo as três origens visuais, variante masculina/feminina, silenciamento, consentimento recusado, sugestões sem tools e cancelamento de respostas/visão.
- README revisado com histórico explícito de marcos anteriores e notas de release; design visual preservado.

## Limitações e privacidade

A leitura eSpeak NG tem limite de 2.400 caracteres por fala; descrições mais extensas continuam disponíveis no transcript. Áudio físico, câmera, tela Wayland/X11 e modelo visual Ollama real dependem do hardware e não são homologados pela CI. Cancelamento é cooperativo, não interrompe inevitavelmente uma chamada HTTP ou subprocesso em execução nem reverte efeitos já realizados. O NEXUS CORE não captura continuamente e não armazena imagens; permissão por análise continua obrigatória. Nenhuma ação sensível ocorre autonomamente fora do SecurityGate.

## Publicação

Tag e release v0.6.2 somente após CI bem-sucedida do commit exato da main em Python 3.12/Linux/PostgreSQL 16/Docker/Xvfb.
