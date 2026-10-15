# NEXUS CORE v0.9.10 — Spoken Voice Selection

## Entrega

- Frases completas em português escolhem a voz feminina ou masculina na janela desktop. A seleção atualiza o mesmo controle da interface e confirma na voz escolhida quando a leitura em voz alta está habilitada.
- A seleção preserva o silenciamento e o estado de escuta. Quando a saída falada está desativada, a confirmação aparece apenas no histórico; com a escuta pausada, os comandos de voz não são recebidos.
- O reconhecimento respeita a frase de ativação opcional “Nexus”. Os comandos são locais e não chamam o Agent/Ollama, banco de dados, ferramentas ou captura visual.
- Testes Tk em Xvfb cobrem as duas vozes, a frase de ativação, a saída silenciada, perguntas comuns que não são comandos e o isolamento do agente.

## Limites

A preferência vale para a sessão atual; não há persistência de voz entre reinicializações. Durante a reprodução, o reconhecimento permanece suspenso para evitar eco. Os testes simulados não certificam microfone ou áudio no Ubuntu físico.

## Integração e publicação

Marco de desenvolvimento sobre v0.9.9, integrada à `main` pelos PRs #15–#31. A última release oficial permanece v0.7.2. O workflow v0.9.10 fica desabilitado; a publicação requer integração ordenada, CI no commit final da `main`, homologação física Ubuntu 24.04 LTS (X11, áudio, câmera, Ollama, PostgreSQL, instalação e recuperação) e revisão específica do workflow.
