# Aceite físico Ubuntu — Nexus Core v0.9.12

**Estado em 17/10/2026: PENDENTE.** Este documento é um roteiro de execução
no notebook do usuário. Nenhuma etapa abaixo está marcada como aprovada pela
CI nem pelos testes simulados. Registre data, versão, SHA, sessão gráfica,
resultado observado e eventuais falhas antes de propor uma tag.

**Registro de 18/10/2026 (`a36bbe1`, Ubuntu 26.04/Wayland):** instalação
concluída com serviços locais existentes; sessão desktop em perfil `eco`
iniciou e encerrou normalmente, relatou `online`, 2010 MiB de memória
disponível e saudação falada em 4,6 s. Nesse trecho não há turnos de chat,
escuta, câmera ou permissões. O `--acceptance-log` seguinte marcou 11 PASSOU,
0 FALHOU, 0 RELATADO e 10 PENDENTE: PostgreSQL, resposta isolada do Ollama
(10 s), microfone, uma transcrição isolada Vosk e captura de quadro passaram.
O operador deixou em branco as oito etapas manuais da janela; teclado no
Wayland e restauração real também seguem pendentes. `session.sh stop`
preservou os serviços preexistentes; não comprova parada de instâncias que
o Nexus iniciou. Esse registro não libera a tag estável.

**Evidência histórica informada pelo usuário, ainda não aceite da v0.9.12:**
Ubuntu 26.04.1, Python 3.14.4 e Wayland; o teste de microfone da linha 0.9.11
registrou sinal PipeWire, o diagnóstico reconheceu um modelo Vosk instalado,
e uma pergunta isolada pelo Ollama recebeu uma resposta curta. Houve relatos
posteriores de problemas de câmera, latência e escuta contínua. Esses testes
não foram repetidos nesta versão e não comprovam o funcionamento conjunto.

**Registro recebido em 17/10/2026 para a v0.9.12 (checkout `164b799`):**
PostgreSQL autenticado, modelo Ollama disponível, resposta de teste em 7 s,
sinal do microfone e um quadro da câmera capturado. O Vosk retornou
`no_transcript`; precisa de novo teste com intensidade e backend de captura.
O registro não contém uma sessão `--desktop`: suas respostas sobre chat, voz,
prévia da câmera e ações não comprovam esses comportamentos. Naquela versão,
`n` contava indevidamente como falha; agora `n` e Enter deixam a etapa pendente,
e somente `f` registra falha testada. O aceite físico permanece pendente.

**Integração do indicador e dos recursos (17/10/2026):** a revisão local
inicial passou com 1.480 testes e 111 ignorados, e gerou o wheel 0.9.12.
Depois, o PR #66 integrou os ajustes à `main` no commit `bb7e487`; sua CI
de pull request passou com 1.619 testes, PostgreSQL e display virtual.
A árvore de arquivos desse commit é idêntica à árvore testada no PR. Isso
não é o aceite no notebook nem substitui a exigência de CI `push` para o
SHA final antes de publicar uma tag. O diagnóstico `--resource-check` foi
executado sem Ollama neste ambiente; consumo, latência e aquecimento no
notebook continuam sem medição. Naquela data, nenhuma tag candidata havia sido
criada; `-rc.1` e `-rc.2` foram publicadas depois, sem release estável.

**Ensaio adicional de ciclo de serviços:** após atualizar a `main`, consulte
`bash scripts/nexus_core_session.sh status`. Com PostgreSQL e Ollama já ativos
para outro aplicativo, rode `start` e `stop` e confirme que ambos continuam
ativos. Depois, com ambos parados e sem outro aplicativo dependente, rode
`start`, verifique a execução do assistente e faça `stop`: apenas as instâncias
iniciadas pelo Nexus devem parar. Se outro processo reiniciar uma unidade no
intervalo, seu identificador de ativação muda e o Nexus deve preservá-la.
Esse ensaio é **PENDENTE no Ubuntu físico**; a CI usa unidades simuladas.

