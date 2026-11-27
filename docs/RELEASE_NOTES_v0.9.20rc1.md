# NEXUS CORE v0.9.20rc1 — candidata para 4 GB

**Pré-release para validação no notebook de 4 GB, não versão estável.** A tag
`v0.9.20-rc.1` aponta somente para o commit de `main` aprovado pela CI de push.

## Mudanças

- Em `eco` com até 5 GiB de RAM utilizável, o prompt de conversa usa apenas
  o turno anterior (até 240 caracteres por lado); o histórico exibido e salvo
  não é encurtado por essa regra. Contexto do modelo: até 768 tokens; lote: 16;
  saída: até 128 tokens; até 2 threads. Perguntas longas e ações podem perder
  contexto, por isso conferir a qualidade da resposta também é parte do teste.
- Antes de carregar o modelo de texto nessa faixa, compara o tamanho em disco
  informado pelo Ollama à RAM **livre naquele momento**, com reserva adicional
  de 512 MiB. Uma estimativa que não cabe é recusada sem enviar o prompt.
  Tamanho em disco não garante uso real de RAM. Se o tamanho não puder ser
  consultado, a execução é recusada nessa faixa.
- O modelo de texto é descarregado após a resposta no perfil compacto.
  A fala das respostas longas usa até 160 caracteres; o texto completo fica
  visível. A prévia ao vivo passa a 480 px e 2 fps, com somente o quadro mais
  recente em memória. A captura avulsa continua no fluxo independente.
- A análise visual preserva o bloqueio por memória e requer um modelo visual
  local que caiba de verdade no computador. O `gemma3:4b` não é prometido em
  4 GB; o instalador sugere `moondream:latest` nessa faixa somente com
  confirmação para download. O modelo visual usado deve ser testado na RAM
  livre real; não há troca automática durante uma conversa.

## Aceite físico necessário

No Ubuntu de 4 GB, atualize a `main` e instale via `python3 scripts/install_linux.py`
se necessário. Abra com `NEXUS_RESOURCE_PROFILE=eco python3
scripts/observe_desktop.py`. Teste duas perguntas simples seguidas, com voz
ligada e desligada. Anote duração, RAM livre, swap, CPU e modelo instalado.
Verifique também prévia da câmera, captura de uma foto e análise da imagem como
resultados **separados**. Confira o encerramento e execute
`bash scripts/nexus_core_session.sh stop`.

CI em runner Linux com mais RAM não comprova desempenho ou estabilidade física
em 4 GB. Serviços continuam sob demanda, sem habilitação na inicialização.
