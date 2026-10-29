# Aceite físico da instalação atual — Nexus Core 0.9.17

**Estado: pendente de execução no notebook Ubuntu.** A suíte automatizada e a
CI não observam a sua webcam, alto-falantes, Wayland nem a memória real. Um
`RELATADO` no diagnóstico é a declaração do operador, não aprovação automática.
Este roteiro acompanha a versão instalada; uma mudança posterior exige repetir
os itens afetados e conferir o SHA final antes de publicar uma versão estável.

## Preparação e observação durante o uso

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
git rev-parse HEAD
python3 scripts/install_linux.py
~/.local/bin/nexus-core --version
NEXUS_RESOURCE_PROFILE=eco python3 scripts/observe_desktop.py
```

O último comando inicia os serviços sob demanda e abre a janela, mostrando
`TESTE-LOCAL` e `[MEDICAO-LOCAL]` no terminal. Feche a janela normalmente para
ver o resumo. O observador informa a cada dez segundos RAM disponível no
sistema, swap usada, modelos carregados no Ollama e soma aproximada de RSS dos
processos da sessão. Ele **não mede** RSS de Ollama/PostgreSQL separadamente,
não calcula consumo atribuível apenas ao Nexus, não mede temperatura nem julga
a qualidade da resposta. Se `/proc` ou Ollama não responder, mostra
`indisponivel` em vez de zero. Nenhuma amostra é salva ou enviada. O registro
do aplicativo não inclui transcrição, imagem ou resposta do modelo, mas revise
os logs antes de compartilhar. `duracao_ms` em `TESTE-LOCAL` é o tempo da ação.

Durante esta janela, use **Testes locais → Voz: testar duas falas**. Faça duas
perguntas diferentes, aguarde cada resposta falada e verifique o retorno da
escuta sem botão. Se uma transcrição falhar, informe `FALHOU`, mesmo que
`--recognition-test` isolado tenha passado. Mude entre voz feminina e
masculina; teste pausa, retomada e cancelamento.

Ligue a câmera com consentimento, observe a prévia, tire uma foto, aceite a
análise, compare a descrição com a imagem e ouça a resposta. Anote a duração
de `evento=visao` e `evento=fala`. Aguarde cerca de 50 segundos após a análise
em perfil `eco` e confirme `modelos_carregados=0` **se não houver outro
usuário do Ollama**. Uma descarga lenta, swap crescente ou travamento deve
ser registrado como problema, sem inferir aprovação da amostra isolada.

## Autorizações, arquivos e serviços

- Peça uma pasta nova: negue primeiro, depois repita e autorize. Confirme
  ausência após negação e uma única pasta após aceitação. Repita consentimento
  por botão, texto e voz; teste também cancelamento.
- Peça "Abra o navegador": deve abrir o padrão, sem consentimento extra ou
  URL escolhida pelo assistente. Para testar autorização de aplicativo, use
  "Abra o gerenciador de arquivos". Automação de teclado em outras janelas
  requer X11 e tem aceite separado; não atribua aprovação a Wayland.
- Crie/edite uma imagem e verifique sua saída real, permissões privadas e
  original intacto. Converta um documento e um PDF somente por funções
  disponíveis e autorizadas; abra as saídas em leitor independente e confira
  conteúdo, páginas e integridade. Ausência de CLI opcional = `PENDENTE`.
- Execute duas sessões separadas de serviços: primeira com PostgreSQL/Ollama
  já ativos, que devem permanecer após fechar o Nexus; segunda com ambos
  parados, que devem ser iniciados pelo Nexus sob autorização e encerrados
  após fechar. Se uma instância for reiniciada por outro aplicativo, ela deve
  ser preservada. Não pare serviços usados por outros aplicativos para testar.
  `bash scripts/nexus_core_session.sh status` mostra prontidão, mas não prova
  propriedade da instância. Se a parada exigir senha, confira a solicitação
  administrativa ou rode `bash scripts/nexus_core_session.sh stop` depois.

Após fechar a janela, reabra os serviços para o diagnóstico isolado e
encerre somente os que foram iniciados pelo Nexus depois:

```bash
bash scripts/nexus_core_session.sh start
~/.local/bin/nexus-core --acceptance-log
bash scripts/nexus_core_session.sh stop
```

O registro separa as observações de cada função. `n` ou Enter significa
pendente; `f` significa falha observada.
Anote SHA, versão instalada, sessão gráfica, RAM/swap mínima e máxima,
latências, resultados dos arquivos e serviços. O teste real de restauração
deve ocorrer somente em instalação descartável. Resultados da v0.9.12 ou
simulações da CI não substituem este aceite da v0.9.17.

**Gate da versão estável:** corrigir falhas críticas reproduzidas, obter aceite
físico completo, CI de `push` verde no SHA exato da `main`, atualizar notas e
workflow de publicação para a versão que de fato será lançada. O workflow
estável permanece bloqueado até essas condições estarem registradas.