**Teste adicional recebido em 17/10/2026:** no notebook, a tentativa de
aplicar o patch falhou porque o arquivo não existia em `~/Downloads`; portanto
o programa executado não tinha o indicador de rede nem `--resource-check`.
Na sessão registrada, o Vosk reconheceu algumas falas incorretamente e várias
capturas de trinta segundos terminaram sem transcrição. Abrir o navegador
precisou de confirmação; uma foto visual levou cerca de 111 segundos para
analisar. São falhas observadas da instalação anterior, não aceite. O código
integrado agora limita a espera sem palavras a oito segundos, solicita repetição
para comando ambíguo, abre apenas o navegador padrão sem confirmação extra e
oferece nova foto com consentimento por captura. Atualize diretamente pela
`main` com `git pull --ff-only` e execute o instalador; não há patch para
baixar em `~/Downloads`. Essa versão ainda precisa de teste físico no notebook:
medir acerto de voz e latência da visão novamente antes de publicar uma tag.

**Sessão física recebida em 17/10/2026 (checkout `0710f9a`):** Ubuntu 26.04
em Wayland, pacote instalado v0.9.12, PostgreSQL autenticado, resposta
isolada do Ollama em 11 s, captura PipeWire com transcrição Vosk no teste
isolado (pico 100%, possível saturação), uma câmera listada e um quadro
capturado. O indicador alternou `online`/`offline`/`online`. A janela entrou
no perfil `eco` e registrou sucessivos `sem_transcricao` por cerca de 8,5 s
cada, inclusive depois da saudação e da resposta visual: **escuta contínua
falhou nessa sessão**, apesar do teste isolado de Vosk. A análise da câmera
terminou em 118,9 s e a fala correspondente levou 23,2 s. Um diagnóstico
passivo separado mostrou 6.694 MiB totais, 2.174 MiB disponíveis, 1.524 MiB
de swap em uso e nenhum modelo Ollama carregado naquele instante. O log não
inclui a resposta visual nem confirma sua coerência. O usuário marcou o chat
como funcional no questionário, mas o arquivo de eventos enviado não contém
um turno `evento=chat`; essa etapa permanece apenas **RELATADA**. As etapas
manuais deixadas em branco não foram testadas. O primeiro `start` do script
de sessão informou Ollama indisponível imediatamente após `systemctl start`,
enquanto o instalador e a abertura seguinte encontraram o serviço pronto;
o script passa a aguardar até 30 s pela API local. Não há aceite de release.

## Logs ao vivo enquanto usa o assistente

### Aceite REA e instalação com banco inicialmente parado

O anexo REA fornecido é um projeto Node/TypeScript completo,
não um módulo Python instalado. A primeira etapa integrada ao NEXUS
trata **somente de inspeção estática offline**. Antes dos testes,
atualize o repositório e execute o instalador com os serviços
locais disponíveis; depois repita o ensaio com PostgreSQL parado,
para confirmar que o instalador solicita autorização para iniciar
o cluster **correto** (não o 16/main na porta 5433):

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
bash scripts/nexus_core_session.sh start
python3 scripts/install_linux.py

mkdir -p "$HOME/NexusTestes"
cp /usr/bin/true "$HOME/NexusTestes/teste.elf"
printf 'import x from "example";\nexport const value = 1;\n' > "$HOME/NexusTestes/teste.js"

