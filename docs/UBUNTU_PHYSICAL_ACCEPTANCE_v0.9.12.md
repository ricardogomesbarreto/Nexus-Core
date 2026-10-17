# Aceite físico Ubuntu — Nexus Core v0.9.12

**Estado em 17/10/2026: PENDENTE.** Este documento é um roteiro de execução
no notebook do usuário. Nenhuma etapa abaixo está marcada como aprovada pela
CI nem pelos testes simulados. Registre data, versão, SHA, sessão gráfica,
resultado observado e eventuais falhas antes de propor uma tag.

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

**Revisão local da proposta de indicador e recursos (17/10/2026):** 1.480
testes passaram, 111 foram ignorados neste ambiente sem display, serviços e
hardware Ubuntu; o wheel 0.9.12 foi gerado e contém os módulos novos. O
diagnóstico `--resource-check` funcionou sem Ollama neste ambiente, sem
iniciar aplicação, inferência ou rede externa. Isso não mede a memória, o
tempo de resposta ou o aquecimento do notebook. A proposta ainda depende de
CI para o SHA final na `main` e das verificações físicas abaixo. Nenhuma tag
foi criada.

**Teste adicional recebido em 17/10/2026:** no notebook, a tentativa de
aplicar o patch falhou porque o arquivo não existia em `~/Downloads`; portanto
o programa executado não tinha o indicador de rede nem `--resource-check`.
Na sessão registrada, o Vosk reconheceu algumas falas incorretamente e várias
capturas de trinta segundos terminaram sem transcrição. Abrir o navegador
precisou de confirmação; uma foto visual levou cerca de 111 segundos para
analisar. São falhas observadas da instalação anterior, não aceite. A revisão
local agora limita a espera sem palavras a oito segundos, solicita repetição
para comando ambíguo, abre apenas o navegador padrão sem confirmação extra e
oferece nova foto com consentimento por captura. Ela ainda não foi instalada
nem testada fisicamente nesse notebook; medir acerto de voz e latência da
visão novamente antes de publicar qualquer tag.

## Logs ao vivo enquanto usa o assistente

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
| Microfone e transcrição Vosk de fala real | PENDENTE | — |
| Voz feminina e masculina audíveis, pausa e retomada | PENDENTE | — |
| Webcam, foto e descrição coerente após consentimento | PENDENTE | — |
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
