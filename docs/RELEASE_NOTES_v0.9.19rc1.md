# NEXUS CORE 0.9.19rc1 — candidata de desempenho

**Pré-release para testes no notebook de 8 GB; não é versão estável.**
Tag `v0.9.19-rc.1` deve apontar somente para o commit da `main` que passou na
CI de `push`. O pacote Python usa a versão `0.9.19rc1` (PEP 440).

## Alterações

- No desktop `eco`, o prompt usa dois turnos recentes, limitados a 420
  caracteres cada por pergunta e resposta; o histórico visível e o arquivo
  de conversas não são truncados por essa política de prompt.
- Respostas longas têm leitura em voz abreviada a 220 caracteres no perfil
  `eco`; o texto completo permanece no chat.
- A câmera ao vivo usa prévia de 2 fps nesse perfil, 5 fps no equilibrado;
  conserva uma única imagem recente em memória, sem gravar vídeo.
- Texto mantém o modelo carregado por até 10 s somente se havia e ainda há
  pelo menos 4 GiB disponíveis e o limite de memória total é de 6 GiB ou mais.
  Com menos memória, volta ao descarregamento imediato (`keep_alive: 0s`).
  Visão continua com descarregamento imediato e verificação de memória.

## O que medir no hardware real

Atualize a instalação no Ubuntu, abra `NEXUS_RESOURCE_PROFILE=eco python3
scripts/observe_desktop.py` e faça duas perguntas simples seguidas, com voz
desligada, depois com voz ligada. Registre tempo, swap e RAM disponível.
Abra a prévia da câmera, tire uma foto e veja separadamente se a captura
funciona e se o Ollama analisa a imagem. Caso `gemma3:4b` não caiba na RAM,
o bloqueio antes da inferência é esperado; não o force por perfil equilibrado.
Após fechar a janela, execute `bash scripts/nexus_core_session.sh stop`.

CI com webcam virtual não substitui esse aceite físico. Nenhum modelo é
baixado, nenhum serviço é habilitado no boot e não há promessa de latência
nem consumo medido no seu computador. O conjunto maior de funcionalidades
da PR #104 permanece separado desta candidata de estabilidade.