~/.local/bin/nexus-core --desktop 2>&1 | tee "$HOME/nexus-core-desktop.log"
```

Na conversa use `Analise o arquivo
/home/usuario/NexusTestes/teste.elf` e o equivalente para
`teste.js`, adaptando para o nome real da conta. **Negue
primeiro e depois autorize**, confirmando que o relatório mostra
SHA-256 e tipo de arquivo sem executar nenhum binário. Arquivos
APK/JAR só devem ser analisados quando próprios ou autorizados.
Um relatório estático não comprova que o software analisado é
seguro, funcional ou livre de malware.

Após fechar o assistente, pare o serviço PostgreSQL 18 se nenhum
outro sistema o usar e execute novamente
`python3 scripts/install_linux.py` com o serviço parado.
Confirme que ele **pergunta** se pode iniciar somente
`postgresql@18-main.service`; o teste real de autenticação
PostgreSQL deve passar depois do início. Não aceite uma mudança de
senha ou ativação automática no boot.

Registre os eventos `TESTE-LOCAL` sem transcrever conteúdo
privado. A CI executa testes simulados de permissões e parsers;
**não** atesta Ghidra, REA completo, análise de malware ou
a instalação/temperatura do notebook.

### Aceite adicional após auditoria do instalador e arquivos locais

A [auditoria corretiva de 17/10/2026](AUDIT_v0.9.12_2026-10-17.md)
encontrou que o instalador criava um Ollama do usuário com autostart
(`enable --now`), enquanto o sistema deve operar sob demanda.
Isso foi corrigido **para novas unidades**. O teste real deve
distinguir unidade recém-criada de unidade antiga habilitada:

```bash
systemctl --user is-enabled nexus-core-ollama.service
systemctl --user is-active nexus-core-ollama.service
systemctl is-enabled ollama.service postgresql.service postgresql@18-main.service
cat /etc/postgresql/18/main/start.conf
```

Não tente criar uma nova unidade sobre uma antiga nem execute
`systemctl disable` sem considerar outros serviços que dependam
daquele daemon. A CI não pode verificar o estado do login físico.

**Criatividade no desktop:** teste três saídas distintas:
(1) cartaz PNG, (2) cópia de foto editada e (3) conversão de
documento com um CLI Rust **realmente instalado e identificado**.
Para cada operação, recuse primeiro, depois autorize com um nome novo,
verifique que o original permanece intacto e que o resultado não é
vazio nem incompatível com sua extensão. Se PhotoCraft/PdfCraft/WordCraft
não estiver instalado, classifique a conversão como **PENDENTE**, não
como aprovada. Um subprocesso externo **não é isolado em Docker**;
somente instale CLIs de fontes confiáveis.

O arquivo `chat-history.json` armazena texto local quando a opção
de histórico está ativa; revise a exclusão e a preferência de gravação
sem copiar mensagens privadas nos logs. A CI não certifica
criptografia nem detecção automática de segredos.

### Criação e edição local (nova integração, ainda sem aceite físico)

Na janela, peça por texto e depois por voz um cartaz PNG em `~/Imagens`
informando o caminho absoluto (um nome novo em cada tentativa). Confira que
o Nexus mostra a prévia da ação e pergunta antes de gravar; recuse uma vez,
autorize outra e confirme que apenas o arquivo autorizado apareceu. Repita
com uma cópia de foto para escala de cinza. Os CLIs PhotoCraft, WordCraft e
PdfCraft são opcionais: testar as respectivas conversões exige instalar cada
binário separadamente e conferir o resultado, sem executar os ZIPs de fonte.
Observe duração, privacidade do arquivo (`0600`) e se o original permanece
igual. Não confunda criação de cartaz com geração de fotografia por IA.

Para a geometria, use uma cópia de foto com resolução de até 4096 por lado
e teste os dois pedidos do README com **saídas novas**: `Redimensione ...`
e `Recorte ... começando em x,y com largura por altura pixels ...`.
Recuse a primeira tentativa, autorize outra com nome diferente e verifique
dimensões, enquadramento, transparência quando aplicável e ausência de
metadados privados. Confirme que repetir um destino existente falha sem
alterá-lo. Repita por voz somente se os caminhos/medidas forem transcritos
exatamente; registre falha de reconhecimento como tal, sem inferir sucesso
da edição textual. Registre tempo e consumo no notebook.

Depois de autorizar uma imagem nova, clique em **Ver imagem criada** na barra
da conversa. Confirme que a prévia é coerente, aparece dentro do Nexus, cabe
na tela, não substitui o arquivo e não abre outro programa. Verifique também
o indicador de rede, o botão de testes, a área de entrada e o histórico com
a janela em 770 × 570 e maximizada. Na autorização, confira leitura dos
detalhes, rolagem, negação, aceitação por texto/botão e cancelamento por Esc.
Essas observações são aceites humanos; a CI com Xvfb não as substitui.

Após `git pull --ff-only` e `python3 scripts/install_linux.py`, execute
`~/.local/bin/nexus-core --desktop` diretamente no terminal. **Deixe esse
terminal aberto enquanto conversa e testa as funções na janela.** O próprio
processo mostra `TESTE-LOCAL evento=... estado=...` com transições de chat,
escuta, reconhecimento, reprodução, câmera, análise visual e permissões.
`duracao_ms` mede o tempo do turno; não indica qualidade da resposta. Se a
resposta demorar, `processando` aparece a cada dez segundos. A escuta
registra o primeiro sinal de cada ciclo, sem imprimir o nível a cada amostra;
a câmera registra início e primeiro quadro, sem inundar o terminal por vídeo.
Copie as linhas `TESTE-LOCAL` da sessão e os erros relevantes para este chat.
Os logs não incluem conteúdo das perguntas, fala transcrita, imagem ou senhas.
`concluido` significa que o processo terminou, e você ainda precisa informar
se a resposta foi correta, audível e visualmente coerente. Não há homologação
automática de teclado Wayland nem de recuperação real.
Após dois ciclos com áudio sem transcrição, experimente **ALSA** no seletor de
microfone da janela, fale uma frase clara e compare com o teste isolado
`--recognition-test`; anote `pico` e `amostras` dos eventos seguintes sem
compartilhar o conteúdo da fala. Um pico de 100% pode indicar saturação, mas
isoladamente não diagnostica o dispositivo. Não marque escuta contínua como
aprovada até obter duas respostas faladas seguidas na própria janela.

Na mesma janela, confira o ponto **ONLINE/OFFLINE** do cabeçalho enquanto
desliga e religa a conexão pelo Ubuntu. O terminal deve registrar
`TESTE-LOCAL evento=rede estado=...` apenas na transição. Com o modo local
padrão, a consulta lê o estado passivo do NetworkManager; **NÃO VERIFICADO**
indica que o sistema não forneceu diagnóstico conclusivo. Esse teste não
comprova a disponibilidade de Ollama, PostgreSQL ou outros serviços locais.

Para avaliar peso e latência da visão, execute
`~/.local/bin/nexus-core --resource-check | python3 -m json.tool` antes de
abrir a câmera, logo após uma pergunta visual e depois de 50 segundos sem
outra análise. Compare também `ollama ps` e `free -h`. O diagnóstico lê
memória do Linux e `/api/ps` em loopback, sem iniciar inferência ou salvar
imagens. O perfil `eco` usa `keep_alive=0s`, enquanto `balanced` usa `45s`;
confirmar descarga e tempo de recarga depende do Ollama real no notebook.
Registre se o microfone
retoma após a resposta falada, além dos eventos `TESTE-LOCAL`.

## Registro guiado no terminal para compartilhar

Depois de atualizar a `main` e executar o instalador, rode diretamente no
terminal interativo (não redirecione a entrada padrão):

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main
git pull --ff-only
python3 scripts/install_linux.py
~/.local/bin/nexus-core --acceptance-log
```

