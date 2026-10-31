# Aceite físico da v0.9.19.dev1 no Ubuntu 26.04

Este roteiro testa a branch do [PR #102](https://github.com/ricardogomesbarreto/Nexus-Core/pull/102).
A CI do PR avalia o código publicado, mas não mede seu notebook, microfone,
câmera, Wayland nem a qualidade das
respostas. O teste não publica tag ou release.

## Preparar a versão de teste

No checkout sem alterações locais, execute:

```bash
cd "$HOME/Projetos/Nexus-Core"
git status --short
git fetch origin feat/offline-study-exercises-v0919-20261030
git switch --detach FETCH_HEAD
git rev-parse HEAD
python3 scripts/install_linux.py --check
python3 scripts/install_linux.py
~/.local/bin/nexus-core --version
```

Confirme `0.9.19.dev1` e compare o SHA com a versão mais recente do PR.
Se `git status --short` mostrar alterações
suas, preserve-as antes de trocar de branch. O instalador pergunta antes de
instalar dependências ou ativar a verificação de atualização. Não habilita
serviços no boot.

## Sessão observada

```bash
bash scripts/nexus_core_session.sh start
~/.local/bin/nexus-core --resource-check | python3 -m json.tool
ollama list
NEXUS_RESOURCE_PROFILE=eco python3 scripts/observe_desktop.py
```

O observador inicia a janela, imprime linhas `[MEDICAO-LOCAL]` a cada dez
segundos e resume RAM disponível, swap e RSS ao fechar a janela. Registre
também a demora aproximada da pergunta e se o notebook travou. O total RSS
do Nexus não inclui toda a memória do Ollama/PostgreSQL: use a RAM disponível
e o swap para interpretar a pressão geral. Uma medição isolada não prova
desempenho em outra máquina.

Na janela, teste duas falas consecutivas sem apertar o microfone entre elas;
ouça ambas as respostas e confira se a escuta retoma. Teste vozes feminina e
masculina, pausa/cancelamento, prévia e fotografia da câmera com consentimento,
e uma análise visual com resposta falada. A falta de câmera ou modelo deve ser
anotada como pendente ou falha conforme o que foi realmente tentado.

## Biblioteca e índice semântico

Selecione dois arquivos TXT/Markdown seus com conteúdo que você conhece.
Na **Biblioteca local**, importe cada um, selecione um documento e abra
**Índice semântico → Indexar documento selecionado**. O modelo de embeddings
deve estar previamente instalado, ter até 900 MiB e caber na memória livre.
Se não houver um modelo adequado em `ollama list`, marque o teste como
**pendente**; esta etapa não baixa modelos automaticamente.

Faça uma pergunta que tenha relação com um dos textos sem repetir as mesmas
palavras. Use **Pesquisar no índice** e confira a fonte. Depois escolha
**Perguntar com fontes do índice**, confirme, compare a resposta com até três
trechos citados e anote latência, RAM/swap e se a resposta foi falada. Negue
uma solicitação e verifique que ela não executa inferência. Remova o índice
de um documento e confirme que seus trechos não aparecem na próxima busca.
Exclua o outro documento e confirme que seus vetores também desaparecem.
Os testes não devem usar dados sensíveis; não cole os textos ou respostas no
chat para comprovar o funcionamento.

## Registro e encerramento

```bash
~/.local/bin/nexus-core --acceptance-log
bash scripts/nexus_core_session.sh stop
bash scripts/nexus_core_session.sh status
```

O registro pede `s` apenas para o que foi testado na janela e funcionou;
`f` para falha observada; `n` ou Enter para pendente. Ele omite conteúdo de
áudio, transcrição e imagem. Compartilhe aqui o resumo e as linhas
`[MEDICAO-LOCAL]` após conferir que os logs não incluem dados pessoais.
O `stop` deve parar somente serviços iniciados pela sessão Nexus, preservando
os que já estavam ativos antes de `start`.

Para retornar ao código estável depois do ensaio, feche o assistente, execute
`git switch main`, `git pull --ff-only` e reinstale com
`python3 scripts/install_linux.py`. Confirme a versão exibida pelo executável.
Também continuam pendentes o aceite real em Fedora, os CLIs externos opcionais,
a automação de teclado Wayland e um ensaio de recuperação descartável.
