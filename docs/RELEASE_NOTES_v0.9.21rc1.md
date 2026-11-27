# NEXUS CORE v0.9.21rc1 — candidata de leitura incremental

**Pré-release para teste no notebook de 4 GB; não é versão estável.** A tag
`v0.9.21-rc.1` aponta apenas para o commit de `main` validado pela CI de push.

## Mudanças

- Perguntas conversacionais de texto e sugestões sem ferramentas usam o fluxo
  de respostas do Ollama. A janela mostra o texto durante a geração, sem
  esperar a conclusão integral. O texto final continua passando pela validação
  do contrato antes de entrar no histórico local ou na saída de voz.
- A conexão HTTP fecha ao cancelar entre os fragmentos recebidos. O fluxo tem
  limites de 4 KiB por linha, 128 KiB de protocolo e 8.192 caracteres de
  resposta. A interface mantém apenas a atualização mais recente na fila,
  evitando crescimento de RAM com fragmentos atrasados.
- Propostas JSON para ações e ferramentas permanecem no caminho sem streaming
  e exigem o mesmo controle de autorização. Os limites de contexto, threads,
  modelo e memória do perfil compacto v0.9.20rc1 são preservados.

## Teste físico necessário

No Ubuntu de 4 GB, instale a candidata e abra com
`NEXUS_RESOURCE_PROFILE=eco python3 scripts/observe_desktop.py`. Teste duas
perguntas curtas consecutivas; meça tempo para o primeiro texto e para o
resultado completo, RAM livre, swap, CPU e versão do modelo (`ollama ps`).
Durante uma terceira resposta, clique **Cancelar** e confira que o texto
parcial some, o áudio não toca e o histórico não recebe resposta incompleta.
Teste também uma ação que exige autorização para conferir o fluxo separado.
Feche o aplicativo e execute `bash scripts/nexus_core_session.sh stop`.

O transporte não consegue interromper imediatamente uma leitura de rede
bloqueada: o encerramento ocorre no próximo fragmento ou timeout. A CI não
mede estabilidade, latência ou consumo reais em 4 GB; anote os resultados na
issue de aceite físico antes de declarar estabilidade ou publicar versão final.