O comando mostra `[EXECUTANDO]` antes de cada etapa e `[PASSOU]`, `[FALHOU]`
ou `[PENDENTE]` após a verificação. Ele consulta versão, PostgreSQL/Ollama,
dependências e status de recuperação; pede `SIM` separadamente antes de usar
Ollama, microfone, Vosk e um quadro da câmera. **Fale claramente quando o
terminal mostrar o teste de áudio**. A captura da câmera não salva imagem.
Abra a janela do assistente em **outro terminal** para responder às perguntas
de observação manual: `[RELATADO]` indica apenas sua declaração, ainda não
homologação independente. Depois de testar na janela, use `s` se funcionou ou
`f` se falhou. Use `n` ou Enter quando **não testou**. A etapa de Vosk mostra
backend, pico e quantidade de amostras, sem transcrição. Se ocorrer
`no_transcript`, fale uma frase clara durante os dez segundos e observe as
métricas; em outra rodada, experimente `NEXUS_AUDIO_INPUT=alsa` antes do
comando de aceite. Isso altera a captura apenas naquele processo.

Copie do cabeçalho `NEXUS CORE — REGISTRO DE ACEITE LOCAL` até `[RELEASE]` e
cole aqui no chat. A saída omite áudio, transcrição, resposta do modelo,
imagem, nomes de câmeras, senha e caminhos privados. Revise o texto antes de
compartilhar; não cole logs brutos do instalador nem o arquivo de credenciais.
Em execução sem terminal interativo, os testes físicos ficam `PENDENTE`.
Mesmo com tudo verde, o resumo não cria tag nem substitui teste de recuperação
real em instalação descartável.

## Identificação e instalação

No terminal do Ubuntu do usuário:

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main
git pull --ff-only
git rev-parse HEAD
grep '^version = ' pyproject.toml
python3 --version
echo "$XDG_SESSION_TYPE"
python3 scripts/install_linux.py --check
python3 scripts/install_linux.py
~/.local/bin/nexus-core --version
~/.local/bin/nexus-core --ubuntu-preflight | python3 -m json.tool
~/.local/bin/nexus-core-recover --status
```

O instalador pode pedir autorização para pacotes oficiais, modelos, usuário
PostgreSQL e configuração de atualização. Revise cada pedido. O resultado
esperado da versão é `Nexus Core 0.9.12`; o preflight deve indicar login
PostgreSQL autenticado. Não copie senhas, tokens nem caminhos privados para
issues ou PRs. O comando de recuperação acima apenas consulta o status:
**não execute rollback em uma instalação de uso real para homologar**.

## Conversa, áudio e câmera

```bash
~/.local/bin/nexus-core --agent-prompt 'Responda em uma frase: você está funcionando?'
~/.local/bin/nexus-core --microphone-test | python3 -m json.tool
~/.local/bin/nexus-core --recognition-test | python3 -m json.tool
~/.local/bin/nexus-core --camera-list | python3 -m json.tool
~/.local/bin/nexus-core --camera-test 0 | python3 -m json.tool
~/.local/bin/nexus-core --desktop
```

O índice `0` é apenas exemplo; use o índice retornado por `--camera-list`.
Confirme que a resposta do Ollama é nova e pertinente, que o teste físico
transcreve uma frase falada, que as vozes feminina e masculina são audíveis,
e que a prévia da webcam exibe imagem. Com a câmera aberta, faça uma pergunta
visual autorizada e compare a resposta ao quadro visto; a prévia não equivale
a inferência contínua de todos os quadros.

## Ações e permissões

Na janela, digite ou fale **“Crie uma pasta chamada NexusAceite”**. Confira o
caminho completo na autorização falada e visual. Primeiro **Negar**: a pasta
não deve existir. Faça um segundo pedido e autorize por botão ou pela frase
exata **“Nexus, autorizo esta ação”**: deve aparecer uma única pasta na sua
home. Confira a trilha de auditoria e remova a pasta depois do teste.

Repita com **“Abra o navegador”**. O navegador padrão do Ubuntu deve abrir
sem diálogo adicional; confira antes com `xdg-settings get default-web-browser`
e confirme que nenhuma URL específica foi carregada pelo Nexus. Diga também
uma frase imprecisa como **“abrir na beira do”**: o assistente deve pedir para
repetir, sem abrir nada. Para testar negação e confirmação de aplicativo,
use **“Abra o gerenciador de arquivos”**. Suspenda a escuta e confira que a
fala de autorização não instrui o uso do microfone pausado. Em Wayland,
**não marque navegação/digitação
em outras janelas como aprovada**: a implementação atual exige X11. Se desejar
testá-la em sessão X11 local, use separadamente
`python3 -m scripts.x11_manual_acceptance`, que cria uma janela temporária e pede
consentimento por operação.

## Registro de evidências

Preencha esta tabela somente com observações reais. Use `PENDENTE`,
`APROVADO`, `FALHOU` ou `NÃO APLICÁVEL`; anexe resumo de comandos sem segredos
e descreva qualquer erro reproduzível.

| Critério | Resultado | Evidência resumida |
| --- | --- | --- |
| SHA da main, Ubuntu/Python/sessão registrados | PENDENTE | — |
| Instalação, login PostgreSQL e status de recuperação | PENDENTE | — |
| Resposta pertinente do Ollama sem internet externa | PENDENTE | — |
| Microfone e transcrição Vosk isolados | APROVADO | PipeWire, `transcribed`, pico 100% no checkout `0710f9a`; precisão da frase não registrada |
| Escuta e resposta a duas falas seguidas na janela | FALHOU | Repetidos `sem_transcricao` de aproximadamente 8,5 s na sessão enviada |
| Voz feminina e masculina audíveis, pausa e retomada | PENDENTE | — |
| Webcam, foto e descrição coerente após consentimento | PENDENTE | — |
| Indicador ONLINE/OFFLINE na janela | APROVADO | Transições `online`/`offline`/`online` no log enviado |
| Latência e recursos da análise visual | PENDENTE | Uma análise levou 118,9 s e fala 23,2 s; medir após diagnóstico e ajustes no notebook |
| Criar pasta: negação e autorização individuais | PENDENTE | — |
| Navegador padrão abre sem diálogo; fala ambígua não abre | PENDENTE | — |
| Abrir gerenciador: negação e autorização individuais | PENDENTE | — |
| Permissão falada, digitada e por botão; cancelamento | PENDENTE | — |
| Navegação/digitação em janela X11 temporária | PENDENTE | — |
| CI de `push` para o SHA final da main | PENDENTE | — |

**Decisão de release: PENDENTE.** Registre qualquer falha como falha; CI verde
não altera esta decisão automaticamente. Recuperação por reversão real e
atualização gerenciada devem ser ensaiadas somente em uma instalação
descartável com backup e plano de restauração, nunca inferidas pelo `--status`.
