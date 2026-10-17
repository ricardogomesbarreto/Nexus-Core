<p align="center">
  <img
    src="assets/brand/nexus-core-logo.png"
    alt="Nexus Core"
    width="980"
  >
</p>

<p align="center">
  <img alt="Python 3.12 ou superior" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white">
  <img alt="PostgreSQL local" src="https://img.shields.io/badge/PostgreSQL-local-4169E1?logo=postgresql&logoColor=white">
  <img alt="Linux desktop" src="https://img.shields.io/badge/Linux-desktop-FCC624?logo=linux&logoColor=black">
  <img alt="Código v0.9.12 integrado; release pendente" src="https://img.shields.io/badge/c%C3%B3digo-v0.9.12%20na%20main-722F37">
  <img alt="Licença MIT" src="https://img.shields.io/badge/licen%C3%A7a-MIT-2F855A">
  <a href="https://github.com/ricardogomesbarreto/Nexus-Core/actions/workflows/ci.yml"><img alt="CI do Nexus Core" src="https://github.com/ricardogomesbarreto/Nexus-Core/actions/workflows/ci.yml/badge.svg?branch=main"></a>
</p>

# Nexus Core

Assistente pessoal de inteligência artificial **local-first, modular e seguro**, desenvolvido para execução no desktop Linux sobre fronteiras explícitas entre inteligência, autorização e execução.

> **Código na `main`:** `v0.9.12 — Authorized Desktop Actions`; desenvolvimento integrado, sem tag deste marco.<br>
> **Publicação estável:** v0.7.2 é a última release oficial; o código v0.7.3–v0.9.12 permanece sem homologação física e sem release estável; [releases](https://github.com/ricardogomesbarreto/Nexus-Core/releases)<br>
> **Linha em evolução:** `v0.9.x — Multimodal Interface` (v0.9.12 acrescenta uma rota local para pedido explícito de pasta, com confirmação por ação)<br>
> **Plataforma e distribuição:** Ubuntu Desktop com `VERSION_ID` reconhecido e Python 3.12+; instalação condicionada às dependências e ao login PostgreSQL local; outras distros em estudo; aplicativo local sob licença MIT<br>
> **Interface atual:** janela nativa Linux (Tk), texto e voz local feminina/masculina<br>
> **Banco único:** PostgreSQL local<br>
> **Validação:** suíte Linux executada na CI com PostgreSQL, Docker e display virtual<br>
> **Primary Platform:** Linux<br>
> **Local Model Runtime:** Ollama<br>
> **Reference Model:** `qwen3:1.7b`<br>
> **Desktop Application:** Native<br>
> **Web Application:** No<br>
> **Primary Visual Identity:** Wine Red<br>
> **Primary Color:** `#722F37`<br>
>
> [Identidade Nexus Line](docs/ICONOGRAFIA.md) · marca oficial, iconografia Core e fundação visual desktop nativa

As [diretrizes do projeto](docs/PROJECT_GUIDELINES.md) incluem o uso como
ambiente local para estudo de segurança, CTF e hacking autorizado, com escopo
definido, confirmação de ações e auditoria. Essa finalidade não habilita
automaticamente ferramentas de rede ou execução irrestrita no host.

As seções de versões abaixo preservam a evolução da implementação. Código
integrado à `main` ainda depende de testes em um Ubuntu físico com Wayland
e, para a automação específica de teclado, X11; além de
PostgreSQL, Ollama, voz, câmera, instalação e recuperação antes de uma nova
tag/release estável. Os workflows de publicação permanecem bloqueados.

## v0.9.12 — Ações autorizadas no desktop (código; aceite físico pendente)

Pedidos exatos como **“Crie uma pasta chamada Projetos”** (também com o
prefixo **“Nexus,”**) agora selecionam
uma única pasta diretamente dentro da home do usuário, sem aguardar a
interpretação do Ollama. Aceita somente um nome simples (até 64 caracteres,
sem barras nem pontos); o contrato `create_directory`, a política de caminhos,
a janela com alvo/risco e a confirmação individual continuam obrigatórios.
Uma frase transcrita incorretamente pode escolher outro nome: confira o caminho
mostrado **antes** de autorizar. Perguntas sobre capacidades e caminhos com
subpastas não entram nessa rota exata.

Os comandos exatos para abrir navegador, gerenciador de arquivos ou terminal
também solicitam confirmação por ação e aceitam uma sessão gráfica Wayland.
Digitação e navegação em **outras janelas** continuam limitadas a X11 local.
O portal de desktop exige concessão da sessão pelo sistema e não fornece a
mesma identidade de janela exigida pela proteção atual; essa automação Wayland
segue pendente de projeto e validação, sem contornar as permissões do ambiente.

O [roteiro de aceite físico v0.9.12](docs/UBUNTU_PHYSICAL_ACCEPTANCE_v0.9.12.md)
registra evidências de instalação, PostgreSQL, conversa Ollama, reconhecimento
de fala, saída feminina e masculina, câmera, ações e recuperação. Seu estado
inicial é **PENDENTE**; testes automatizados não preenchem o aceite de hardware.
O workflow de publicação manual verifica agora a CI de `push` aprovada para o
SHA exato da `main`; o bloqueio de publicação permanece ativo. Não há tag
v0.9.12 nem tags retroativas para marcos ainda não homologados.

## Correções e auditoria do código atual

### Autorização por voz, texto ou botão (código em desenvolvimento)

As permissões de ferramentas com confirmação individual aparecem em uma
janela com **ação, risco, alvo e recursos**. A janela agora inclui uma caixa
de texto: digite **AUTORIZAR** ou **NEGAR** e pressione Enter. Também é
possível usar os botões **Autorizar esta ação** e **Negar**. Quando a escuta
estiver ativa, diga exatamente **"Nexus, autorizo esta ação"** ou
**"Nexus, nego esta ação"**. Respostas isoladas como "sim" ou texto ambíguo
não autorizam nada. Se a escuta estiver pausada ou o reconhecimento falhar,
as opções de texto e botões permanecem disponíveis.

Com a leitura em voz alta habilitada, o assistente pergunta pela autorização
em voz, informa a ação resumida e orienta a conferir alvo e risco na janela.
O microfone da confirmação só inicia depois que a pergunta falada termina,
para não reconhecer a própria voz do assistente. Desligar a leitura em voz
alta mantém a janela e os meios de resposta por texto, botão e voz ativa.
Se a reprodução falhar, a decisão pela janela continua disponível.

A escuta da confirmação é separada da conversa normal, não aciona o Ollama,
não grava áudio nem amplia o escopo da permissão. Cada decisão vale para uma
única operação; **Esc**, fechar a janela, cancelamento ou tempo esgotado
negam a execução. O `SecurityGate` revalida alvo e política depois de uma
aprovação. O reconhecimento de voz precisa de validação física no Ubuntu;
esta alteração integra o código da v0.9.12 sem publicar release estável.

### Ações locais autorizadas e resposta de voz (código em desenvolvimento)

- **Criar pasta:** pedidos por texto ou voz podem propor `create_directory`
  para criar uma pasta por vez dentro da área autorizada do usuário. A frase
  exata acima usa uma rota local; outros pedidos continuam sujeitos ao modelo.
  Exige confirmação individual, pasta principal existente e caminho sem links
  simbólicos. Não modifica pastas protegidas ou arquivos já existentes.
- **Abrir aplicativos:** `Abra o navegador`, `Abra o gerenciador de arquivos`
  e `Abra o terminal` são comandos exatos que dispensam espera pelo Ollama,
  mas ainda exigem confirmação. O iniciador seleciona somente aplicativos
  conhecidos instalados nos caminhos de sistema; não recebe argumentos ou
  comandos do modelo. Pode ser chamado no Wayland com sessão gráfica ativa.
  O resultado confirma o envio da solicitação de abertura, não a interação
  subsequente com o aplicativo.
- **Escuta após silêncio:** ao parar a entrega de bytes pelo PipeWire depois
  de uma fala, o reconhecedor verifica o tempo de pausa e finaliza o turno;
  antes podia esperar o limite total da captura. Testes simulados cobrem o
  caso. Latência real e qualidade da transcrição exigem teste físico.

Essas mudanças foram integradas ao código até a versão **0.9.12**;
não representam uma nova tag ou release. Abrir arquivos no aplicativo padrão,
controlar aplicativos no Wayland, inferência de vídeo contínuo em tempo real,
conversa simultânea durante a resposta de voz e um conjunto completo de
ferramentas de pentest **permanecem pendentes**.

### Prontidão e conversa mais clara na versão de código v0.9.11

- **Início mais rápido da escuta:** a saudação falada agora se limita a
  **"Bem-vindo ao Nexus Core, [nome]"**. O nome vem da conta Linux local
  quando é seguro pronunciá-lo; se não houver nome válido, a frase termina
  em **"Nexus Core"**. O diagnóstico completo continua no texto da janela.
  Como o microfone não escuta a própria síntese, a frase curta reduz a
  espera antes do primeiro turno de voz.
- **O que posso fazer?** Pergunte **"O que você pode fazer?"** por texto ou
  voz. A resposta imediata, gerada localmente sem consulta ao modelo, lista
  as capacidades efetivamente implementadas e limitações do Wayland.
- **Prontidão da webcam:** a interface indica **câmera iniciando** até chegar
  o primeiro quadro. Perguntas e fotos durante a prévia aceitam apenas um
  quadro com até três segundos de idade; se o vídeo parar, o assistente
  informa a falha em vez de descrever uma imagem antiga como atual.
  Perguntas como **"O que estou segurando?"** podem usar o vídeo já
  autorizado. Outros assuntos continuam no chat de texto.
- **Diagnóstico físico separado do modelo:** `--camera-list` enumera os
  dispositivos V4L2 acessíveis sem obter imagem; `--camera-test INDEX`
  captura um único quadro com consentimento implícito no comando explícito,
  informa resolução ou erro em JSON e descarta os pixels. O teste não abre
  PostgreSQL, não grava imagem e não consulta o Ollama. Execute primeiro:

  ```bash
  ~/.local/bin/nexus-core --camera-list | python3 -m json.tool
  ~/.local/bin/nexus-core --camera-test 0 | python3 -m json.tool
  ```

  Substitua `0` pelo índice listado. O segundo comando abre a câmera de
  verdade e falha com código de saída 1 se ela não entregar uma foto.
- **Limite do transporte local:** respostas HTTP do Ollama são lidas até
  8 MiB; uma resposta maior produz erro controlado, sem leitura ilimitada
  na memória. Esse limite é distinto do tamanho das imagens enviadas.

Essas melhorias foram verificadas em testes de código e CI. A interação
física de microfone, alto-falantes, webcam e tempo de inferência exige
validação no Ubuntu do usuário. O vídeo é contínuo somente como prévia:
as análises são quadros pontuais durante perguntas, sem interpretação
automática de cada quadro, conversa full-duplex ou automação livre do PC.

### Webcam ao vivo e perguntas faladas (código v0.9.11)

O botão **Câmera ao vivo** e `Ctrl+Shift+K` ligam uma prévia contínua local da
webcam, após selecionar o dispositivo e autorizar a sessão. O mesmo botão,
o controle da prévia ou o comando **"Feche a câmera"** interrompem a
captura. O FFmpeg gera quadros JPEG em memória; o aplicativo mantém só o
último quadro e não grava o vídeo em arquivo nem no PostgreSQL. A janela
mostra **Visão: câmera iniciando** até receber uma imagem e, depois,
**Visão: câmera ligada** enquanto a prévia está ativa.

O microfone pode continuar ouvindo durante a prévia. Diga **"Abra a câmera"**,
depois **"Na câmera, o que você vê?"** ou faça outra pergunta que mencione
a câmera; é possível escrever a pergunta no chat também. Cada pergunta
explícita envia **um quadro recente** ao modelo visual do Ollama local,
mostra a resposta no chat e a lê em voz alta quando a voz está habilitada.
O vídeo permanece aberto para outras perguntas. Não há análise automática
de todos os quadros: a latência da resposta depende do modelo e do hardware.
O comando `--vision-camera INDEX` continua sendo uma captura única no terminal.

**Foto da câmera** (`Ctrl+Shift+P`) restaura a captura única com prévia e
análise após autorização específica. Com vídeo desligado, abre a webcam só
para a foto; com vídeo ligado, usa o quadro mais recente da mesma sessão,
sem disputar o dispositivo com outro FFmpeg. A janela de prévia contínua
também tem **Analisar foto deste vídeo**. Por voz, **"Tire uma foto"** ou
**"Analise uma foto da câmera"** solicita a mesma autorização. Se FFmpeg
falhar por câmera ocupada, permissão negada ou formato incompatível, a
janela informa o motivo em texto e, quando habilitada, por voz. A busca
sem dispositivo diferencia ausência de `/dev/video`, falta de permissão e
nós sem captura V4L2. Uma pergunta visual demanda um modelo Ollama visual
instalado; a prévia contínua sozinha não produz inferência em tempo real.

**Estado das ações por voz:** a transcrição de Vosk encaminha pedidos ao
mesmo planejador e às mesmas permissões do chat. O código lista diretórios,
lê arquivos autorizados, cria uma pasta por operação e solicita a abertura
de um aplicativo de uma lista limitada, sempre mediante confirmação nas
ações de alteração/abertura. Navegação e digitação seguem restritas a X11;
abrir arquivos no aplicativo padrão e controlar janelas no Wayland ainda
não possuem ferramenta homologada. O sandbox de terminal não altera o
sistema do usuário.

**Auditoria de compatibilidade de câmera (código v0.9.11):** a busca V4L2
inclui agora dispositivos numerados de `/dev/video0` até `/dev/video255`.
Os nós somente de metadados continuam excluídos por `VIDIOC_QUERYCAP`.
O seletor da janela e `--vision-camera` aceitam esses índices; a captura
continua a exigir autorização por foto. Esta correção foi validada por testes
de código e ainda precisa de confirmação com webcam física no Ubuntu.

### Persistência automática do assistente e preferências do usuário (v0.9.11)

O NEXUS CORE conserva as escolhas do usuário **entre reinicializações**,
sem internet e sem depender da disponibilidade do Ollama. A gravação é
automática quando uma preferência muda e durante o encerramento normal;
não é necessário reconfigurar o assistente a cada abertura.

| Configuração | Comportamento após reiniciar |
| --- | --- |
| **Voz** | Mantém **Masculina** ou **Feminina**, inclusive quando trocada por comando de voz |
| **Leitura de respostas em voz alta** | Mantém ativada/desativada; a saudação inicial obedece a essa escolha |
| **Palavra de ativação** | Mantém a exigência opcional de dizer "Nexus" |
| **Microfone** | Mantém **Automático / PipeWire / ALSA**, sem alterar o áudio global do Ubuntu |
| **Escuta** | Respeita a escolha de **Pausar escuta** mesmo depois de fechar e reabrir |
| **Janela** | Restaura a última largura e altura usadas, respeitando limites seguros |
| **Salvar conversas** | Preserva a decisão de manter ou não o histórico textual local |

A configuração é um documento JSON versionado em
`$XDG_CONFIG_HOME/nexus-core/preferences.json` (ou
`~/.config/nexus-core/preferences.json`). É gravado por
**substituição atômica**, com arquivo de permissões **0600** e pasta
privada **0700**, sem transmissão para a internet. Chaves desconhecidas,
valores inválidos, arquivos malformados ou links simbólicos inseguros
não são carregados silenciosamente. Caso o salvamento falhe, a janela
avisa o usuário; nenhuma alteração no banco de dados ou no SO é exigida.

**Histórico textual local:** a opção visível **Salvar conversas** inicia
selecionada para novas instalações, mas pode ser desmarcada a qualquer
momento. São armazenadas até **200 trocas de mensagens textuais comuns**
em `$XDG_DATA_HOME/nexus-core/chat-history.json` (ou
`~/.local/share/nexus-core/chat-history.json`), com as mesmas
permissões privadas e gravação atômica. As últimas **6 conversas**
compõem o contexto curto ao reiniciar e aparecem no histórico da
janela. É possível usar **Apagar histórico** após uma confirmação.
Desativar novos salvamentos **não apaga dados antigos**; use o botão
para excluir o histórico existente.

**Limites importantes de privacidade:** o arquivo de histórico contém
texto legível pelo próprio usuário Linux, não criptografia de ponta a
ponta. Não arquiva áudio, imagens, frames de tela ou câmera, conteúdo
bruto de ferramentas/arquivos, autorizações temporárias ou senhas
do PostgreSQL. O banco de **memórias explícitas** continua separado,
com seu próprio ciclo de retenção e comandos de gerenciamento.
Operações autorizadas e auditoria permanecem sob `SecurityGate`;
reabrir o programa **nunca restaura permissões de captura anteriores**.

A persistência foi implementada em
`nexus/desktop/preferences.py` e `nexus/desktop/chat_archive.py`,
integrada à janela e ao contexto de `ChatSession`, com testes de
gravação/recuperação, permissões, reinicialização Tk/Xvfb, exclusão,
arquivos corrompidos, e distinção entre conversa comum e saídas
sensíveis de ferramentas. A **v0.9.11** permanece sem tag/release
estável até homologação física no Ubuntu.

### Diagnóstico e recuperação de visão e voz no Ubuntu (v0.9.11)

Esta rodada corrige falhas observadas em **capturas reais do notebook**:
o modelo multimodal `gemma3:4b` aparece instalado, porém a requisição
visual falha; e a escuta reconhece fala inicialmente, depois parece parar.

**Visão local (Ollama).** Um modelo estar listado não comprova que a
inferência caiba na RAM do computador. O processamento agora reduz
imagens grandes para um limite de 1536 pixels no maior lado e, se o
PNG expandir excessivamente, emprega JPEG sem EXIF/metadados, apenas
para a inferência no Ollama local. Mantém a política existente de 6 MiB
de entrada, 4096 px e 8 MP. As requisições multimodais usam contexto
delimitado, temperatura baixa e resposta de tamanho limitado. Em
vez do antigo erro genérico `não conseguiu analisar`, agora distingue:

- **HTTP 400/413/422:** requisição ou formato/modelo incompatível;
- **HTTP 404:** modelo visual não encontrado;
- **HTTP 500/502/503/507:** falha interna ou recursos insuficientes;
- **Timeout:** o modelo não respondeu dentro do limite configurado;
- **Ollama desconectado:** serviço local indisponível, mesmo sem
  necessidade de conexão à internet.

**Voz contínua (PipeWire/ALSA + Vosk).** A gravação PCM no Ubuntu passa
a verificar a entrada do gravador em intervalos curtos, em vez de esperar
até receber um bloco inteiro de 8000 bytes. A pausa, o encerramento e
as trocas de backend podem, assim, interromper a escuta em tempo hábil.
Falhas transitórias de abertura/leitura podem tentar reconectar até duas
vezes, sem loops ilimitados. Se continuar falhando, o programa explicita
o erro e mantém o chat por teclado disponível. Ao ocorrer silêncio
repetido, o assistente diferencia **sem sinal** de **sinal captado, mas
sem transcrição Vosk**.

Para confirmar a causa do erro visual, execute **sem abrir a webcam**
(estes comandos não enviam fotos):

```bash
ollama list
ollama ps
free -h
systemctl status ollama --no-pager
```

Se o Ollama foi instalado como serviço do usuário, confira também
`systemctl --user status nexus-core-ollama.service --no-pager`.
O código não consegue diagnosticar a RAM nem o driver da webcam
remotamente apenas a partir de uma captura de tela; **o usuário deve
verificar esses resultados no próprio Ubuntu**. Se estiver usando o
ambiente virtual gerenciado, os comandos devem ser executados como
usuário comum e sem `sudo` para iniciar o aplicativo.

**Teste da escuta local, sem internet:**

```bash
~/.local/bin/nexus-core --microphone-test
~/.local/bin/nexus-core --recognition-test
NEXUS_AUDIO_INPUT=alsa ~/.local/bin/nexus-core --recognition-test
~/.local/bin/nexus-core --desktop
```

As correções preservam os consentimentos por captura, operação local-first,
o histórico temporário e a identidade visual. A CI verifica mocks de
Ollama, PCM local e desktop Tk/Xvfb, **não substitui a homologação de
RAM, PipeWire, Vosk, webcam e GPU no notebook físico**. Sem alteração
de versão/tag/release estável antes do teste físico.

### Operação totalmente local: respostas novas e voz natural (v0.9.11)

O NEXUS CORE executa as conversas pelo **Ollama instalado no próprio
computador**, usando exclusivamente o endereço de loopback
`http://127.0.0.1:11434`. O padrão `NEXUS_OFFLINE_MODE=true` mantém o
runtime offline e não depende de acesso externo para inferência, transcrição
Vosk, síntese de voz ou processamento visual, **desde que os modelos
necessários já estejam instalados**. A aquisição inicial dos modelos
e atualizações são processos separados que exigem conexão e consentimento.

- **Correção de repetições:** quando duas perguntas diferentes resultarem
  literalmente na mesma resposta do modelo conversacional local, o
  assistente fará **uma única tentativa de resposta sem histórico e sem
  permissão de ferramentas**. Se a nova resposta continuar idêntica,
  exibirá um diagnóstico claro, em vez de apresentar a resposta anterior
  como se ela atendesse ao novo pedido. Uma pergunta idêntica pode
  legitimamente produzir a mesma resposta. Erros de serviço não serão
  confundidos com respostas válidas nem adicionados ao histórico.
- **Voz natural:** Markdown gerado pelo modelo (como
  `**negrito**`, `*itálico*`, listas e títulos) é convertido em
  frases antes de chamar o Piper, RHVoice ou eSpeak NG. Trechos de código
  extensos não são recitados; o chat conserva os detalhes. A narração
  usa pontuação e tem limite de extensão para não prender o áudio por
  um tempo excessivo.
- **Câmera, imagem e tela:** o resultado visual aparece em texto sem
  asteriscos decorativos; a mesma resposta é narrada **sem pronunciar
  marcadores Markdown**. A captura permanece única e autorizada, sem
  gravação persistente ou serviços de IA remotos.
- **Indisponibilidade local:** se o Ollama não estiver acessível,
  a interface informa a falha do serviço local; não reutiliza uma
  resposta salva, não consulta modelo externo e não inventa conteúdo.

**Validação no Ubuntu, com a internet desligada:**

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main
git pull --ff-only
python3 scripts/install_linux.py
ollama list
curl --noproxy '*' -fsS http://127.0.0.1:11434/api/tags
~/.local/bin/nexus-core --desktop
```

Os comandos `git pull` e a instalação/atualização de modelos exigem
conexão quando há itens a baixar; **execute-os antes** de desligar a
internet. No teste offline, use somente `ollama list`, a consulta local
`curl` e a janela do assistente. Se o Ollama não responder em loopback,
confira `systemctl --user status nexus-core-ollama.service` quando usa
a instalação gerenciada ou `systemctl status ollama` para uma
instalação global. Teste duas perguntas **diferentes** e uma captura
visual já com modelo multimodal instalado. O status físico de webcam,
áudio e síntese deve ser verificado no notebook.

A CI usa modelos/alto-falantes simulados e não substitui essa homologação
no hardware. Não há mudança de versão, tag, release estável, dados
armazenados nem permissões de segurança nesta correção.

### Conversa, imagens, câmera, tela e microfone — aperfeiçoamentos v0.9.11

O NEXUS CORE é um **assistente conversacional local**: responde perguntas,
propõe ideias úteis e oferece ações do computador **somente quando solicitadas,
mediadas pelo SecurityGate e pelas permissões aplicáveis**. Não é uma
implementação da personalidade nem das capacidades fictícias de um filme.

- **Enviar:** pressione **Enter** para enviar; **Shift+Enter** insere
  uma quebra de linha; **Ctrl+Enter** continua disponível. Botão Enviar
  e atalho percorrem o mesmo caminho de validação e cancelamento.
- **Conversa:** perguntas cotidianas e o modo Sugerir seguem a resposta
  de texto natural, sem gerar propostas de ferramentas. Perguntas exatas
  sobre hora/data usam o relógio do próprio computador, sem consultar
  Ollama nem executar `system_info`. Informações do sistema solicitadas
  explicitamente são apresentadas em linguagem legível, não JSON bruto.
- **Imagem:** após seleção e autorização, exibe uma **prévia da imagem
  realmente carregada**. A descrição requer um **modelo multimodal Ollama**
  instalado, como `gemma3:4b`; o modelo de texto `qwen3:1.7b`
  isoladamente **não analisa imagens**. A aplicação consulta a lista de
  modelos locais, prefere o modelo visual solicitado quando instalado e
  pode usar outro modelo visual instalado. Sem modelo disponível informa
  a instalação necessária em vez de inventar uma descrição. Nenhuma
  imagem é enviada a serviço remoto.
- **Ativar análise visual no Ubuntu** (download grande, só com decisão
  consciente do usuário):

  ```bash
  ollama list
  ollama pull gemma3:4b
  ~/.local/bin/nexus-core --desktop
  ```

  Se desejar fixar um modelo visual compatível já instalado, configure
  `NEXUS_VISION_MODEL`. Somente modelos locais com famílias visuais
  reconhecidas são aceitos; não há download automático silencioso.
- **Câmera e tela:** o clique e a autorização por análise geram **uma
  única foto/captura**, exibida na janela de prévia e depois interpretada
  pelo Ollama multimodal. Não existe streaming permanente. No Wayland,
  **Tela** solicita o alvo tela/monitor ao portal XDG. Sessões antigas
  que não possuem `AvailableTargets` ainda podem usar o diálogo
  interativo de captura de tela; solicitações de **janela exclusiva**
  continuam bloqueadas onde não é possível garantir a restrição.
  A prévia representa o quadro capturado, não vídeo ao vivo.
- **Microfone:** a GUI oferece **Automático / PipeWire / ALSA**.
  A escolha afeta apenas o reconhecedor do NEXUS CORE, não troca a
  entrada global do Ubuntu. Use a opção ALSA quando a entrada padrão
  PipeWire não resultar em transcrição e compare o indicador de sinal.
  Sem áudio recebido, a animação permanece parada; a intensidade
  sonora por si só não garante que o Vosk reconheça palavras.
- **Boas-vindas faladas:** preserva a função integrada na PR #46,
  com síntese local antes de ativar a escuta, evitando o retorno
  acústico. As mensagens nunca declaram os dispositivos "100%
  funcionais" antes da homologação física.

Para investigar hardware sem enviar gravações:

```bash
~/.local/bin/nexus-core --microphone-test
~/.local/bin/nexus-core --recognition-test
NEXUS_AUDIO_INPUT=alsa ~/.local/bin/nexus-core --recognition-test
```

**Limites de aceite:** CI Ubuntu/Python 3.12/PostgreSQL/Xvfb valida código,
autorização, renderização e integrações simuladas; somente testes no
computador físico validam câmera, portal Wayland, sinal acústico e
reconhecimento real. A versão **v0.9.11** permanece sem nova
tag/release estável até esse aceite.

### Interface desktop renovada e boas-vindas verificáveis

A interface Tkinter do **NEXUS CORE v0.9.11** recebeu uma reorganização
visual, mantendo **a logo original** e a identidade da marca (vinho
`#722F37`, cabeçalho `#241c24` e tons claros de apoio). A mudança
se aplica somente à apresentação, sem alterar a autorização das ações.

- **Janela redimensionável:** abertura em 980 × 720 px, com mínimo de
  770 × 570 px. A transcrição ocupa o espaço expansível; entrada de texto,
  botões e indicadores ficam no rodapé reservado, sem disputa por espaço.
- **Ações distribuídas:** botões `Sugerir`, `Enviar` (destaque vinho),
  `Cancelar`, `Pausar escuta` e `Desligar assistente` em **cinco colunas
  de larguras iguais**. O texto de status fica em uma faixa própria, abaixo
  das ações, não comprimindo mais os botões.
- **Visão:** `Imagem`, `Tela`, `Foto da câmera` e `Câmera ao vivo` recebem a mesma largura
  disponível e continuam exigindo consentimento por análise. Ícone animado
  de microfone, porcentagem PCM, estado de escuta, saída de voz e visão
  continuam visíveis e não implicam funcionamento físico comprovado.
- **Acessibilidade e atalhos:** comandos e atalhos anteriores permanecem,
  inclusive `Ctrl+Enter` para enviar e `Ctrl+Shift+M` para pausar/retomar
  escuta. As cores de botões usam `ttk` com tema `clam` quando disponível.
- **Boas-vindas faladas:** ao abrir a janela, a conversa exibe uma saudação
  detalhada; o assistente também fala **uma saudação curta e personalizada
  em português brasileiro, automaticamente**, utilizando a voz masculina/feminina
  selecionada no menu e a síntese local Piper/RHVoice/eSpeak NG já
  existente. Não consulta Ollama nem executa ações. A fala só é iniciada
  quando **Ler respostas em voz alta** está habilitado.
  A escuta do microfone **começa somente após a fala terminar**,
  evitando reconhecer a própria voz do assistente. Se TTS estiver
  desativado, a escuta começa normalmente; se a reprodução falhar, um
  aviso textual é exibido e a conversa permanece disponível.
  A reprodução não é repetida automaticamente na mesma sessão.
  Caso `app.status().database` confirme a inicialização do PostgreSQL,
  o texto apresenta especificamente esse estado; de outro modo,
  informa apenas que a janela abriu.

**O texto de boas-vindas não declara que o Nexus Core está “100%
funcional”.** Iniciar o banco e a janela não valida Ollama, Vosk, câmera,
alto-falantes, dispositivos reais nem conectividade. Essas verificações
permanecem separadas e dependem dos testes reais no desktop Ubuntu. A
apresentação é intencionalmente honesta quanto ao nível de prontidão.
O módulo `nexus/desktop/welcome.py` isola essa decisão para testes
automatizados.

Esta alteração **não cria nova tag nem release estável**: o código
continua em v0.9.11, sujeito à homologação física dos recursos de mídia.

### Diagnóstico físico da webcam, microfone e arquivos (Ubuntu)

A **v0.9.11** inclui correções de uso a partir de testes físicos no notebook,
sem alterar o design ou publicar uma nova versão/tag:

- **Câmera V4L2:** a captura autorizada de **uma única foto** agora ignora
  os oito primeiros quadros do FFmpeg, permitindo que a exposição automática
  estabilize. Quando a imagem permanecer quase totalmente preta, a análise
  visual é interrompida e a janela informa que pode existir tampa física de
  privacidade fechada, câmera ocupada por outro aplicativo ou iluminação
  inadequada. O programa não deve atribuir uma captura preta ao modelo como
  se fosse uma foto válida. **Não** existe vídeo contínuo nem abertura
  automática sem autorização explícita.
- **Áudio/indicador:** a animação existente acompanha os níveis reais da
  captação, agora atualizados a cada ~0,25 s durante a escuta. O rótulo
  `Entrada: N%` ajuda a perceber o sinal e distinguir o ícone parado de
  problemas de entrada. Sem entrada PCM, o ícone permanece no estado
  inativo — nunca simula uma voz que o microfone não captou.
- **Diagnóstico de transcrição:** `--recognition-test` acrescenta
  `backend`, `peak_percent`, `level_samples` e `diagnosis` ao JSON.
  **Pico acima de zero não prova que o Vosk entendeu palavras.** Uma
  gravação `--microphone-test` com sinal e o `--recognition-test`
  sem sinal exigem verificação da entrada padrão ou do backend de áudio
  usado pela aplicação.
- **Imagens e pastas:** o diálogo nativo abre preferencialmente
  `~/Imagens`, `~/Pictures` ou `~/Downloads` (se existirem) e exibe
  formatos em filtros separados: PNG, JPEG/JPG, WEBP, BMP, GIF, TIFF,
  AVIF (se o Pillow suportar), além de **Todos os arquivos**. Ao mostrar
  apenas pastas, navegue até a pasta onde as imagens realmente estão,
  escolha o filtro **Todos os arquivos** quando necessário, ou selecione
  um caminho de imagem pelo campo `Nome do arquivo`. Os formatos podem
  não aparecer quando a pasta atual não contém arquivos correspondentes.

**Testes após atualizar no Ubuntu:**

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
python3 scripts/install_linux.py
~/.local/bin/nexus-core --microphone-test
~/.local/bin/nexus-core --recognition-test
NEXUS_AUDIO_INPUT=alsa ~/.local/bin/nexus-core --recognition-test
~/.local/bin/nexus-core --desktop
```

O último comando com `NEXUS_AUDIO_INPUT=alsa` é um teste **alternativo**.
Se ele receber a voz e o PipeWire não, é possível iniciar também o desktop
com `NEXUS_AUDIO_INPUT=alsa ~/.local/bin/nexus-core --desktop`, sem alterar
a configuração permanente do computador. Se ambos reportarem silêncio,
revise em **Configurações do Ubuntu → Som → Entrada**, o dispositivo
padrão, permissões e mudo físico. A câmera também depende do estado real
do obturador/tecla de privacidade e dos drivers do notebook.

**Permissões dos diretórios:** o aplicativo possui ferramentas mediadas
`list_directory` e `read_file`, mas as regras `PathSecurity` limitam
acessos à pasta pessoal e bloqueiam áreas sensíveis e links simbólicos.
Escolher arquivos pela janela **Imagem** não significa dar permissão de
escrita ou liberdade irrestrita sobre todas as pastas. O seletor gráfico
pode navegar até outros diretórios, mas a análise recusa imagens fora da
área autorizada ou inválidas. A leitura, alteração e execução de ações
continuam sujeitas aos contratos e ao `SecurityGate` aplicável.

Esses testes automatizados usam dispositivos simulados no CI/Xvfb. Nenhum
resultado virtual garante que o microfone, a câmera ou o portal do Wayland
estejam homologados **no hardware físico do usuário**.

### Ícone do microfone animado por atividade de voz

A janela do NEXUS CORE inclui um **ícone de microfone da identidade vinho
(`#722F37`)**, preparado a partir da arte original em quatro estados e
exibido no rodapé, ao lado dos estados **Escuta / Voz / Visão**. A arte PNG
é transparente e acompanha a instalação pelo pacote Python:

<p align="center">
  <img src="nexus/assets/ui/microphone_speaking.png"
       alt="Microfone NEXUS CORE: repouso e três intensidades de atividade de áudio"
       width="320">
</p>

O indicador é **dinâmico pelo áudio realmente recebido**, e não uma
simulação sempre ativa. Os eventos `input_level` do reconhecedor Vosk,
enviados do worker de captura à fila da interface Tk, são convertidos
na própria thread gráfica para os seguintes quadros:

| Pico de entrada PCM | Quadro visual |
| --- | --- |
| 0–3% ou escuta inativa | Repouso, sem ondas |
| 4–19% | Ondas leves |
| 20–49% | Ondas médias |
| 50–100% | Ondas fortes/pulso máximo |

O ícone retorna ao repouso em silêncio, pausa, encerramento, resposta
do assistente ou quando deixa de receber eventos de nível por 1,4 s.
A animação não abre microfone, não armazena som, não altera configurações
de captura e **não indica transcrição bem-sucedida**: o som ambiente
também pode movimentar as ondas. A fala continua sendo transcrita apenas
pelo Vosk. O arquivo é
`nexus/assets/ui/microphone_speaking.png` (sprite PNG de 320 × 80 px);
o módulo `nexus/desktop/microphone_indicator.py` recorta os quatro
quadros nativamente com Tkinter, sem depender do Pillow. A janela mostra
um símbolo estático de reserva se a imagem estiver ausente ou corrompida.

A versão de código permanece **v0.9.11**, sem nova tag/release estável.
A animação tem testes unitários e de GUI na CI Linux/Xvfb, mas a intensidade
real no microfone físico do Ubuntu ainda requer homologação.

### Compatibilidade de imagens, câmera V4L2 e reconhecimento no Ubuntu

Correções adicionais da linha de código **v0.9.11**, sem criar release estável:

- **Imagem:** o diálogo mostra PNG, JPG/JPEG/JPE/JFIF, WEBP, BMP, GIF,
  TIF/TIFF e AVIF, incluindo nomes com extensão maiúscula. Também existe
  “Todos os arquivos” para localizar arquivos com extensão atípica, mas o
  programa **valida o conteúdo real** e rejeita dados que não sejam imagens
  raster suportadas. AVIF depende de suporte de decodificação da versão
  instalada do Pillow. GIF/TIFF usam somente o primeiro quadro/página.
  Todas as imagens aceitas são limitadas a 6 MiB, 4096 px e 8 megapixels,
  e convertidas para PNG sem metadados antes do modelo local.
- **Microfone:** o PipeWire fornece PCM mono S16LE **sem cabeçalho** por meio
  de `pw-record --raw`. Em versões recentes, a saída `-` sem `--raw`
  pode carregar contêiner AU que o Vosk interpretava erroneamente como áudio.
  O teste de microfone mede sinal, mas só `--recognition-test` confirma
  transcrição. Nenhuma gravação é persistida.
- **Câmera:** a descoberta verifica `VIDIOC_QUERYCAP` em cada nó V4L2,
  evitando oferecer como câmera os nós auxiliares apenas de metadados
  (`/dev/video1` em algumas webcams integradas). Continua exigindo
  autorização **por captura**, sem vídeo contínuo. Falhas na captura mostram
  orientação sobre permissão, dispositivo ocupado ou formato V4L2.
- **Tela:** permanece sujeita ao diálogo de seleção e às permissões do portal
  do desktop no Wayland. A seleção não acessa silenciosamente abas de navegador.

Após atualizar `main` e reinstalar, valide no notebook:

```bash
~/.local/bin/nexus-core --microphone-test
~/.local/bin/nexus-core --recognition-test
~/.local/bin/nexus-core --vision-check
~/.local/bin/nexus-core --desktop
```

Caso não haja transcrição, confira a entrada padrão no PipeWire e faça outro
teste após uma pausa na fala. Se a câmera falhar, feche outros programas que
possam utilizá-la e confira as permissões de `/dev/video*`. Os testes
automatizados simulam dispositivos; **a homologação física Ubuntu/Wayland
continua necessária** antes de uma tag ou release estável.

No desktop Ubuntu, perguntas comuns agora usam uma resposta curta de texto
direta do `qwen3:1.7b`, sem exigir JSON de planejamento. Perguntas sobre
capacidade, como “Vai poder arrumar meus arquivos?”, permanecem no modo de
conversa; pedidos explícitos de ação ainda usam contratos, `SecurityGate` e
confirmação. O limite de tokens impede que uma resposta simples se prolongue
indefinidamente. O primeiro uso do Ollama ou um computador com poucos recursos
ainda pode demorar; o estado da janela indica quando o modelo está processando.

Na escuta, a fala curta é enviada ao Vosk quando há uma pausa de cerca de
1,2 segundo, mesmo se o detector de fim de frase do modelo não disparar. Um
medidor de sinal do microfone **não comprova transcrição**. Teste as duas
etapas separadamente:

```bash
~/.local/bin/nexus-core --microphone-test | python3 -m json.tool
~/.local/bin/nexus-core --recognition-test | python3 -m json.tool
~/.local/bin/nexus-core --desktop
```

O segundo comando abre o microfone por até dez segundos, solicita uma frase
em português e retorna a transcrição (ou `no_transcript`). A gravação não é
salva. Se houver sinal mas nenhuma transcrição, confira a entrada padrão do
PipeWire nas configurações de som, aguarde o Vosk carregar, fale com uma pausa
ao final e teste o modelo com uma frase clara. A janela informa quando detecta
sinal repetidamente sem reconhecer palavras. Este fluxo foi testado com áudio
simulado; a transcrição e a latência reais ainda precisam ser verificadas no
seu notebook.

**Câmera e Tela:** os botões **Foto da câmera** e **Câmera ao vivo** procuram dispositivos `/dev/video*` sem
abrir a câmera durante a busca. Se houver apenas um, pede autorização para
vídeo contínuo local; com vários dispositivos, mostra seus nomes para escolha.
Se não houver câmera, informa isso em texto e na voz escolhida. Perguntas
explícitas durante a prévia enviam um quadro recente ao modelo visual local,
como `gemma3:4b` instalado separadamente. O vídeo não é gravado e a resposta
é lida em voz alta quando essa opção está ativada. Erros de captura ou do
modelo também são informados em texto e voz.

No **Wayland**, o botão **Tela** e os comandos “analisar a tela” ou “analisar
a janela” abrem o seletor do portal do desktop para escolher **uma janela**.
“Analisar a tela inteira” pede a escolha de um monitor. O portal precisa
oferecer esse alvo; se não oferecer, o aplicativo informa a limitação e não
captura a tela inteira por engano. O seletor mostra as janelas permitidas pelo
ambiente, mas não lista abas internas do navegador nem lê nomes de páginas em
segundo plano. No X11, o botão Tela continua capturando uma foto da tela após
autorização. Para o Wayland, a instalação `.[vision]` inclui `dbus-next` e o
desktop precisa disponibilizar `xdg-desktop-portal` com backend de captura.
Essas rotas ainda precisam de teste físico no seu Ubuntu 26.04/Wayland.

Perguntas como **“O que é uma IA?”** geram respostas de texto pelo Ollama;
o planejador não recebe contratos de ferramentas nesse turno e rejeita
propostas de `system_info`. Pedidos explícitos para consultar o computador
continuam a passar pelo `SecurityGate`. A janela mostra o nível de sinal do
microfone e usa o dispositivo padrão do PipeWire quando há uma sessão ativa;
o ALSA permanece disponível. Para forçar ALSA, execute
`NEXUS_AUDIO_INPUT=alsa ~/.local/bin/nexus-core --desktop`.

O instalador oferece a voz neural **masculina** em português brasileiro do
[Piper](https://github.com/OHF-Voice/piper1-gpl) com o modelo aberto
[`pt_BR-faber-medium`](https://huggingface.co/rhasspy/piper-voices/tree/v1.0.0/pt/pt_BR/faber/medium).
Ela fica como seleção inicial quando instalada. A opção **Feminina** usa
[RHVoice Letícia](https://packages.ubuntu.com/resolute/rhvoice-brazilian-portuguese)
dos pacotes Ubuntu, com eSpeak NG como alternativa. Não há modelo feminino
neural com licença aberta integrado nesta versão. O áudio é gerado e reproduzido apenas no
computador. A instalação do Piper é opcional e um erro nela não impede o
chat de texto. A CI simula áudio: teste o microfone e as duas vozes no Ubuntu
físico antes de considerar esta correção homologada.
Na síntese, espaços extras são reduzidos e frases curtas recebem pontuação
quando ausente. A voz Piper usa uma cadência ligeiramente mais lenta. São
ajustes de prosódia e legibilidade; o timbre e o nível de naturalidade
continuam limitados pelos modelos locais. A fala física precisa ser ouvida
no computador para avaliar o resultado.

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
python3 scripts/install_linux.py
~/.local/bin/nexus-core --microphone-test | python3 -m json.tool
~/.local/bin/nexus-core --voice-check | python3 -m json.tool
~/.local/bin/nexus-core --desktop
```

O teste de microfone **grava três segundos após este comando explícito**,
informa a entrada usada e o pico do sinal e descarta o áudio. Se informar
`no_signal`, selecione o microfone correto nas configurações de som do Ubuntu,
desative o mudo e execute o teste novamente. `--voice-check` apenas verifica
dependências; não abre microfone ou alto-falante. Um pico detectado ainda não
certifica transcrição correta pelo modelo Vosk.

## Compatibilidade do instalador Ubuntu

O bloqueio exclusivo da versão 24.04 foi removido do código após a v0.9.11.
Em um Ubuntu identificado por `/etc/os-release` (`ID=ubuntu` e `VERSION_ID`
numérico como `24.04` ou `26.04`), o instalador aceita **Python 3.12 ou
superior** e verifica as dependências disponíveis no próprio computador.
Pacotes ausentes são apresentados antes de pedir autorização para `apt-get`;
se uma dependência continuar ausente, a instalação para. O banco é somente
PostgreSQL: a ativação exige login local autenticado e `SELECT 1` no ambiente
Python instalado. Outras distribuições continuam apenas no diagnóstico.

No Ubuntu 26.04 com Wayland, a janela Tk pode ser testada normalmente.
`xdotool` é opcional e a automação de janelas de terceiros requer sessão X11
local; sua ausência no Wayland não impede a instalação. `--check` é passivo
e não certifica áudio, câmera, inferência Ollama ou funcionamento físico.
Compatibilidade de instalação não significa homologação de todas as versões
Ubuntu: a CI automatizada ainda usa Ubuntu 24.04/Python 3.12, e o aceite
físico no Ubuntu 26.04/Python 3.14/Wayland permanece pendente.

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
python3 scripts/install_linux.py --check
python3 scripts/install_linux.py  # usuário comum; sudo apenas após confirmação
~/.local/bin/nexus-core --version
~/.local/bin/nexus-core --ubuntu-preflight
~/.local/bin/nexus-core --desktop
```

Se já houver um usuário ou banco `nexus`, o instalador preserva esses dados
e oferece criar um usuário e banco separados, `nexus_core`, após confirmação.
Se `nexus_core` também existir, ele interrompe sem alterar nenhum dos dois:
configure credenciais manualmente após verificar a finalidade do banco.
A senha gerada, o nome do banco e o usuário ficam em
`~/.config/nexus-core/credentials.json` com permissão `0600`, carregados pelo
launcher gerenciado. Se você informar uma senha pelo ambiente, ela só é salva
nesse arquivo **depois** de o login PostgreSQL ser comprovado, preservando
qualquer arquivo de credenciais anterior. O Ollama e o modelo Vosk em português
têm preparação e testes próprios descritos abaixo.

**Instalação guiada atual:** além dos pacotes Ubuntu, ambiente Python e PostgreSQL,
`python3 scripts/install_linux.py` confere o Ollama e os modelos locais antes de
ativar o aplicativo. Caso o binário Ollama não exista, pode baixar o pacote Linux
oficial para uma pasta privada do usuário e iniciar um serviço `systemd --user`,
sem executar um script remoto com privilégios de administrador. Em seguida,
oferece baixar `qwen3:1.7b` pelo próprio Ollama e o modelo Vosk de português
da fonte oficial, apenas se estiverem ausentes. Cada download exige confirmação,
e o instalador interrompe se o serviço ou os modelos necessários falharem. No
computador que já tem Ollama e Vosk, ele preserva ambos. `--check` continua
passivo; a instalação não abre microfone, câmera nem comprova a inferência real.
Docker continua opcional para o sandbox de comandos e automação de janelas
de terceiros com `xdotool` exige sessão X11.

### Janela sem campo de mensagem ou resposta no Ubuntu

Depois de atualizar o código e executar novamente `python3 scripts/install_linux.py`,
abra `~/.local/bin/nexus-core --desktop`: o campo **Sua mensagem** e o botão
**Enviar** ficam visíveis abaixo da transcrição. Teste primeiro a resposta sem
microfone com `~/.local/bin/nexus-core --agent-prompt 'Responda em uma frase: você está funcionando?'`.
O Agent responde perguntas comuns diretamente; pedidos de ação usam o esquema
de propostas JSON e passam pelas permissões antes de qualquer execução. A marca da
janela está embutida no pacote instalado, ampliada sobre cabeçalho escuro para
dar contraste à palavra clara “Nexus”. `--status` indica componentes
inicializados, não comprova que houve uma inferência ou que o microfone funciona.
Se o prompt ainda falhar, verifique `ollama list` e o serviço Ollama no próprio
computador; nenhuma resposta de modelo inválida autoriza a execução de ferramentas.
Se `--voice-check` mostrar `vosk_local_model: false`, execute novamente o
instalador guiado para baixar o modelo; a conversa digitada continua disponível.

---

# v0.9.12 — Authorized Desktop Actions (código integrado; aceite físico pendente)

Pedidos exatos para uma pasta filha da home são resolvidos localmente e
continuam sujeitos a autorização por operação. O navegador, o gerenciador de
arquivos e o terminal permanecem ações delimitadas que funcionam em sessões
gráficas Wayland e X11. A automação de teclado em janelas de terceiros exige
X11; nenhuma sessão Wayland foi homologada para essa finalidade.

Leia as [notas da v0.9.12](docs/RELEASE_NOTES_v0.9.12.md) e o
[roteiro de aceite físico](docs/UBUNTU_PHYSICAL_ACCEPTANCE_v0.9.12.md).
O código pode evoluir na `main`, mas a tag e a release dependem do aceite
físico e da CI no commit final. O workflow permanece bloqueado.

---

# v0.9.11 — First-Run PostgreSQL Authentication (código integrado; release pendente)

No instalador guiado para Ubuntu Desktop 24.04 LTS, a existência de uma senha
no ambiente ou no arquivo privado de credenciais deixou de ser suficiente para
ativar a versão. Após instalar e verificar o pacote no ambiente Python do
usuário, o instalador executa `--ubuntu-preflight` com esse ambiente e exige
um login PostgreSQL local autenticado seguido de `SELECT 1` somente leitura.
Se o login falhar, não troca o link da versão ativa, não cria os launchers nem
relata instalação concluída. A senha é passada apenas no ambiente do processo
filho; não aparece em argumentos, mensagens ou logs do diagnóstico.

O mesmo pré-diagnóstico verifica se o modelo Ollama configurado está listado e
se as dependências locais de entrada/saída de voz estão visíveis, **sem
baixar modelos nem abrir hardware**. Esses dois resultados orientam a
configuração separada do Ollama e de um modelo Vosk em português; uma falha
nesses componentes não é confundida com falha de autenticação no banco. O
comando `nexus-core --ubuntu-preflight` continua disponível após a instalação
para conferir os estados. A presença do binário Ollama ou do diretório Vosk
não comprova inferência, reconhecimento, reprodução de áudio ou operação do
microfone e câmera no computador físico.

Leia as [notas da v0.9.11](docs/RELEASE_NOTES_v0.9.11.md). A publicação
estável permanece condicionada ao aceite físico e à revisão do workflow.

---

# v0.9.10 — Spoken Voice Selection (código integrado; release pendente)

Na janela desktop, diga **"Use voz feminina"**, **"Use voz masculina"**,
**"Mude para voz feminina/masculina"** ou **"Selecione voz
feminina/masculina"** para alterar o mesmo seletor já disponível na
interface. O comando é tratado localmente, sem chamar o Agent/Ollama,
acessar o PostgreSQL, capturar imagens ou executar ferramentas. A confirmação
aparece no histórico e usa a voz recém-selecionada quando a opção **Ler
respostas em voz alta** estiver ligada. Se estiver desligada, a escolha é
feita sem reativar a fala: a confirmação fica apenas em texto.

As frases precisam ser pedidos completos. A palavra de ativação **"Nexus"**
continua obrigatória quando essa opção está marcada. Com a escuta pausada,
nenhum comando falado é recebido; retome pelo botão ou `Ctrl+Shift+M`.
A escolha vale para a sessão atual e não altera o estado do microfone ou
autorizações. Testes em display virtual cobrem as duas vozes, frase de
ativação, saída silenciada e isolamento do modelo. Áudio e microfone físicos
no Ubuntu 24.04 LTS seguem pendentes de homologação.

Leia as [notas da v0.9.10](docs/RELEASE_NOTES_v0.9.10.md).
Este marco foi integrado após o código v0.9.9 na `main`. O
workflow de release permanece bloqueado até aceite físico registrado.

---

# v0.9.9 — Spoken Desktop Controls (código integrado; release pendente)

Além dos atalhos da janela, o assistente aceita comandos falados locais
para **"analisar imagem"**, **"analisar tela"** e **"analisar câmera"**.
Cada um abre o mesmo fluxo dos botões: seleção quando aplicável,
pergunta e autorização individual antes da leitura/captura. Se a escolha
ou autorização for recusada, não há captura e a escuta volta a aguardar
o usuário. A resposta visual autorizada continua podendo ser falada na
voz feminina ou masculina selecionada.

**"Desative a voz"** e **"Ative a voz"** controlam a opção **Ler
respostas em voz alta**. Desativar confirma por texto; ativar também
confirma pela voz local. Os comandos são reconhecidos por frases completas,
sem chamar o agente ou executar ferramentas, e respeitam a opção de
exigir **"Nexus"** no início da fala. A escuta pausada pelo usuário não
aceita comandos falados até ser retomada pelo botão ou `Ctrl+Shift+M`.
Durante a reprodução de uma resposta, o reconhecimento está suspenso
para evitar eco; use `Ctrl+Shift+S` para interromper a fala atual ou
`Ctrl+Shift+V` para desativar a saída falada. Operações em andamento
continuam sob o botão **Cancelar** ou `Ctrl+Shift+X`.

Testes Tk sob display virtual cobrem autorização, recusa, seleção
cancelada, resposta falada e frase de ativação. Hardware Ubuntu físico
segue pendente. Leia as [notas da v0.9.9](docs/RELEASE_NOTES_v0.9.9.md).
Uma correção nesta versão impede que a recusa ou falha da configuração
PostgreSQL seja apresentada como instalação concluída.
As versões v0.8.3–v0.9.9 foram integradas à `main` pelos PRs #15–#31.
O workflow de release segue bloqueado até homologação física registrada
e revisão específica da publicação.

---

# v0.9.8 — Accessible Speech Output Toggle (código integrado; release pendente)

Na janela desktop, **Ctrl+Shift+V** alterna a opção **Ler respostas em voz
alta**. Quando desativada durante uma fala, interrompe a reprodução local
em curso; respostas seguintes permanecem em texto até a opção ser
reativada. Reativar não reproduz automaticamente a última mensagem.
O atalho usa a mesma política do controle visual e atualiza o indicador
de privacidade **Voz**.

O comando não pausa nem reativa o microfone, não inicia análise visual,
Ollama ou execução de ferramentas. A escuta pausada pelo usuário continua
pausada. Testes Tk sob display virtual cobrem alternância por evento de
teclado, fala em andamento, evento de áudio atrasado e resposta visual
pendente. Áudio físico e teclado real ainda requerem homologação no Ubuntu
Desktop 24.04 LTS. Leia as [notas da v0.9.8](docs/RELEASE_NOTES_v0.9.8.md).

**Estado atual:** o código v0.9.8 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.7 — Keyboard-Gated Vision Requests (código integrado; release pendente)

Na janela desktop, **Ctrl+Shift+F** abre a escolha de um arquivo de imagem,
**Ctrl+Shift+T** solicita análise da tela atual e **Ctrl+Shift+K** seleciona
uma câmera. Cada atalho percorre a mesma escolha de pergunta e o mesmo
diálogo de autorização individual dos botões **Imagem**, **Tela** e
**Câmera**. A captura ou leitura só ocorre depois de confirmar aquela
análise; cancelar a escolha ou recusar a autorização não inicia captura.

Os atalhos não iniciam monitoramento contínuo e não substituem o controle
de escuta. Durante uma operação, outra solicitação visual é ignorada.
Testes Tk sob display virtual verificam as três fontes, as recusas,
o cancelamento e o bloqueio durante operação. Ainda é necessária a
homologação física de tela e câmera no Ubuntu Desktop 24.04 LTS.
Leia as [notas da v0.9.7](docs/RELEASE_NOTES_v0.9.7.md).

**Estado atual:** o código v0.9.7 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.6 — TTS Startup Cancellation Safety (código integrado; release pendente)

A interrupção de voz da v0.9.5 também deve valer se **Ctrl+Shift+S**
chegar enquanto o eSpeak NG está iniciando. Antes, a janela podia marcar
a fala como interrompida enquanto o processo ainda não estava registrado
para receber a parada. Agora o sintetizador local recebe uma verificação
da requisição atual antes de iniciar e outra logo após registrar o
processo. Se ela foi substituída ou interrompida nesse intervalo, o
processo é encerrado sem receber o texto antigo.

O comportamento normal da voz feminina/masculina, o atalho e os controles
permanecem. Os sintetizadores injetados para teste mantêm a interface de
dois argumentos. O teste reproduz precisamente a parada durante a criação
do processo; a verificação com alto-falante e hardware Ubuntu continua
pendente. Leia as [notas da v0.9.6](docs/RELEASE_NOTES_v0.9.6.md).

**Estado atual:** o código v0.9.6 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.5 — Spoken Reply Interruption (código integrado; release pendente)

Durante uma resposta falada, **Ctrl+Shift+S** interrompe somente a
reprodução atual. O texto da resposta continua no histórico e a opção
**Ler respostas em voz alta** permanece ligada para as respostas futuras.
Quando a escuta estiver habilitada, o assistente volta a aguardá-la;
uma escuta pausada pelo usuário **continua pausada**. Sem fala em curso,
o atalho não altera a mensagem digitada nem a configuração de voz.

O comando utiliza a interrupção local do eSpeak NG e ignora eventos
atrasados da fala interrompida. Não cancela a solicitação ou ação já
executada, não acessa o modelo, a câmera ou o banco de dados e não
inicia autorizações. Para cancelar uma operação em andamento, use o
botão **Cancelar** ou **Ctrl+Shift+X**. Testes Tk sob display virtual
cobrem a reprodução, a escuta pausada e a próxima resposta; ainda é
necessário o teste físico de áudio no Ubuntu. Leia as
[notas da v0.9.5](docs/RELEASE_NOTES_v0.9.5.md).

**Estado atual:** o código v0.9.5 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.4 — Accessible Cancellation Shortcut (código integrado; release pendente)

O atalho **Ctrl+Shift+X** aciona o mesmo **Cancelar** da janela durante
uma pergunta em processamento ou análise visual já autorizada. Quando
não há operação, não altera a conversa nem a entrada digitada. Em uma
conversa, solicita cancelamento do turno e nega autorizações pendentes;
na análise visual, marca o cancelamento solicitado e omite o resultado
quando a operação terminar. Repetir o atalho durante o mesmo cancelamento
não repete a solicitação.

O cancelamento é **cooperativo**: uma ação já executada não é desfeita,
e uma captura ou chamada Ollama em andamento pode continuar até retornar.
O atalho não inicia escuta, captura, chamada ao modelo ou autorização
nova. A interface e os controles existentes permanecem disponíveis.
Testes Tk sob display virtual cobrem estado ocioso, conversa pendente e
análise visual autorizada. Não substituem homologação física Ubuntu.
Leia as [notas da v0.9.4](docs/RELEASE_NOTES_v0.9.4.md).

**Estado atual:** o código v0.9.4 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.3 — Typed Privacy Status (código integrado; release pendente)

Digite **“Qual é o estado da privacidade?”** na caixa de conversa e envie
para receber no histórico o estado atual de **Escuta, Voz e Visão**. As
outras frases explícitas da v0.9.2 também funcionam. A consulta é útil
com a escuta pausada: **não retoma o microfone**. Com a leitura de respostas
habilitada, o assistente fala a resposta na voz selecionada; se ela estiver
desativada, a resposta permanece só no texto. Antes de responder, a janela
interrompe a escuta ou fala anterior em curso para evitar sobreposição.

A resposta usa apenas o estado local do aplicativo e informa que não
verifica o hardware. Não chama Agent/Ollama, banco de dados nem câmera
ou tela, não concede permissões e não cria um turno na memória da conversa.
Uma pergunta diferente continua no fluxo normal do assistente. Durante
outra operação, o envio permanece indisponível e o texto digitado é
preservado; o atalho **Ctrl+Shift+I** segue disponível para consulta.

Testes Tk sob display virtual cobrem escuta pausada, voz ligada e
desligada, isolamento do modelo e a conversa normal. Não constituem
homologação física em Ubuntu Desktop. Leia as
[notas da v0.9.3](docs/RELEASE_NOTES_v0.9.3.md).

**Estado atual:** o código v0.9.3 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.2 — Spoken Privacy Status (código integrado; release pendente)

Durante a conversa contínua, pergunte **“Qual é o estado da privacidade?”**,
**“Como está minha privacidade?”** ou **“Informe o estado da privacidade.”**
O assistente responde no histórico e, quando a leitura de respostas está
habilitada, na voz feminina ou masculina selecionada. Se a opção de exigir
“Nexus” estiver ativa, diga “Nexus, qual o estado da privacidade?”.
A resposta mostra o estado atual de **Escuta, Voz e Visão** do aplicativo,
com o aviso de que não verifica o hardware. Ela não chama Agent/Ollama,
PostgreSQL, câmera ou tela, não altera permissões e não retoma a escuta
pausada. Os comandos são frases explícitas; perguntas diferentes seguem
o fluxo normal de conversa. Os atalhos e o layout da v0.9.1 permanecem.

Testes de fluxo de áudio sob display virtual verificam a resposta local,
voz selecionada, saída desativada e a palavra de ativação. Isso não é
homologação física de microfone, alto-falantes nem leitor de tela.
Leia as [notas da v0.9.2](docs/RELEASE_NOTES_v0.9.2.md).

**Estado atual:** o código v0.9.2 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.1 — On-Demand Privacy Status (código integrado; release pendente)

O atalho **Ctrl+Shift+I** mostra, em um diálogo nativo da janela Tk,
os estados atuais de **Escuta, Voz e Visão**. A consulta é explícita,
funciona inclusive durante uma análise já autorizada e usa a mesma
representação local da v0.9.0, sem depender da atualização periódica dos
rótulos. Assim a pausa de escuta aparece imediatamente como `pausada` e
uma análise cancelada em curso aparece como `cancelamento solicitado`.

O diálogo não chama o Agent/Ollama, não grava áudio, não captura imagem,
não acessa PostgreSQL nem mostra nomes de arquivos, pergunta ou conteúdo
visual. Não concede novas permissões. Os estados descrevem solicitações
do software; **não certificam o funcionamento físico** do microfone,
alto-falantes ou câmera. A janela principal, marca e fluxo de
autorização por análise continuam com o mesmo design e comportamento.
O atalho fica indisponível após o início do encerramento.

Os testes Tk sob Xvfb cobrem a consulta inicial, a mudança imediata
após pausar a escuta/desativar a voz, a visão autorizada e o cancelamento,
sem deixar uma chamada ao modelo ou captura não autorizada. Isso não
substitui homologação de leitor de tela nem testes em Ubuntu Desktop real.
Leia as [notas da v0.9.1](docs/RELEASE_NOTES_v0.9.1.md).

**Estado atual:** o código v0.9.1 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.9.0 — Multimodal Privacy & Accessibility Status (código integrado; release pendente)

Iniciando a linha `v0.9.x — Multimodal Interface` prevista no roadmap, esta versão aprimora a **transparência do estado de privacidade** do assistente desktop, preservando a interface Tk e a identidade Nexus Line. A janela mantém os mesmos controles e apresenta um painel textual discreto com três indicadores: **Escuta**, **Voz** e **Visão**.

* **Escuta** diferencia `pausada`, `aguardando` e `solicitada`: essa última é uma **requisição de reconhecimento**, não uma certificação de que o microfone efetivamente gravou.
* **Voz** diferencia `desativada`, `habilitada` e `saída solicitada`, sem afirmar que a reprodução de áudio realmente ocorreu.
* **Visão** permanece `sem captura` até o usuário **autorizar uma análise específica** de imagem, tela ou câmera. Somente após essa autorização mostra `processando imagem/tela/câmera`. No cancelamento, mostra `cancelamento solicitado`, pois processos já iniciados podem continuar até finalizar; não afirma interrupção instantânea.

O novo atalho `Ctrl+Shift+M` realiza exatamente a mesma ação do botão `Pausar escuta / Retomar escuta`. **Não concede acesso à tela, câmera ou outras ferramentas**. O novo `nexus/desktop/multimodal_status.py` é uma máquina de apresentação imutável e local, sem dependências de captura, rede ou persistência. O layout aprovado e os ícones existentes são preservados.

Os testes verificam os estados em unidade e na janela Tk sob Xvfb, inclusive recusa de consentimento sem acesso à tela, cancelamento visual e pausa por teclado. São **testes simulados de interface**, não homologação física de microfone, câmera, leitores de tela ou Ollama em produção. Leia [notas da v0.9.0](docs/RELEASE_NOTES_v0.9.0.md).

**Estado atual:** o código v0.9.0 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.8.9 — Ubuntu Activation Journal & Offline Repair (código integrado; release pendente)

Esta versão fecha uma lacuna conhecida de atualizações no **Ubuntu Desktop 24.04 LTS**: a troca dos apontadores `previous` e `current` envolve duas operações de sistema de arquivos, que podem ser interrompidas entre si. A nova `.activation-intent.json`, gravada de forma privada antes de modificar os apontadores, registra a versão antiga, a candidata e a versão anterior ao início da operação. Uma ativação concluída remove o registro; uma interrupção deixa evidência para análise.

Quando há registro pendente, o inicializador e o atualizador gerenciado **recusam continuar**. A ferramenta offline independente do Python do assistente, `nexus-core-recover`, ganha dois comandos:

```bash
# Diagnóstico do estado, sem rede nem qualquer alteração:
~/.local/bin/nexus-core-recover --activation-status

# Reparo da ativação interrompida, autorizado no terminal:
~/.local/bin/nexus-core-recover --repair-activation
# Digite REPARAR somente se concordar com a reconciliação dos links.
```

O reparo valida os arquivos e as versões sob o lock da v0.8.6, desliga atualização automática e concilia `previous` com `current`, **sem executar nem substituir a versão atual por conta própria**. Se `current` continuar na versão antiga, recupera a referência anterior; se já estiver na nova versão, confirma a referência `previous` correta. O procedimento não altera banco PostgreSQL, credenciais, modelos, arquivos do usuário ou serviços.

**Limites:** o registro detecta e auxilia o reparo, mas **não torna duas trocas de symlink atomicamente transacionais**. O auxiliar externo da v0.8.8 instalado anteriormente precisa ser atualizado explicitamente para incluir a nova trava de execução, já que um wheel novo não altera automaticamente scripts fora do ambiente Python. Nada substitui testes no Ubuntu físico. Leia [notas v0.8.9](docs/RELEASE_NOTES_v0.8.9.md).

**Estado atual:** o código v0.8.9 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.8.8 — Managed Launcher Integrity (código integrado; release pendente)

Esta versão prioriza o início real da instalação gerenciada no Ubuntu Desktop 24.04 LTS: o comando `~/.local/bin/nexus-core` passa a ser uma cópia autônoma do inicializador `nexus/updates/managed_entrypoint.py`, usando somente a biblioteca padrão do Python e os caminhos da instalação salvos quando o usuário a realizou.

Antes de executar o Python do NEXUS CORE, o inicializador verifica que `managed` e `versions` são pastas privadas do usuário, que o link `current` aponta para uma versão diretamente dentro de `versions` e que `bin/python` é um arquivo regular pertencente ao usuário e com permissão de execução, recusando links simbólicos externos e binários manipulados. Somente então inicia o ambiente com `python -I -m nexus.updates.launcher`.

O `NEXUS_MANAGED_HOME` passa a ser fixado pelo inicializador e utilizado internamente. Assim, mudanças posteriores na variável `XDG_DATA_HOME` da sessão não fazem o atualizador procurar ou modificar outra instalação. O instalador e o atualizador também protegem os diretórios das novas versões com permissão `0700`, garantindo consistência com a verificação.

As credenciais PostgreSQL opcionais são lidas somente de um JSON privado do próprio usuário, com tamanho limitado, sem expor a senha e sem substituir credenciais já definidas. O mecanismo não instala serviços, não altera banco ou modelos e preserva a interface Tk e as autorizações do assistente.

**Limites:** isso não é uma assinatura criptográfica do ambiente nem substitui homologação física de Ubuntu, X11, voz, câmera, Ollama e atualizações/rollback. A ferramenta offline independente `nexus-core-recover` continua responsável por versões quebradas. A nova implementação está descrita nas [notas v0.8.8](docs/RELEASE_NOTES_v0.8.8.md).

**Estado atual:** o código v0.8.8 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.8.7 — Ubuntu Pre-Activation Validation (código integrado; release pendente)

Na versão anterior, a manutenção de instalação, atualização e recuperação passou a usar `flock` exclusivo. Nesta versão, o NEXUS CORE evolui a **validação anterior à troca de versão**, para evitar selecionar um ambiente Python novo que não possua as dependências necessárias ou que não execute corretamente os próprios diagnósticos passivos.

O instalador gerenciado do Ubuntu 24.04 LTS e o atualizador automático opt-in passam a verificar, **no ambiente candidato e antes de alterar o ponteiro `current`**:

```bash
python -I -m pip check
python -I -m nexus.main --version
python -I -m nexus.main --platform-check
```

O `-I` impede que código localizado no diretório corrente ou em `PYTHONPATH` seja confundido com o pacote instalado. A validação exige a versão exata, JSON do diagnóstico passivo, Python suportado, Ubuntu 24.04 LTS e ausência de dependências de sistema consideradas obrigatórias. Falha em qualquer etapa mantém a versão anteriormente selecionada e rejeita a candidata; o procedimento não abre a interface Tk, não executa inferência, não conecta a bancos nem testa câmera ou microfone.

**Limite operacional:** passar nesses três checks **não** demonstra funcionamento completo da instalação, áudio, imagem, Ollama, PostgreSQL autenticado ou integridade de todos os pacotes. Os testes reais em Ubuntu físico continuam necessários. [Notas v0.8.7](docs/RELEASE_NOTES_v0.8.7.md).

**Estado atual:** o código v0.8.7 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.8.6 — Ubuntu Maintenance Coordination (código integrado; release pendente)

Este incremento resolve um risco concreto do NEXUS CORE gerenciado: a **possibilidade de instalação, atualização automática e recuperação offline ocorrerem ao mesmo tempo**. Todas essas operações passam a usar um **bloqueio de manutenção Linux** compartilhado, `fcntl.flock`, no arquivo privado `.maintenance.lock`. Uma segunda operação encontra o ambiente ocupado e recusa alterar `current`, `previous` ou iniciar instalação de dependências. O lock é liberado pelo kernel quando o processo termina, mesmo após falha.

Além disso, o launcher não deve consultar releases nem modificar a instalação quando o usuário solicita apenas um diagnóstico: `--version`, `--platform-check`, `--ubuntu-doctor`, `--ubuntu-preflight`, `--desktop-check`, `--voice-check`, `--vision-check` e diagnósticos declarativos de dispositivos permanecem sem atualizações por efeito colateral. A inicialização normal continua podendo buscar atualizações **somente quando habilitadas**.

A atualização revalida a autorização depois de adquirir o lock (inclusive caso o operador tenha acabado de reverter/desabilitar atualizações). O instalador Ubuntu e o utilitário independente `nexus-core-recover` compartilham a mesma exclusividade. Uma falha ao limpar o marcador após ativação **não pode eliminar o ambiente que acabou de ser selecionado**.

```bash
# Consultas de diagnóstico não atualizam a instalação:
~/.local/bin/nexus-core --version
~/.local/bin/nexus-core --platform-check

# Inspeção e recuperação continuam explícitas e offline:
~/.local/bin/nexus-core-recover --status
~/.local/bin/nexus-core-recover --rollback
```

**Limites:** exclusividade por lock não é garantia de segurança contra usuários que editam arquivos diretamente; a troca de dois symlinks não constitui uma transação atômica conjunta. Nenhum banco PostgreSQL, memória, modelo, voz, câmera ou arquivo do usuário é alterado por esse mecanismo. O aceite físico no Ubuntu Desktop 24.04 LTS continua obrigatório e não é substituído pela CI. Consultar [notas da v0.8.6](docs/RELEASE_NOTES_v0.8.6.md).

**Estado atual:** o código v0.8.6 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.8.5 — Ubuntu Recovery & Documentation Integrity (código integrado; release pendente)

O NEXUS CORE passa a disponibilizar uma **ferramenta de recuperação offline independente do seu próprio ambiente Python**, instalada no Ubuntu como `~/.local/bin/nexus-core-recover`. Quando uma atualização deixa a versão atual inutilizável, o operador pode escolher a **versão anterior já preservada**, após fechar o assistente e confirmar expressamente a reversão.

```bash
~/.local/bin/nexus-core-recover --status    # inspeciona versões sem fazer alterações
~/.local/bin/nexus-core-recover --rollback  # exige terminal + confirmação REVERTER
```

A recuperação não precisa de internet nem de importar o NEXUS CORE possivelmente danificado. Limita-se a selecionar outro ambiente de execução Python dentro do diretório privado do usuário e **desliga atualizações automáticas antes de reverter**. O módulo recusa symlinks fora da instalação, executáveis ausentes, diretórios permissivos e ausência de versão anterior. **Não reverte banco PostgreSQL, migrações, modelos ou dados**; não interrompe uma aplicação já aberta. A recuperação exige uma atualização anterior que tenha preservado `previous`.

A v0.8.5 inclui uma [auditoria da documentação](docs/DOCUMENTATION_AUDIT_v0.8.5.md) cobrindo o README, todas as notas históricas disponíveis, identidade visual, aceitação física X11 e workflows CI/release, com matriz de regras obrigatórias e esclarecimentos de estados antigos dos PRs.

**Diretrizes preservadas:** Ubuntu Desktop **24.04 LTS** é a plataforma de instalação prioritária; futuras distros dependem de homologação; aplicativo nativo Tk e identidade visual inalterados; PostgreSQL e Ollama locais; segurança e consentimento por ação; nenhuma tag/release sem CI exata e aceite físico. Leia as [notas da v0.8.5](docs/RELEASE_NOTES_v0.8.5.md).

**Estado atual:** o código v0.8.5 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.8.4 — Ubuntu Readiness Preflight (código integrado; release pendente)

Esta versão acrescenta ao Ubuntu Desktop 24.04 LTS o comando **`nexus-core --ubuntu-preflight`**, que avalia requisitos básicos para executar a conversa por texto e voz, **sem iniciar conversas, gravar áudio ou alterar dados**. Complementa o `--ubuntu-doctor` da versão anterior.

```bash
nexus-core --platform-check   # diagnóstico passivo sem rede
nexus-core --ubuntu-doctor    # verifica se PostgreSQL/Ollama locais respondem
nexus-core --ubuntu-preflight # SELECT 1 somente leitura, /api/tags local e recursos de voz
```

O preflight autentica no PostgreSQL já configurado usando `SELECT 1` e sessão `default_transaction_read_only=on`, verifica se o nome do modelo `qwen3:1.7b` (ou outro explicitamente configurado) aparece no inventário do Ollama local e inspeciona ferramentas de fala Vosk/ALSA/eSpeak NG. **Não faz download ou execução de modelos, consultas a outras redes, instalações de pacotes, nem testes físicos de microfone, webcam ou alto-falantes.** Saídas JSON não incluem senhas, lista completa de modelos, histórico nem conteúdos pessoais.

`text_chat_dependencies_ready_to_try` e `voice_chat_dependencies_ready_to_try` indicam apenas pré-requisitos. Não certificam inferência, áudio, estabilidade, desempenho ou hardware. A CI permanece em **Ubuntu Desktop 24.04 LTS**; o instalador passou a aceitar outras versões Ubuntu compatíveis, sem alegar homologação física de cada uma. Leia as [notas v0.8.4](docs/RELEASE_NOTES_v0.8.4.md).

**Estado atual:** o código v0.8.4 foi integrado à `main` em ordem. A última release estável segue v0.7.2; a publicação posterior exige homologação física e revisão do workflow bloqueado.

---

# v0.8.3 — Ubuntu First-Run Doctor (código integrado; release pendente)

O marco v0.8.3 oferece o diagnóstico local e limitado `nexus-core --ubuntu-doctor`. Ele consulta **somente** o PostgreSQL no endereço `127.0.0.1:5432` por `pg_isready` e o Ollama no `127.0.0.1:11434/api/version` (resposta limitada, timeout, sem redirects ou downloads). A ferramenta separa indisponibilidade dos serviços de ausência de pacotes e apresenta recomendações sem executar alterações. **Não autentica no banco, não verifica modelos Ollama instalados, não inicia microfone/câmera e não garante funcionalidade completa do assistente.**

```bash
nexus-core --platform-check  # inventário passivo, nenhuma conexão
nexus-core --ubuntu-doctor   # apenas duas consultas ao loopback local
```

Na v0.8.3, o Ubuntu Desktop **24.04 LTS** era o alvo exclusivo de instalação; a restrição foi removida posteriormente, conforme a seção de compatibilidade atual. O uso destas ferramentas de diagnóstico não cria serviços, não utiliza sudo e não acessa sistemas externos. Outras distribuições Linux terão adaptação e testes próprios em versões futuras.

**Estado dos merges:** PRs [#11](https://github.com/ricardogomesbarreto/Nexus-Core/pull/11), [#12](https://github.com/ricardogomesbarreto/Nexus-Core/pull/12), [#13](https://github.com/ricardogomesbarreto/Nexus-Core/pull/13) e [#14](https://github.com/ricardogomesbarreto/Nexus-Core/pull/14) já foram integrados à `main`, em ordem. **Isso não equivale a homologação física ou release estável.** As publicações automáticas dessas versões continuam explicitamente bloqueadas enquanto não houver os aceites de X11 e de instalação Ubuntu real. Consulte as [notas v0.8.3](docs/RELEASE_NOTES_v0.8.3.md).

---

# v0.8.2 — Ubuntu Desktop Baseline & Distribution Portability (integrado ao código, release não homologada)

Na v0.8.2, **Ubuntu Desktop 24.04 LTS era o primeiro alvo** para desenvolvimento, instalação guiada, testes de integração e homologação física. A seção atual de compatibilidade registra a ampliação para outras versões Ubuntu que atendam aos requisitos. Debian, Fedora, Arch Linux e SteamOS seguem sem instalador guiado.

O novo módulo `nexus.platforms` disponibiliza um **perfil passivo de compatibilidade** (ID/versão do sistema, sessão X11/Wayland, Python, dependências e limites de teste), isolado do instalador. É possível consultar qualquer Linux sem executar comandos de instalação, acessar sensores ou inicializar banco/modelo:

```bash
nexus-core --platform-check
# Também disponível diretamente no checkout de código:
python3 scripts/install_linux.py --check
```

Na implementação original da v0.8.2, o instalador só alterava o **Ubuntu 24.04 LTS com Python 3.12+**. A restrição fixa foi removida posteriormente, conforme a seção atual de compatibilidade. O consentimento para pacotes e a recusa de `ID_LIKE=debian` em outras distros permanecem. A CI desta linha roda em `ubuntu-24.04`, com PostgreSQL, Docker, Xvfb e Python 3.12.

**Compatibilidade X11/Wayland:** o aplicativo Tk pode ser executado em Wayland, mas a automação `xdotool` de janelas de terceiros permanece limitada a sessões X11 locais com consentimento por ação. A inspeção de dependências não comprova microfone, câmera, Ollama em execução, modelo instalado ou PostgreSQL saudável.

O código de voz, visão, integrações, atualizações verificadas e interface visual permanece preservado. Consulte as [notas da v0.8.2](docs/RELEASE_NOTES_v0.8.2.md) para a matriz de suporte, critérios de aceite e adaptações planejadas.

---

# v0.8.1 — Linux Bootstrap & Verified Self-Update (código integrado; release pendente)

A implementação original da v0.8.1 iniciou um instalador guiado para a família Debian/Ubuntu. A v0.8.2 o restringiu temporariamente ao Ubuntu Desktop 24.04 LTS; a seção atual de compatibilidade descreve a ampliação posterior. O instalador verifica dependências do sistema e propõe sua instalação por **sudo apt-get com autorização**. Prepara ambiente Python virtual **exclusivo e isolado por versão**, instala as dependências Python (voz/visão) e disponibiliza o comando gerenciado `~/.local/bin/nexus-core`. Pode configurar o PostgreSQL local com credencial aleatória protegida em arquivo 0600; se detectar banco ou usuário `nexus` já existente, não o altera e oferece criar o banco separado `nexus_core` após confirmação.

**Correção na v0.9.9:** a instalação para antes de criar o ambiente Python e
o launcher se não houver senha PostgreSQL local utilizável. Após uma recusa
ou quando banco/usuário já existirem, configure a credencial manualmente
com `NEXUS_DATABASE_PASSWORD` e execute novamente o instalador. Um arquivo
de credenciais privado porém inválido não conta como configuração pronta.
Essa verificação de presença/formato não substitui o teste de autenticação
no PostgreSQL nem a homologação da instalação em Ubuntu físico.

```bash
# Em um checkout revisado desta versão, sem sudo:
python3 scripts/install_linux.py
# Após a instalação, iniciar pelo launcher gerenciado:
~/.local/bin/nexus-core
```

O instalador pergunta expressamente se o usuário deseja ativar **atualizações automáticas**. Quando autorizado, o launcher consulta o repositório oficial GitHub por releases **estáveis**, confere versão, URL, nome exato do wheel, limite de tamanho e **SHA-256 divulgado na API GitHub**. A atualização é baixada sob diretório privado e instalada em novo venv, com verificação do executável antes de trocar atomicamente o link `current`; a instalação anterior é mantida para recuperação. Enquanto o assistente funciona, uma thread **opt-in** pode preparar releases novas a cada hora, mas **só instala na próxima inicialização**. Sem internet, o CORE já instalado continua operando.

**Não há `curl | bash`, instalação silenciosa como root, scripts de terceiros desconhecidos, atualizações de código não estável ou mudança do visual do assistente.** A segurança depende da integridade do GitHub e do digest; ainda não há assinatura independente nem lockfile integral dos pacotes transitivos. A gestão de Ollama, modelos de voz Vosk, permissões de áudio/câmera e acesso seguro ao Docker pode exigir passos próprios. O instalador automático atual aceita Ubuntu com requisitos compatíveis; Debian, SteamOS/Arch e outras distribuições recebem diagnóstico, sem comandos de pacotes incompatíveis.

Esse código está integrado à `main`, mas segue sem release estável e sem homologação física da instalação. Consulte as [notas da v0.8.1](docs/RELEASE_NOTES_v0.8.1.md) para requisitos, limites e testes de aceitação.

---

# v0.8.0 — Device Registry Foundation (código integrado; release pendente)

A primeira entrega da linha **Devices & Distributed Architecture** estabelece um catálogo declarativo de dispositivos Arduino e ESP32, **sem conexão física, descoberta ou comunicação de rede**. O pacote `nexus.devices` valida manifestos `nexus.devices.v1`, limitados a **32 itens e 16 KiB**, e implementa um registro atômico e efêmero em memória. Os dados são declarações do usuário, não leituras de sensores nem dispositivos emparelhados.

Apenas as famílias `arduino` e `esp32` são aceitas, e somente capacidades descritivas de leitura como `temperature.read`, `humidity.read`, `motion.read`, `position.read` e `battery.read`. O contrato rejeita endpoints, credenciais, comandos, parâmetros adicionais, identificadores duplicados e qualquer transporte diferente de `disabled`.

Diagnósticos sem hardware nem inicialização do modelo ou PostgreSQL:

```bash
nexus-core --devices-check
# Para validar seu próprio manifesto JSON através de stdin:
nexus-core --devices-preview-stdin < exemplo-dispositivos.json
```

A prévia confirma apenas a conformidade do manifesto; ela mostra `connected_devices: 0` e não registra dispositivos fora da memória do processo. **Não há integração serial/USB, BLE, MQTT, Wi-Fi, LoRa, telemetria real, operação remota ou controle de atuadores.** A confirmação por ação continuará obrigatória antes de qualquer futura comunicação com dispositivos; essa comunicação não faz parte desta versão.

A v0.8.0 é construída em PR separado **sobre a v0.7.3**, ainda não integrada à `main` por depender da homologação de desktop X11 real. A CI precisa validar o commit de cada PR; publicação/merge seguirão a ordem de dependências. Interface nativa, visual aprovado, áudio feminino/masculino, escuta com pausa, visão consentida, PostgreSQL e Ollama permanecem inalterados. Consulte as [notas v0.8.0](docs/RELEASE_NOTES_v0.8.0.md).

---

# v0.7.3 — Desktop Target Integrity (desenvolvimento)

A v0.7.3 reforça a integridade do destino de digitação/navegação no **Linux X11 local**. A ferramenta de leitura pontual `desktop_window_info` passa a retornar `window_id`, `window_title`, `window_pid` e `window_class`. Os quatro atributos passam a ser **obrigatórios** nas ferramentas `desktop_type_text` e `desktop_navigate`. A janela Tk apresenta o ID, título, PID, classe e a ação proposta no diálogo de consentimento individual.

Após a confirmação do usuário, o adaptador `xdotool` consulta novamente título, PID e WM_CLASS do mesmo ID. Identidade alterada, metadados ausentes ou valores inválidos **bloqueiam a operação antes do envio**. São preservadas as quatro teclas permitidas, o limite de 300 caracteres, a proibição de shell/cliques/atalhos arbitrários e o modo consultivo **Sugerir**. A consulta inicial e a revalidação usam subprocesso sem shell com timeout e saída limitada.

**Limite de segurança:** PID e WM_CLASS são declarações não autenticadas de clientes X11; não impedem falsificação, reutilização nem eliminam integralmente corridas entre a última consulta e a ação. Os aplicativos podem rejeitar eventos `XSendEvent`. Janelas sem PID ou WM_CLASS não podem receber comandos, por decisão de segurança. Não há suporte Wayland, controle autônomo contínuo ou captura automática. O comando `nexus-core --desktop-check` permanece **passivo**, sem testar o X11 real.

**Compatibilidade:** chamadas antigas que informam somente ID/título agora são recusadas. Primeiro consulte `desktop_window_info`, depois solicite a operação na janela reconhecida, confira todos os atributos e autorize aquela ação individualmente. Voz, visão mediante consentimento, PostgreSQL local, Ollama e identidade visual são preservados.

**Qualidade/publicação:** testes de regressão para PID, classe e identidade de destino estão na branch; a CI integral Python 3.12/PostgreSQL/Docker/Xvfb e a homologação em X11 físico continuam pendentes. **Não há tag ou release estável v0.7.3 nesta etapa.** Detalhes: [Release notes v0.7.3](docs/RELEASE_NOTES_v0.7.3.md).

---

# v0.7.2 — Desktop Interaction Safety & Diagnostics

Esta versão consolida a verificação passiva das condições necessárias
para interação X11 e reforça a documentação dos limites de autorização.
O comando `nexus-core --desktop-check` continua sem abrir janela,
consultar o servidor X11, pressionar teclas ou iniciar PostgreSQL e Ollama.
Além dos campos anteriores, seu JSON agora informa `ready`, `reason`,
`navigation_actions`, `typing_max_characters` e
`confirmation_per_action`. Os motivos estáveis são `READY`,
`WAYLAND_SESSION`, `LOCAL_X11_DISPLAY_REQUIRED` e `XDOTOOL_MISSING`.
`ready` indica apenas que a sessão e o executável aparentam estar
disponíveis: não testa janela, permissão X11, foco nem aceitação das
teclas pelo aplicativo de destino.

A consulta e as ações continuam limitadas ao Linux X11 local. A digitação
e a navegação exigem confirmação **por ação**, revalidam o título do ID
da janela aprovada após o diálogo e registram decisão/execução no
`SecurityGate`. As quatro ações de navegação e o limite de 300 caracteres
estão expostos no diagnóstico para facilitar a verificação do contrato.
O relatório de sucesso do subprocesso comprova a tentativa de envio,
sem provar efeito na interface. Sessões Wayland, display remoto e ausência
de `xdotool` são identificados sem tocar no desktop. Os testes cobrem
essa classificação sem usar o X11 real; compatibilidade física depende
de homologação no Linux do usuário.

O banco de dados da aplicação permanece **exclusivamente PostgreSQL
local**. Documentação e testes de rejeição de provedores inválidos foram
alinhados com essa configuração. Voz local feminina/masculina, escuta
contínua com pausa, conversa via Ollama e análise visual pontual com
consentimento mantêm os limites documentados nas versões anteriores.

**Marco v0.7.3 em desenvolvimento:** consulte a seção inicial para os contratos e limites da verificação de identidade. A integração e a publicação dependem da validação real.

---

# v0.7.1 — Controlled Desktop Navigation

Esta versão incorpora **navegação limitada por teclado no desktop X11**,
preservando integralmente o design da janela Tk, a conversa local,
a fala feminina/masculina e a resposta em voz às análises autorizadas
de Imagem, Tela e Câmera.

## Nova ferramenta: desktop_navigate

O assistente pode **propor UMA ação de navegação** na janela X11
especificamente indicada por `window_id` e `window_title`. São
permitidas somente estas quatro ações (identificadores técnicos
estáveis, que também aparecem no diálogo de consentimento):

| Ação permitida | Tecla X11 enviada | Finalidade |
| --- | --- | --- |
| `next_field` | `Tab` | Tentar avançar para o próximo campo |
| `previous_field` | `ISO_Left_Tab` | Tentar retornar ao campo anterior |
| `page_up` | `Prior` | Tentar mover uma página para cima |
| `page_down` | `Next` | Tentar mover uma página para baixo |

O comando envia **apenas uma tecla predefinida** por operação.
Não permite `Enter`, `Escape`, atalhos Ctrl/Alt, cliques,
coordenadas, texto livre como tecla, repetição, macros ou shell.
A navegação **não escolhe por conta própria aplicações ou campos**.

## Autorização, segurança e auditoria

A nova ferramenta tem risco **MEDIUM** e passa pelo
`ToolExecutor` e `SecurityGate`. A política padrão exige
**confirmação humana por operação**, inclusive quando a proposta
foi produzida pelo modelo local. Sem autorização a operação não
é executada. O diálogo mostra a janela (ID e título) e o nome
exato da ação, antes de solicitar consentimento.

O host usa `xdotool` **sem shell**, com limite de tempo, revalida
o título do **mesmo ID de janela após a confirmação** e envia uma
tecla direcionada àquela janela. Um ID inválido, título alterado,
ação fora da lista, display remoto ou sessão Wayland bloqueia
a operação. Uma falha do subprocesso não é reportada como sucesso.
Os registros de autorização e de execução seguem o mecanismo de
auditoria existente.

A consulta `desktop_window_info` da v0.7.0 permanece como
forma de obter metadados da janela ativa sem captura de pixels.
A ação `desktop_type_text` continua restrita a texto curto
com consentimento específico. O botão **Sugerir** permanece
consultivo, sem executar ferramentas.

## Como utilizar

1. No desktop **Linux X11 local**, instale `xdotool` e
   inicie o NEXUS CORE normalmente.
2. Solicite ao assistente identificar a janela ativa. Depois,
   peça algo como: **"Avance um campo nessa janela"** ou
   **"Mova uma página para baixo na janela informada"**.
3. Confira no diálogo o **ID, título e ação**; só então
   confirme. Para navegar novamente, é necessário novo pedido
   e nova confirmação.

Diagnóstico passivo, sem teclado, X11 ativo ou acesso a imagens:

```bash
nexus-core --desktop-check
```

## Limites reais e próximos passos

Programas X11 podem ignorar eventos sintéticos `XSendEvent` e
focar elementos de forma diferente. O resultado indica apenas
que a tecla foi enviada ao subprocesso, **não comprova a
navegação na interface do programa**. Não utilize esta função
em diálogos ou formulários sensíveis antes de homologar o
comportamento no aplicativo Linux real.

**X11 local apenas**, com `xdotool` opcional. Não há
automação Wayland, captura contínua, exploração livre da área
de trabalho ou execução autônoma de sequências. Os testes
da CI simulam subprocessos e confirmação, sem substituir
testes físicos de desktop, microfone, câmera, alto-falantes
ou modelo multimodal. Nenhum custo adicional ou serviço
hospedado foi introduzido.

**Marco seguinte:** `v0.7.2 — Desktop Interaction Safety & Diagnostics`
foi implementado com diagnóstico passivo ampliado. Consulte a seção inicial.

---

# v0.7.0 — Controlled Desktop Automation Foundation

Este marco inicia **automação controlada do desktop Linux**, preservando
a identidade visual existente e as ferramentas de conversação, visão e voz
das versões anteriores. Automação é **por solicitação do usuário,
uma ação de cada vez**, nunca controle livre do sistema pela IA.

## O que foi implementado

- **desktop_window_info**: consulta somente o **ID e título da janela
  atualmente ativa** na sessão Linux **X11**. É uma ferramenta de
  leitura de metadados, sem screenshot, gravação ou interação.
- **desktop_type_text**: solicita uma **digitação pontual de texto
  imprimível de até 300 caracteres** na janela X11 de ID e título
  explicitamente informados. **Não envia Enter**, atalhos, mouse,
  URLs ou comandos de terminal por conta própria.
- O `ToolExecutor` obriga a passagem pelo `SecurityGate`.
  `desktop_type_text` tem risco **MEDIUM** e exige confirmação
  humana **a cada execução** com a política padrão; sem confirmação,
  a ferramenta falha sem enviar caracteres.
- O diálogo da interface Tk exibe a **janela de destino e o texto
  a digitar**, para que a autorização corresponda à ação real.
  Após o consentimento, a ferramenta verifica novamente **o ID
  e título da janela aprovada** antes de enviar qualquer evento.
- Argumentos passam por contratos tipados e validação adicional
  contra controles de teclado, limites excessivos, IDs inválidos
  e títulos alterados. O resultado registra **número de caracteres
  cujo envio foi solicitado**, não garante que a aplicação os aceitou.
- Chamada ao `xdotool` como subprocesso Linux com argumentos
  delimitados, **sem shell**, tempo limite e erros sanitizados.
  Nenhum serviço remoto, captura de imagens ou acesso contínuo
  foi adicionado à automação.

## Diagnóstico e operação

Instale gratuitamente o utilitário `xdotool` na sessão X11 Linux
conforme sua distribuição. O comando abaixo **somente verifica** a
presença de dependências e o tipo de sessão; não abre aplicações,
não interage com janelas, não inicia PostgreSQL nem consulta Ollama:

```bash
nexus-core --desktop-check
```

O fluxo pela conversa (texto ou voz local) é:

1. Solicite ao NEXUS CORE: **"Qual é a janela ativa?"**
   (`desktop_window_info` consulta o ID e título).
2. Solicite: **"Digite 'Olá!' naquela janela"**. O modelo pode
   propor a ferramenta `desktop_type_text` com o ID/título do
   contexto da conversa, mas não recebe autoridade para executá-la.
3. A interface mostra uma autorização pontual, incluindo a janela
   e o texto. **Somente após aprovação** o host revalida a janela
   e tenta enviar os caracteres. Recusar/cancelar não digita nada.

A entrada visual de **Imagem/Tela/Câmera** continua exigindo
autorização por análise e respondendo em voz feminina/masculina
quando a leitura de voz estiver habilitada. O botão **Sugerir**
segue **somente consultivo**, com ferramentas proibidas.
O botão **Cancelar** continua cooperativo; não desfaz texto já
inserido ou operações realizadas.

## Limites e garantias reais

**Somente X11 local nesta primeira versão.** Sessões Wayland ou
XWayland e DISPLAY com endereço remoto são recusados. Alguns
programas X11 ignoram eventos `XSendEvent` enviados por ID de
janela; mesmo com saída de comando bem-sucedida, não há garantia
de que texto tenha aparecido. O usuário precisa conferir o resultado
na aplicação. A ferramenta não localiza campos específicos nem
sabe se o foco está em um campo de senha. **Não autorize
digitação de dados sigilosos ou em formulários sensíveis.**

Automação de janelas age diretamente no **host X11**, fora
do sandbox Docker de comandos; por isso é intencionalmente
limitada e depende de consentimento específico. A v0.7.0
**não implementa** mouse, cliques, atalhos, execução em lote,
navegação, comandos shell fora do sandbox, controle irrestrito
nem observação de tela constante.

A CI roda testes de contratos, autorização, ID/título alterados,
argumentos inválidos, recusa de Wayland/DISPLAY remoto, subprocessos
e diagnóstico sem acesso à interface. **O uso físico do desktop,
o campo de texto e compatibilidade de aplicativos X11 ainda
precisam ser homologados no computador Linux** do usuário.

## Próximo incremento

`v0.7.1 — Controlled Desktop Navigation` foi implementada com
quatro teclas estritamente delimitadas, sem alterar o layout existente
nem liberar execução autônoma de macros. Consulte a seção da v0.7.1.

---

# v0.6.3 — Conversation Reliability

Versão corretiva: **sem mudanças de design**, melhorias de concorrência de
áudio, cancelamento seguro de autorizações e integridade do repositório.

## Correções técnicas

**Reconhecimento de voz:** cada escuta Vosk utiliza uma geração e um registro
de captura pendente. Pausar e retomar rapidamente não dispara gravações ALSA
sobrepostas: uma nova escuta só começa quando a anterior encerra. Eventos
atrasados de uma geração obsoleta não podem alterar o estado da atual.

**Fala eSpeak NG:** cada reprodução recebe uma geração. Ao silenciar, mudar
de pedido, cancelar ou fechar, o áudio anterior é invalidado. Um evento
tardio de término não pode desativar uma reprodução mais recente, reativar
o microfone prematuramente ou apresentar um erro de voz já cancelada.
Workers de áudio enfileirados antes do cancelamento recusam iniciar fala.

**Autorização cancelada:** a ação Cancelar recusa imediatamente confirmações
de ferramentas ainda pendentes. Mesmo uma resposta positiva tardia de um
diálogo já cancelado não reautoriza a ação. Operações já executadas
não são revertidas pelo cancelamento cooperativo.

**Imagem, Tela e Câmera:** preservadas as respostas de visão por texto
e voz feminina ou masculina no Linux, com leitura em voz alta habilitada
por padrão e opção de silenciamento. As capturas continuam exigindo
consentimento por análise, sem observação contínua.

## Revisão transversal dos arquivos

Inventário inicial realizado na main v0.6.2: **191 arquivos rastreados**,
incluindo código, testes, recursos visuais, workflows e documentação.
A suite adicionou varredura de integridade dos arquivos disponíveis
no checkout: sintaxe de todos os módulos Python, codificação UTF-8
de arquivos textuais, parsing de JSON/SVG, verificação de ícones do
manifesto e consistência do README, versão do pacote e notas de release
das versões v0.4.0 a v0.6.3.

A CI Linux continua verificando compilação e todos os testes com Python
3.12, PostgreSQL 16, Docker e Xvfb; os novos testes reproduzem as condições
de corrida de fala, escuta, cancelamento e confirmação humana.
Essa verificação **não equivale à inspeção semântica manual linha a linha**
de cada arquivo e não substitui a homologação física de câmera, microfone,
áudio e modelo visual Ollama no computador do usuário.

**Limitações:** voz local por turnos, não full-duplex com latência instantânea.
Cancelamento cooperativo pode aguardar processos ou chamadas em curso e
não desfaz operações já executadas. Sem serviços pagos, hospedagem ou
mudanças de interface.

---

# v0.6.2 — Guided Autonomy & Conversation

Esta versão fortalece a conversação guiada, **a resposta por voz nas três
fontes de visão** e o controle humano sobre operações demoradas, sem
alterar a identidade visual atual da janela Linux.

## O assistente responde por voz às análises de Imagem, Tela e Câmera

Na interface desktop, ao selecionar **Imagem**, **Tela** ou **Câmera**
e autorizar **aquela única análise**, o assistente:

1. Captura/lê uma imagem autorizada e envia somente ao modelo multimodal
   do **Ollama local** (dependências `.[vision]` e modelo `gemma3:4b`
   instalados separadamente).
2. Mostra a descrição resultante na conversa em texto.
3. **Lê a resposta em voz alta** usando o **eSpeak NG** na variante
   escolhida: **Feminina** ou **Masculina**. A opção **Ler respostas
   em voz alta** já inicia marcada. Isso é validado por testes de
   interface **separados para Imagem, Tela e Câmera** e seleção de voz.
4. Retoma a escuta contínua local do Vosk após terminar de falar,
   se o microfone não tiver sido pausado. A descrição textual pode
   contextualizar perguntas seguintes sem nova captura automática.

O usuário mantém controle para **desmarcar a leitura em voz alta**;
assim, as três análises continuam retornando texto, mas **sem som**.
O eSpeak NG limita cada fala a **2.400 caracteres**; textos maiores
permanecem disponíveis integralmente no transcript (limite de
descrição visual: 12.000 caracteres). Nenhuma voz externa paga é usada.
Se o eSpeak NG ou dispositivo de áudio falhar, o texto permanece
disponível e a falha pode aparecer na barra de estado.

## Sugestões práticas com autorização explícita para ações

O botão discreto **Sugerir** permite solicitar orientações concretas
com o contexto efêmero da conversa, sem precisar montar um prompt.
Essa solicitação usa modo **somente consultivo**: o `AgentPlanner`
recebe uma proibição explícita de executar ferramentas,
**independentemente de o modelo propor um `tool_call`**.
Por isso, sugestões não podem iniciar shell, capturas de tela,
leitura de arquivos ou outros efeitos colaterais.

Conversas normais continuam respondendo a dúvidas e podendo
propor uma ferramenta autorizada, limitada a no máximo uma
proposta por turno e mediada pelo `SecurityGate`, confirmação
humana e políticas de risco. **Autonomia é orientada e auditável,
não irrestrita**. Nada funciona como observador contínuo em
segundo plano, nem captura câmera/tela sem confirmação por ação.

## Cancelamento cooperativo

O botão **Cancelar** fica disponível enquanto uma pergunta, sugestão
ou análise visual está em processamento. Ao acioná-lo:

- a resposta pendente não é exibida nem lida em voz alta;
- capturas e análises visuais concluídas depois do cancelamento
  não acrescentam descrição ao histórico da conversa;
- o agente verifica cancelamento antes do planejamento e
  imediatamente antes de qualquer nova execução de ferramenta;
- as autorizações futuras continuam sendo solicitadas normalmente.

**Limitação:** cancelamento é **cooperativo**, não uma interrupção
instantânea garantida de todo processo. Não desfaz comandos já
executados, não reverte operações confirmadas e pode precisar
aguardar uma chamada Ollama ou captura já iniciada terminar
para liberar os controles. A interface permanece responsiva.

## Testes e compatibilidade

Testes automatizados verificam a resposta falada por fonte
(Imagem/Tela/Câmera), voz masculina/feminina, opção de silêncio,
recusa de consentimento, cancelamento de diálogo e visão,
sugestão sem ferramentas e regressão da interface Tk sob Xvfb.
As imagens continuam não sendo armazenadas pelo NEXUS CORE,
e o PostgreSQL local segue como único banco.

A interação por voz ainda acontece **por turnos** (escuta, processa,
responde e volta a escutar), não é full-duplex de latência zero.
Os testes da CI usam equipamentos simulados; a homologação
de microfone/alto-falantes/câmera e Ollama multimodal real
precisa ser executada no hardware Linux do usuário.

---

## Histórico de marcos e documentação

### Índice completo das versões históricas

A documentação de desenvolvimento inicial, mantida integralmente nas
seções **Histórico de releases** e **Roadmap** deste README, registra:
`v0.1.0`, `v0.1.1`, `v0.1.2`, `v0.1.3`, `v0.1.4`,
`v0.1.5`, `v0.1.6`, `v0.1.7`, `v0.1.8`, `v0.1.9`;
`v0.2.0`, `v0.2.1`, `v0.2.2`, `v0.2.3`, `v0.2.4`;
`v0.3.0`, `v0.3.1`, `v0.3.1.1`, `v0.3.1.2`,
`v0.3.1.3`, `v0.3.2`, `v0.3.3`, `v0.3.4`,
`v0.3.5`, `v0.3.6`, `v0.3.7`, `v0.3.8`, `v0.3.9`.
A lista acima é **registro histórico**, não declaração de que cada
item tem uma release oficial publicada ou homologação física.
A nota histórica inicial também está acessível diretamente em [v0.3.9](docs/RELEASE_NOTES_v0.3.9.md).
As notas dedicadas de `v0.3.9` até `v0.9.12` estão disponíveis
em `docs/RELEASE_NOTES_v*.md`. O histórico **não foi apagado
nem reescrito**: as respectivas seções detalhadas permanecem abaixo.


O README mantém as seções completas das versões anteriores e as notas
oficiais abaixo, para que decisões, limitações e evolução permaneçam
rastreáveis no GitHub:

| Versão | Marco | Documentação |
| --- | --- | --- |
| v0.3.7 | Local Voice Conversation | Histórico do README |
| v0.3.8 | Continuous Local Voice Conversation | Histórico do README |
| v0.3.9 | Linux Stability & Release | [Release](https://github.com/ricardogomesbarreto/Nexus-Core/releases/tag/v0.3.9) |
| v0.4.0 | Persistent Memory Foundation | [Notas](docs/RELEASE_NOTES_v0.4.0.md) |
| v0.4.1 | Knowledge Base | [Notas](docs/RELEASE_NOTES_v0.4.1.md) |
| v0.5.0 | Voice Foundation | [Notas](docs/RELEASE_NOTES_v0.5.0.md) |
| v0.6.0 | Vision & Screen Understanding Foundation | [Notas](docs/RELEASE_NOTES_v0.6.0.md) |
| v0.6.1 | Vision Desktop Integration | [Notas](docs/RELEASE_NOTES_v0.6.1.md) |
| v0.6.2 | Guided Autonomy & Conversation | [Notas](docs/RELEASE_NOTES_v0.6.2.md) |
| v0.6.3 | Conversation Reliability | [Notas](docs/RELEASE_NOTES_v0.6.3.md) |
| v0.7.0 | Controlled Desktop Automation Foundation | [Notas](docs/RELEASE_NOTES_v0.7.0.md) |
| v0.7.1 | Controlled Desktop Navigation | [Notas](docs/RELEASE_NOTES_v0.7.1.md) |
| v0.7.2 | Desktop Interaction Safety & Diagnostics | [Notas](docs/RELEASE_NOTES_v0.7.2.md) |
| v0.7.3 | Desktop Target Integrity — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.7.3.md) |
| v0.8.0 | Device Registry Foundation — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.0.md) |
| v0.8.1 | Linux Bootstrap & Verified Self-Update — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.1.md) |
| v0.8.2 | Ubuntu Desktop Baseline & Portability — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.2.md) |
| v0.8.3 | Ubuntu First-Run Doctor — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.3.md) |
| v0.8.4 | Ubuntu Readiness Preflight — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.4.md) |
| v0.8.5 | Ubuntu Recovery & Documentation Integrity — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.5.md) |
| v0.8.6 | Ubuntu Maintenance Coordination — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.6.md) |
| v0.8.7 | Ubuntu Pre-Activation Validation — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.7.md) |
| v0.8.8 | Managed Launcher Integrity — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.8.md) |
| v0.8.9 | Ubuntu Activation Journal & Offline Repair — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.8.9.md) |
| v0.9.0 | Multimodal Privacy & Accessibility Status — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.0.md) |
| v0.9.1 | On-Demand Privacy Status — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.1.md) |
| v0.9.2 | Spoken Privacy Status — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.2.md) |
| v0.9.3 | Typed Privacy Status — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.3.md) |
| v0.9.4 | Accessible Cancellation Shortcut — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.4.md) |
| v0.9.5 | Spoken Reply Interruption — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.5.md) |
| v0.9.6 | TTS Startup Cancellation Safety — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.6.md) |
| v0.9.7 | Keyboard-Gated Vision Requests — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.7.md) |
| v0.9.8 | Accessible Speech Output Toggle — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.8.md) |
| v0.9.9 | Spoken Desktop Controls — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.9.md) |
| v0.9.10 | Spoken Voice Selection — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.10.md) |
| v0.9.11 | First-Run PostgreSQL Authentication — integrado à main; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.11.md) |
| v0.9.12 | Authorized Desktop Actions — integrado à main; aceite físico pendente; sem tag | [Notas](docs/RELEASE_NOTES_v0.9.12.md) |

O histórico inicial v0.1.x–v0.3.x segue no roadmap detalhado abaixo.
Consulte a página de [releases](https://github.com/ricardogomesbarreto/Nexus-Core/releases)
para identificar tags oficiais, cada qual condicionada à validação CI
da versão correspondente.

---

# v0.6.1 — Vision Desktop Integration

Esta versão adiciona **visão à própria janela nativa Linux**, sem alterar a
identidade visual existente. O assistente mantém sua conversa por voz
Vosk/ALSA e suas respostas em eSpeak NG masculino/feminino; a visão agora
participa da conversa por meio de **descrições textuais efêmeras** e
sugestões pertinentes, sujeitas às mesmas regras de segurança.

## Utilização na interface gráfica

Na janela do NEXUS CORE, a linha discreta **Visão local sob autorização**
oferece três botões: **Imagem**, **Tela** e **Câmera**. Cada acionamento:

1. É iniciado por um clique explícito. Em **Imagem**, escolhe-se um raster
   aceito no HOME (PNG/JPEG/WEBP/GIF/BMP/TIFF/AVIF, conforme decodificador).
   Em **Câmera**, o aplicativo filtra os nós V4L2, escolhe automaticamente
   a única câmera de captura disponível ou pede escolha se houver várias;
   em **Tela**, solicita uma janela/monitor no portal Wayland quando possível.
2. Solicita uma **pergunta visual** de até 2.000 caracteres para imagem/tela;
   a câmera usa uma pergunta descritiva padrão sem diálogo adicional.
3. Exibe confirmação **para aquela única captura/leitura e análise no
   Ollama local**. Cancelar qualquer diálogo impede a captação.
4. Pausa temporariamente a escuta do microfone, executa a captura e
   análise em thread sem bloquear a janela, e apresenta a resposta no
   transcript. Com leitura em voz alta ativada, o assistente pode
   enunciar também a descrição.
5. Após concluir, libera botões e retorna à escuta, se estiver ativa.

Os pixels **não entram automaticamente no histórico da conversa**;
apenas uma descrição textual resumida, sujeita ao limite de seis turnos,
permanece na sessão **enquanto a janela está aberta**. Isso permite
perguntas como "O que podemos melhorar nessa tela?", usando a descrição
anterior como contexto, sem nova captura automática.

## Diálogo, sugestões e autonomia delimitada

O NEXUS CORE deve **responder perguntas formuladas normalmente**,
pelo texto ou fala local, e **sugerir ações úteis quando pertinente**.
O Agent recebeu orientações explícitas para:
- responder em português brasileiro, com clareza e naturalidade;
- recomendar próximos passos sem afirmar que já os executou;
- propor no máximo uma ferramenta por solicitação;
- nunca iniciar captura, leitura de arquivos, comandos ou rotinas
  autônomas sem solicitação pertinente;
- submeter toda execução de ferramenta ao `ToolExecutor`,
  `SecurityGate`, políticas de risco e confirmação humana quando exigida.

**O sistema ainda não é um assistente full-duplex com interrupção de fala
instantânea**: capta uma fala, processa localmente, responde e retoma
a escuta. Latência depende do microfone, Vosk, Ollama, CPU/GPU e eSpeak
NG. "Conversa em tempo real" aqui significa interação contínua por
turnos, sem botão obrigatório de pressionar-para-falar. Não inclui
observação contínua da tela, iniciativas em segundo plano ou ações
irreversíveis independentes.

## Instalação opcional

```bash
python -m pip install -e '.[voice,vision]'
nexus-core --desktop
```

Instale o modelo Vosk brasileiro no caminho configurado e um modelo
multimodal local `gemma3:4b` no Ollama para análise de imagens.
As capturas requerem `grim` em sessões Wayland compatíveis,
ImageMagick `import` no X11 ou FFmpeg/V4L2 para webcam. A interface
de texto e voz continua funcionando se a visão não estiver instalada.
Não há monitoramento nem retenção automática de imagens, pagamentos
ou serviços de nuvem.

**Homologação pendente:** câmera, microfone, alto-falantes, integração
Wayland/X11 e o modelo visual multimodal rodando em hardware Linux
real. A CI verifica a GUI em display virtual e dispositivos simulados.
A autorização por captura e as permissões do Linux continuam
obrigatórias.

---

# v0.6.0 — Vision & Screen Understanding Foundation

A visão local está disponível apenas mediante **solicitação explícita pela CLI**.
Esta versão não abre a câmera automaticamente, não monitora a tela, não
armazena imagens nem entrega imagens como ações para o Agent. A interface
Tk aprovada, o modo de voz e a arquitetura PostgreSQL foram preservados.

## Recursos implementados

- **Imagem local:** leitura de arquivos PNG, JPEG e WEBP com validação
  por descritores de arquivo ancorados no HOME autorizado (`O_NOFOLLOW`).
  Links simbólicos, caminhos protegidos, arquivos especiais ou externos
  ao HOME são recusados.
- **Tela:** captura de **um único quadro**, quando solicitada, utilizando
  `grim` em sessões Wayland compatíveis ou `import` do ImageMagick em X11.
  Não funciona automaticamente em todos os compositores ou portais Linux.
- **Câmera:** captura de **um quadro** de `/dev/video0` a `/dev/video9`
  por FFmpeg/V4L2. O dispositivo é escolhido por índice numérico
  explícito e não existe streaming contínuo.
- **Normalização:** Pillow faz validação e conversão para PNG RGB,
  descartando metadados EXIF e textuais antes do envio. Máximos:
  **6 MiB** de entrada e saída, **4.096 px** por dimensão e **8 milhões
  de pixels**. Captura externa tem tempo limite de **20 segundos**;
  subprocessos são executados sem shell, com saída temporária anônima.
- **Compreensão multimodal local:** chamada pontual à API `/api/chat`
  do Ollama exclusivamente em origem HTTP loopback validada, com imagem
  codificada em base64 e uma pergunta limitada a **2.000 caracteres**.
  Modelo visual padrão: `gemma3:4b`, **não instalado automaticamente**.
  A transcrição/texto da resposta tem limite de **12.000 caracteres**.
- **Diagnóstico:** `--vision-check` relata presença de dependências
  sem abrir câmera, capturar tela ou acessar o Ollama.

## Como utilizar

Instale o suporte de visão com `python -m pip install -e '.[vision]'`.
Tenha um modelo **multimodal** instalado no Ollama local; por exemplo,
instale `gemma3:4b` separadamente se seu hardware suportar esse modelo.
O `qwen3:1.7b` utilizado para conversas comuns não é automaticamente
um modelo multimodal e **não** deve ser usado para análise de imagens.

```bash
nexus-core --vision-check
nexus-core --vision-image ~/Imagens/foto.jpg --vision-question "O que aparece?"
nexus-core --vision-screen --vision-question "Descreva a janela atual"
nexus-core --vision-camera 0 --vision-question "O que está na câmera?"
nexus-core --vision-image ~/Imagens/figura.png --vision-model gemma3:4b
```

**Dependências externas opcionais, gratuitas:** `grim` (Wayland,
se compatível), ImageMagick `import` (X11), FFmpeg (V4L2). Em desktops
Linux, permissão de acesso à câmera e à tela depende do ambiente. A
ausência dessas dependências não impede o funcionamento da conversa
por texto nem da voz.

**Privacidade e limitações:** capturas e imagens não são persistidas
pelo NEXUS CORE, mas **a imagem enviada ao Ollama local contém
os pixels visíveis, incluindo possíveis dados privados**. O runtime
Ollama é um processo separado, com seus próprios registros e controles.
Revise a tela/câmera antes da chamada. Não existe pedido automático
da IA para capturar imagens ou executar ferramentas do sistema após
a resposta visual. Não há OCR independente, monitoramento contínuo
ou API de visão disponível para a interface Tk nesta versão.

**Homologação pendente:** câmera e captura de tela em hardware real,
compatibilidade de Wayland/X11 e um modelo multimodal Ollama
instalado. A CI valida limites, políticas de acesso e mensagens com
fakes/mocks, mas não demonstra funcionamento com hardware real.

---

# v0.5.0 — Voice Foundation

Esta etapa consolida a **escuta contínua local** com Vosk/ALSA e
síntese de voz feminina ou masculina pelo eSpeak NG, recursos já
introduzidos nas versões v0.3.7/v0.3.8. A interface atual é mantida,
sem redesenho, sem gravação de conversas em disco e sem recursos pagos.

## Novidades

- **Frase de ativação opcional:** marque `Exigir "Nexus" para ativar` na
  janela para aceitar perguntas somente quando a transcrição local
  iniciar com "Nexus", "Ei Nexus", "Olá Nexus" ou "Hey Nexus".
  Exemplo: **"Nexus, explique redes de computadores"**. Somente o texto
  após o prefixo será enviado ao Agent. Fala sem a frase inicial
  será ignorada. Apenas dizer "Nexus" não dispara uma solicitação.
- **Compatibilidade:** a opção começa **desativada**, preservando a
  conversa contínua sem precisar pressionar botões ou pronunciar
  a palavra de ativação. O botão **Pausar escuta** e comandos de
  desligamento continuam disponíveis, sem alterações nas confirmações
  obrigatórias de ações sensíveis.
- **Diagnóstico local:** `nexus-core --voice-check` retorna um JSON
  que informa a presença de `arecord` (ALSA), `vosk`, modelo
  instalado e `espeak-ng`. Não inicializa PostgreSQL ou Ollama,
  não abre microfone, não reproduz áudio e não salva informações.
- **Testes:** reconhecimento de prefixos e rejeição de frases
  incidentais, modos de conversa, diagnósticos sem captura e testes
  integrados na GUI Tk com display virtual Linux.

## Verificar instalação

```bash
nexus-core --voice-check
```

Para usar a voz no Linux, instale `alsa-utils`, `espeak-ng`,
`pip install -e '.[voice]'` e configure um modelo Vosk local para
português brasileiro (`NEXUS_VOSK_MODEL_PATH`). O programa
continua funcional em modo texto na ausência dessas dependências.

**Limitações importantes:** a frase de ativação é reconhecida
**após** a transcrição do Vosk. Ela **não** é um mecanismo independente
de detecção de palavra-chave de baixo consumo, e o microfone permanece
ativo enquanto a escuta está habilitada. Para interromper a captura,
use **Pausar escuta** ou diga o comando de pausa reconhecido;
não dependa do filtro de frase para obter privacidade de microfone.

A CI verifica o fluxo com microfone simulado, saída eSpeak NG e
interface Tk via Xvfb, mas **não comprova** operação de um microfone,
alto-falante ou dispositivo ALSA específico de um computador real.
Essa homologação exige teste físico no Linux do usuário.

---

# v0.4.1 — Knowledge Base

A Knowledge Base é uma **biblioteca local de documentos opt-in**, sem crawling
da pasta pessoal, sem sincronização em nuvem e sem acesso automático da IA
aos conteúdos. O PostgreSQL local recebe apenas documentos **importados
explicitamente** pelo usuário por comando. A identidade visual, o Ollama,
a interface Tk e a voz existentes não foram redesenhados.

## Capacidades implementadas

- **Ingestão segura:** arquivos `.txt` e `.md` em UTF-8, máximo **256 KiB**
  por arquivo. A abertura acontece por descritores de arquivo autorizados
  pelo `PathSecurity` da v0.3.9; links simbólicos, diretórios protegidos,
  arquivos binários ou especiais e caminhos fora do HOME são recusados.
- **Indexação PostgreSQL:** tabelas `nexus_knowledge_documents`,
  `nexus_knowledge_chunks` e `nexus_knowledge_audit`, índice GIN de
  full-text search com dicionário `simple`, trechos de até **1.000
  caracteres** e sobreposição de 100 caracteres (até 320 trechos).
- **Deduplicação:** SHA-256 do texto normalizado; conteúdos repetidos
  não são reimportados mesmo com nomes/caminhos diferentes.
- **Retrieval:** busca em chunks por full-text ou substring literal,
  com queries SQL parametrizadas; respostas exibem IDs de documento
  e trecho para identificação de origem. A busca é lexical, **não
  semântica/vetorial**.
- **Lifecycle:** listagem, exclusão explícita de documento por ID e
  exclusão automática dos chunks relacionados via chave estrangeira.
- **Auditoria:** ação, ID, quantidade e horário, sem persistir texto de
  documentos, consultas ou arquivos na tabela de auditoria.
- **Integração com memória:** somente em `--knowledge-context` com
  `--knowledge-with-memory` o programa consulta também a memória
  da v0.4.0 e apresenta os dois conjuntos de resultados. O material
  **não é enviado automaticamente ao Ollama**.

## Comandos

```bash
nexus-core --knowledge-import ~/Documentos/minhas-notas.md
nexus-core --knowledge-list
nexus-core --knowledge-search "PostgreSQL"
nexus-core --knowledge-context "Redes"
nexus-core --knowledge-context "Redes" --knowledge-with-memory
nexus-core --knowledge-delete 1
nexus-core --knowledge-search "Python" --knowledge-limit 10
```

O ID de exclusão é ilustrativo. Limite de resultados: **1 a 20**.
`--knowledge-*` usa o PostgreSQL, sem precisar iniciar a interface
Tk ou o Ollama. Não é necessário reinstalar dependências extras.

**Segurança e privacidade:** os trechos, os nomes e caminhos dos arquivos
são armazenados em **texto claro no PostgreSQL local**. Não importe
segredos ou arquivos sensíveis. A cópia no banco continua existindo
após excluir o arquivo original; use `--knowledge-delete ID` para
excluí-la. Logs de auditoria preservam apenas metadados de operação.
Nenhuma proteção do código equivale a criptografia de disco.

**Limitações conscientes:** somente documentos TXT/Markdown, sem PDF,
DOCX, OCR, varredura de diretórios, embeddings ou RAG autônomo. Os
resultados são retornados ao terminal com identificação de origem;
não podem ampliar permissões do agente e não são injetados nos prompts
sem autorização explícita. A validação em hardware físico de áudio
permanece separada dos testes de CI.

---

# v0.4.0 — Persistent Memory Foundation

A memória persistente é **explícita e opcional**. Mensagens do chat e
respostas do Ollama **não são salvas automaticamente**. O histórico de
seis turnos continua temporário; não há recuperação automática durante a conversa.

- **PostgreSQL local:** tabelas `nexus_memories` e `nexus_memory_audit` criadas
  sob demanda, com PostgreSQL local e sem serviço em nuvem.
- **Operações:** salvar, listar, pesquisar texto literal case-insensitive, excluir
  por ID, exclusão total com confirmação e consulta de estatísticas.
- **Retenção:** padrão de 90 dias, entre 1 e 365; cada memória até 1.200
  caracteres. Memórias expiradas não aparecem nas consultas e são purgadas
  na operação seguinte.
- **Auditoria:** ação, ID, quantidade e horário, **sem texto salvo nem consulta**
  na tabela de auditoria.

### Comandos explícitos

```bash
# Modo mais privado: escreva no terminal e forneça pelo stdin:
nexus-core --memory-add-stdin --memory-days 90
# Alternativa (o texto pode ficar no histórico do terminal):
nexus-core --memory-add "Prefiro respostas objetivas" --memory-days 90
nexus-core --memory-list
nexus-core --memory-search "respostas"
nexus-core --memory-status
nexus-core --memory-delete 1
nexus-core --memory-clear --memory-confirm
```

O ID 1 acima é ilustrativo. Os comandos não iniciam o Ollama nem a interface
desktop. As memórias ficam em **texto claro no PostgreSQL local**. O argumento
de `--memory-add` pode aparecer no histórico do shell e na lista de processos.
`--memory-add-stdin` aceita até 1.200 caracteres pela entrada padrão sem
incluir a frase na linha de comando, mas não criptografa o banco:
**não armazene senhas, tokens ou outros segredos**. A versão não inclui
embedding, RAG, sincronização cloud ou memória automática do agente.

A release será etiquetada somente após CI aprovada no commit da `main`;
testes de microfone e alto-falantes físicos permanecem fora da CI.

---
# v0.3.9 — Hardening e expansão desktop

Escopo de implementação nesta linha:

- **Segurança de caminhos**: operações de leitura, listagem e consulta de
  metadados abrem arquivos e diretórios por descritores ancorados no HOME
  permitido, com `O_NOFOLLOW` em cada componente. A política é
  conservadora e recusa links simbólicos mesmo quando apontam para uma
  área autorizada. Nenhum caminho aberto depende de um novo
  `Path.resolve()` para efetivar a leitura.
- **Sandbox Docker**: o workspace autorizado é copiado por descritores
  para um diretório temporário privado antes do bind mount; o container
  vê um snapshot em modo somente leitura, nunca o caminho original
  mutável. O snapshot bloqueia links simbólicos, arquivos especiais,
  árvores com mais de **512 entradas (arquivos e diretórios)** ou **32 MB** e profundidade
  superior a oito níveis. Esse limite é de segurança, não uma quota
  comercial. Arquivos novos/modificados após o snapshot não aparecem
  na execução corrente.
- **Nova ferramenta**: `file_metadata` consulta tamanho e data de
  modificação de um arquivo regular autorizado, sem ler seu conteúdo.
  Usa o mesmo controle de recursos e as mesmas regras da
  ferramenta `read_file`.
- **Interface gráfica**: encerramento aguarda a saída dos workers de
  áudio, reconhecimento e inferência antes de destruir a janela e
  libera variáveis Tk na thread gráfica. O PNG oficial é exibido no
  cabeçalho Tk; o sprite SVG permanece disponível para evolução
  posterior.
- **CI**: ações compatíveis com Node 24, cancelamento de execuções
  obsoletas de PR, testes adversariais de troca de symlink e limites
  de snapshot.

**Critério de publicação:** o workflow de release gera a tag anotada
`v0.3.9` somente após CI bem-sucedida do commit correspondente da `main`.
Para confirmar a publicação, consulte as [releases oficiais](https://github.com/ricardogomesbarreto/Nexus-Core/releases).

**Homologação manual ainda necessária:** escuta e saída de voz com
microfone/alto-falantes físicos no Linux real (a CI usa fakes no
microfone). A nova ferramenta não concede acesso arbitrário ao
filesystem; só pode acessar arquivos regulares autorizados.

---

# Histórico de validação da v0.3.8 — 09/10/2026

A linha publicada é **v0.3.8 — Continuous Local Voice Conversation**. O
`pyproject.toml`, `Settings.version` e a tag
[`v0.3.8`](https://github.com/ricardogomesbarreto/Nexus-Core/releases/tag/v0.3.8)
concordam com essa versão. A tag aponta para o commit
[`1be4958`](https://github.com/ricardogomesbarreto/Nexus-Core/commit/1be495839a145c3c26e2272064d849dcf52f8799);
correções posteriores apenas de documentação não alteram a tag publicada.

A [CI da release](https://github.com/ricardogomesbarreto/Nexus-Core/actions/runs/37879650437)
foi aprovada no Ubuntu com Python 3.12, PostgreSQL 16, Docker e display
virtual: **625 testes aprovados, nenhum teste falho, dois avisos** de
`PytestUnraisableExceptionWarning` durante a destruição de objetos
Tkinter fora do loop da thread principal. O workflow também executou
`compileall` e verificou `nexus-core --version` (0.3.8).
Aprovação da CI não equivale a homologação completa em um computador pessoal.

**O que está efetivamente implementado:** janela nativa Tk, conversa de
texto com histórico efêmero de até seis turnos, Ollama local, uma
proposta de ferramenta por turno, confirmação individual das operações
que a exigem, PostgreSQL local obrigatório, sandbox Docker e escuta
automática opcional por Vosk/ALSA com saída eSpeak NG feminina ou
masculina. O modo texto permanece utilizável sem os componentes opcionais
de voz.

**Limitações da evidência:** a CI utiliza fakes para o microfone e a
escuta contínua; não demonstra funcionamento em um microfone físico,
modelo Vosk instalado e ambiente desktop de usuário. Os ativos de marca
e SVG são versionados, mas a janela Tk atual não renderiza o catálogo
completo de ícones. Não há distribuição desktop empacotada homologada,
memória de conversa persistente ou automação irrestrita do computador.

**Pendências identificadas na auditoria histórica da v0.3.8:** investigar os
dois avisos de finalização Tkinter; homologar entrada/saída de voz em
hardware Linux real; revisar mitigação de condições de corrida em
caminhos de arquivos entre a checagem de permissão e o acesso efetivo.

---

# Visão geral

O **Nexus Core** é a infraestrutura central de um assistente pessoal de inteligência artificial projetado para operar prioritariamente de forma local.

O programa roda como processo nativo no Linux. O comando `nexus-core` abre
a janela de conversa na sessão gráfica do usuário. A opção
`--sandbox-command` exige confirmação no terminal para cada execução isolada.
`--agent-prompt` aceita uma solicitação ao modelo local e pode propor uma única
chamada mediada pelo executor.
Na janela, confirmações surgem em um diálogo local; um turno pode produzir uma
resposta ou propor uma ação, com histórico curto mantido apenas em memória.
Com o modo de voz ativo, o Vosk transcreve o microfone sem botão de fala; as respostas
podem ser lidas em voz masculina neural Piper (quando instalada) ou voz
feminina RHVoice Letícia (se disponível), com eSpeak NG como alternativa.
O Ollama continua
a interpretar as perguntas e propor ações, sujeito aos contratos e à política.
Não há aplicação ou servidor web na arquitetura do produto.

O projeto busca preservar:

* privacidade;
* controle operacional;
* segurança;
* auditabilidade;
* independência de serviços externos;
* funcionamento local sempre que tecnicamente possível;
* modularidade;
* portabilidade;
* substituibilidade de componentes;
* testabilidade;
* evolução incremental;
* comportamento previsível;
* compatibilidade controlada.

O Nexus Core não é projetado como um LLM com acesso irrestrito ao computador.

A arquitetura estabelece fronteiras explícitas entre:

```text
INTELIGÊNCIA
     │
     ▼
DECISÃO
     │
     ▼
AUTORIZAÇÃO
     │
     ▼
EXECUÇÃO
```

Um modelo pode interpretar informações e propor uma ação.

Isso não significa que o modelo possua autoridade para executá-la.

---

# Objetivo de longo prazo

O Nexus Core é projetado para evoluir para um assistente capaz de oferecer, de forma integrada:

* conversação por texto;
* conversação por voz;
* operação offline e online;
* modelos de IA locais;
* roteamento entre modelos;
* memória persistente;
* Knowledge Base;
* leitura de arquivos;
* análise de documentos;
* visão computacional;
* interpretação de imagens;
* interpretação de tela;
* pesquisa web;
* desenvolvimento de software assistido;
* automação controlada do desktop;
* geração de documentos;
* geração multimídia;
* integração com dispositivos externos;
* integração com Arduino;
* integração com ESP32;
* arquitetura distribuída entre computadores e dispositivos;
* interface gráfica multimodal.

Essas capacidades não são consideradas implementadas apenas por existirem no roadmap.

Cada release deve adicionar uma responsabilidade pequena, explícita, testável e arquiteturalmente revisável.

---

# Princípios de engenharia

O desenvolvimento do Nexus Core segue princípios que devem continuar válidos durante toda a evolução do projeto.

* **Local First**
* **Security First**
* **Privacy First**
* **Open Source**
* **Free Core**
* **Least Privilege**
* **Defense in Depth**
* **Fail-safe Defaults**
* **Modularidade**
* **Testabilidade**
* **Observabilidade**
* **Auditabilidade**
* **Determinismo quando aplicável**
* **Contratos explícitos**
* **Separação de responsabilidades**
* **Isolamento de falhas**
* **Compatibilidade controlada**
* **Regressão automatizada**
* **Configuração explícita**
* **Scope Control**
* **Evolução incremental**
* **Portabilidade**
* **Substituibilidade de componentes**

Segurança não é tratada como funcionalidade adicionada posteriormente.

Ela faz parte da fundação arquitetural.

---

# Open Source, gratuito e sem quotas comerciais artificiais

O Nexus Core é concebido com a intenção de ser totalmente open source.

O core não deve depender estruturalmente de:

* assinatura obrigatória;
* créditos;
* saldo comercial de tokens;
* billing obrigatório;
* API proprietária obrigatória;
* conta externa obrigatória;
* vendor lock-in;
* quota comercial artificial.

O produto também não deve introduzir limites comerciais como:

```text
N perguntas por dia
N mensagens por mês
N imagens por usuário
saldo de créditos
tokens comerciais
limite por assinatura
```

Limites técnicos continuam existindo.

Exemplos:

* RAM disponível;
* armazenamento;
* capacidade de CPU;
* tamanho da context window;
* tempo de inferência;
* tamanho de arquivo;
* limites de segurança;
* recursos disponíveis no dispositivo.

Esses limites devem ser tratados tecnicamente através de mecanismos como:

* chunking;
* filas;
* paginação;
* indexação;
* compressão de contexto;
* memória persistente;
* cache local;
* gestão de armazenamento;
* processamento incremental.

O objetivo é:

> **nenhuma quota comercial artificial imposta pelo Nexus Core.**

---

# Critérios para tecnologias externas

Uma tecnologia candidata ao Nexus deve ser avaliada considerando:

* disponibilidade do código-fonte;
* licença;
* possibilidade de uso gratuito;
* execução local quando aplicável;
* suporte a Linux;
* ausência de assinatura obrigatória;
* ausência de API obrigatória;
* ausência de lock-in estrutural;
* comunidade ativa;
* manutenção ativa;
* auditabilidade;
* automatização;
* possibilidade de substituição.

Model weights devem ser avaliados separadamente.

Um modelo disponível gratuitamente não é automaticamente open source.

A licença dos pesos e o model card devem ser auditados antes de distribuição pública ou integração definitiva.

---

# Estado atual

**Versão do código na `main`: `v0.9.12`. A última release estável publicada é v0.7.2; a homologação física e as tags posteriores continuam pendentes.** As subseções sobre
`v0.3.0` e `v0.3.1` abaixo preservam decisões e baselines
**históricos**; não representam, isoladamente, as capacidades ou
dependências atuais do código `v0.9.12` na `main`. Para as funcionalidades disponíveis,
consulte a seção de validação acima e as entregas `v0.3.2`–`v0.3.8`.

A linha `v0.3.1` inclui a abstração de modelos, a identidade visual desktop
(`v0.3.1.1`), a fundação PostgreSQL (`v0.3.1.2`) e correções de configuração
(`v0.3.1.3`). A release `v0.3.2` introduz a mediação explícita de caminhos do
host antes de executar ferramentas. Cada tag preserva o snapshot da sua versão.

O PostgreSQL local é o único provider de banco configurado para produção.
A aplicação exige `NEXUS_DATABASE_PASSWORD` no processo de composição,
conecta no `initialize()`, cria `system_events` e fecha a conexão no
`shutdown()`. A tabela `system_events` não representa a memória do assistente; as memórias
explícitas da v0.4.0 usam `nexus_memories` e `nexus_memory_audit`.

A `v0.3.1` evolui a Local Model Layer introduzida na `v0.3.0`.

A principal mudança é a separação entre:

```text
contrato genérico de modelo

e

implementação concreta Ollama
```

O fluxo principal passa a ser:

```text
NexusApplication
        │
        ▼
ModelRouter
        │
        ▼
ModelProvider
        │
        ▼
OllamaProvider
        │
        ▼
OllamaTransport
        │
        ▼
Ollama
        │
        ▼
Local Model
```

A `v0.3.1` registra apenas:

```text
provider_id = "ollama"
```

na composição de produção.

A abstração permite evolução futura sem introduzir nesta release:

* provider online;
* API paga;
* credenciais;
* fallback;
* balanceamento;
* heurísticas;
* seleção por IA;
* descoberta dinâmica.

---

# Entregas da v0.3.1

A `v0.3.1 — Provider Abstraction & Model Routing` introduz:

* `ModelError`;
* `ModelValidationError`;
* `ModelProtocolError`;
* `ModelProviderError`;
* `ModelProviderUnavailableError`;
* `ModelProviderTimeoutError`;
* `ModelRequest`;
* `ModelResponse`;
* `ModelProvider`;
* `OllamaProvider`;
* `ModelRouter`;
* `ModelRoutingError`;
* erros específicos de routing;
* `build_model_router()`;
* composição provider-agnostic;
* normalização de erros de provider;
* runtime validation no boundary do router;
* provider padrão explícito;
* seleção explícita por `provider_id`;
* `model_layer` como API genérica de health;
* label genérico `Model Layer`;
* compatibilidade controlada com a API `LocalModel*` da `v0.3.0`;
* preservação da composição lazy;
* preservação do comportamento local-first;
* preservação da independência entre Model Layer e conectividade externa;
* preservação da separação entre Model Layer e Tool System;
* 493 testes automatizados passando.

---

# O que a v0.3.1 não implementa

A release deliberadamente **não** implementa:

* providers cloud;
* OpenAI provider;
* Anthropic provider;
* Gemini provider;
* APIs pagas;
* API keys;
* credenciais;
* fallback automático;
* retry inteligente;
* model discovery;
* provider discovery;
* provider availability probes;
* seleção baseada em custo;
* seleção baseada em latência;
* seleção aleatória;
* load balancing;
* model registry dinâmico;
* streaming;
* vision models;
* audio models;
* Agent;
* Planner;
* tool calling pelo modelo;
* memória persistente;
* Knowledge Base;
* self-update;
* dependency repair;
* automatic environment bootstrap.

Essas capacidades devem ser introduzidas por releases próprias.

---

# Baseline atual

```text
Release Target:       v0.3.9
Capability:           Continuous Local Voice Conversation
Tests:                veja a seção Testes abaixo
Primary Platform:     Linux
Runtime Baseline:     Python 3.12
Database:             PostgreSQL (loopback)
Sandbox:              Docker
Local Model Runtime:  Ollama
Reference Model:      qwen3:1.7b
Model Provider:       OllamaProvider
Model Router:         ModelRouter
Development Status:   ACTIVE
```

O baseline funcional é:

> **Linux systems with constrained compute resources; no dependency on dedicated GPU.**

GPU pode melhorar desempenho, mas não é requisito estrutural da arquitetura atual.

---

# Arquitetura atual

```text
NEXUS CORE
│
├── Configuration Boundary
│   │
│   ├── Environment
│   ├── load_settings()
│   │   ├── parsing
│   │   ├── normalization
│   │   ├── validation
│   │   └── controlled overrides
│   │
│   ├── Local HTTP Origin Policy
│   │   └── loopback-only validation
│   │
│   └── Settings(frozen=True)
│
├── NexusApplication
│   │
│   ├── Logger
│   ├── Database
│   ├── EventBus
│   ├── ConnectivityManager
│   ├── ConnectivityRuntimeEvaluator
│   ├── ConnectivityMonitor
│   ├── RuntimeStateController
│   ├── HealthStatus
│   ├── ModelRouter
│   ├── SecurityGate
│   ├── ToolRegistry
│   └── ToolExecutor
│
├── Model Layer
│   │
│   ├── ModelRequest
│   ├── ModelResponse
│   ├── ModelProvider
│   ├── ModelRouter
│   ├── OllamaProvider
│   ├── OllamaTransport
│   ├── build_model_router()
│   │
│   └── Compatibility Layer
│       ├── LocalModelRequest
│       ├── LocalModelResponse
│       ├── LocalModelValidationError
│       ├── LocalModelProtocolError
│       ├── LocalModelClient
│       └── build_local_model_client()
│
├── Security Layer
│   │
│   ├── SecurityGate
│   ├── SecurityPolicy
│   ├── PathSecurity
│   ├── ToolPermissionPolicy
│   ├── AuditLogger
│   └── RiskLevel
│
└── Tool System
    │
    ├── NexusTool
    ├── ToolResult
    ├── ToolRegistry
    ├── ToolExecutor
    ├── ListDirectoryTool
    ├── ReadFileTool
    ├── SystemInfoTool
    └── TerminalSandboxTool
        └── Docker
```

---

# Model Layer

A Model Layer representa a fronteira entre o Nexus Core e sistemas de inferência.

Na `v0.3.1`, os contratos principais são provider-agnostic.

---

## `ModelRequest`

`ModelRequest` é um dataclass imutável.

Campos:

```text
prompt
system_prompt
temperature
context_length
think
```

Defaults:

```text
system_prompt = None
temperature = 0.0
context_length = 2048
think = False
```

### `prompt`

Deve ser uma `str` não vazia.

Strings compostas apenas por whitespace são rejeitadas.

### `system_prompt`

Pode ser `None` ou `str` não vazia.

### `temperature`

Deve ser um número finito maior ou igual a zero.

`bool` não é tratado como número válido.

### `context_length`

Deve ser:

```text
int >= 1
```

### `think`

Deve ser:

```text
bool
```

---

# `ModelResponse`

Campos:

```text
content
model
done
prompt_tokens
output_tokens
```

Regras principais:

```text
content        -> str não vazia
model          -> str não vazia
done           -> bool
prompt_tokens  -> int >= 0
output_tokens  -> int >= 0
```

Para a integração não-streaming atual:

```text
done != True
```

representa protocolo incompleto.

---

# `ModelProvider`

`ModelProvider` é um `typing.Protocol` estrutural e `runtime_checkable`.

Contrato conceitual:

```python
@property
def provider_id(self) -> str:
    ...

def generate(
    self,
    request: ModelRequest,
) -> ModelResponse:
    ...
```

A abstração define o que o Nexus espera de um provider.

Ela não determina:

* transporte;
* protocolo externo;
* modelo;
* hardware;
* mecanismo de inferência.

---

# `ModelRouter`

`ModelRouter` é responsável por resolver providers de maneira determinística.

Responsabilidades:

* registrar providers;
* validar contrato estrutural;
* rejeitar provider inválido;
* rejeitar IDs duplicados;
* validar o provider padrão;
* resolver provider explicitamente;
* utilizar provider default;
* validar `ModelRequest`;
* validar `ModelResponse`.

```text
ModelRequest
     │
     ▼
ModelRouter
     │
     ├── provider_id explícito
     │
     └── default_provider_id
             │
             ▼
       ModelProvider
```

---

## Política do router

O router atual não realiza:

```text
fallback
retry policy
provider discovery
model discovery
availability probing
load balancing
cost routing
latency routing
random selection
AI-based selection
```

Essa simplicidade é intencional.

O routing deve permanecer previsível e auditável.

---

# `OllamaProvider`

`OllamaProvider` é a implementação concreta utilizada na `v0.3.1`.

Identificador:

```text
ollama
```

Responsabilidades:

```text
ModelRequest
     │
     ▼
Ollama payload
     │
     ▼
OllamaTransport
     │
     ▼
raw Ollama response
     │
     ▼
protocol validation
     │
     ▼
ModelResponse
```

O provider conhece:

* semântica da API Ollama;
* mensagens;
* `num_ctx`;
* `temperature`;
* `think`;
* estrutura da resposta;
* conclusão não-streaming;
* mapeamento de erros.

O provider não implementa HTTP diretamente.

---

# `OllamaTransport`

`OllamaTransport` é responsável pela comunicação HTTP concreta.

Endpoint:

```text
POST /api/chat
```

Responsabilidades:

* requisição HTTP;
* JSON encode;
* JSON decode;
* timeout;
* erros de conexão;
* erros HTTP;
* JSON inválido.

A fronteira permanece:

```text
HTTP / urllib
     │
     ▼
OllamaTransport
```

e não:

```text
ModelRouter → HTTP

ModelProvider → HTTP

NexusApplication → HTTP Ollama
```

---

# Taxonomia de erros da Model Layer

```text
ModelError
│
├── ModelValidationError
│
├── ModelProtocolError
│
├── ModelProviderError
│   ├── ModelProviderUnavailableError
│   └── ModelProviderTimeoutError
│
└── ModelRoutingError
    ├── InvalidModelProviderError
    ├── InvalidModelProviderIdError
    ├── UnknownModelProviderError
    └── DuplicateModelProviderError
```

`ModelValidationError` preserva compatibilidade com `ValueError`.

Erros de protocolo, provider e routing preservam semântica compatível com `RuntimeError` quando definida pelo contrato.

---

# Normalização de erros Ollama

```text
OllamaUnavailableError
        │
        ▼
ModelProviderUnavailableError
```

```text
OllamaTimeoutError
        │
        ▼
ModelProviderTimeoutError
```

```text
OllamaHTTPError
        │
        ▼
ModelProviderError
```

```text
OllamaInvalidJSONError
        │
        ▼
ModelProtocolError
```

A causa original é preservada por exception chaining.

---

# Compatibilidade com v0.3.0

A `v0.3.1` preserva:

```text
LocalModelRequest
LocalModelResponse
LocalModelValidationError
LocalModelProtocolError
LocalModelClient
build_local_model_client()
```

Aliases:

```text
LocalModelRequest is ModelRequest

LocalModelResponse is ModelResponse

LocalModelValidationError is ModelValidationError

LocalModelProtocolError is ModelProtocolError
```

---

## `LocalModelClient`

`LocalModelClient` permanece como facade de compatibilidade.

Novo código deve preferir:

```text
ModelRouter
ModelProvider
ModelRequest
ModelResponse
```

O facade delega a semântica Ollama ao:

```text
OllamaProvider
```

e preserva os atributos históricos:

```text
model
transport
timeout
```

---

## Compatibilidade de erros do client legado

Na `v0.3.0`, erros originados no transporte podiam escapar diretamente pelo `LocalModelClient`.

A `v0.3.1` preserva esse comportamento no facade legado.

```text
NOVO CAMINHO

ModelRouter
   → OllamaProvider
   → erros Model*
```

```text
CAMINHO LEGADO

LocalModelClient
   → OllamaProvider
   → recupera OllamaTransportError original
   → preserva superfície v0.3.0
```

---

# Factory da Model Layer

Factory principal:

```python
build_model_router(settings)
```

Composição:

```text
OllamaTransport
      │
      ▼
OllamaProvider
      │
      ▼
ModelRouter
```

Produção:

```text
providers = [OllamaProvider]
default_provider_id = "ollama"
```

A criação da composição não realiza inferência.

---

# Composição lazy

```text
NexusApplication()
       │
       ├── _model_router = None
       │
       └── nenhum contato com Ollama
```

No primeiro acesso:

```text
app.model_router
       │
       ▼
build_model_router(settings)
       │
       ▼
ModelRouter
```

O backend só é utilizado quando uma geração é solicitada.

---

# Compatibilidade `local_model_client` no Application

`NexusApplication` mantém:

```python
app.local_model_client
```

como propriedade de compatibilidade.

Na `v0.3.1`, ela resolve o provider Ollama através do router.

Não existe uma segunda composição paralela de Model Layer.

---

# Modelo técnico de referência

```text
qwen3:1.7b
```

É o baseline técnico da camada local atual.

A licença dos pesos deve ser auditada separadamente da futura licença do Nexus Core.

---

# Backend local

```text
Ollama
```

O Nexus Core atualmente:

* não instala Ollama;
* não inicia o daemon;
* não encerra o daemon;
* não instala modelos automaticamente;
* não executa model discovery;
* não carrega modelo no startup;
* não executa inferência no startup;
* não executa probe automático de provider;
* não assume ownership do lifecycle do serviço.

---

# Endpoint local

Default:

```text
http://127.0.0.1:11434
```

A configuração permite somente origem HTTP loopback.

São rejeitados:

* HTTPS;
* hosts externos;
* hosts LAN;
* credenciais;
* custom paths;
* query;
* fragment;
* porta inválida.

---

# Health da Model Layer

API principal:

```python
health.model_layer
```

O campo histórico:

```python
health.local_model_layer
```

é preservado para compatibilidade sobre o mesmo estado.

---

## Semântica

```text
Model Layer ✓ READY
```

significa readiness estrutural da camada de software.

Não significa:

* Ollama liveness;
* modelo instalado;
* modelo carregado;
* inferência bem-sucedida;
* provider saudável.

---

# Painel de status

O label atual é:

```text
Model Layer
```

Exemplo conceitual:

```text
╔══════════════════════════════════════════════╗
║                  N E X U S                   ║
║                    v0.3.1                    ║
╠══════════════════════════════════════════════╣
║ Core              ✓ ONLINE                  ║
║ Configuration     ✓ READY                   ║
║ Database          ✓ READY                   ║
║ Logger            ✓ READY                   ║
║ EventBus          ✓ READY                   ║
║ SecurityGate      ✓ READY                   ║
║ ToolRegistry      ✓ READY                   ║
║ Terminal Sandbox  ✓ READY                   ║
║ Model Layer       ✓ READY                   ║
╠══════════════════════════════════════════════╣
║ Health Monitor    ✓ READY                   ║
╠══════════════════════════════════════════════╣
║ Node              ...                       ║
║ Network           ...                       ║
║ Mode              ...                       ║
╚══════════════════════════════════════════════╝
```

---

# Configuração

Configuração principal:

```python
Settings(frozen=True)
```

Defaults relevantes:

```text
node_name                              NEXUS-NODE-01
offline_mode                           True
connectivity_monitor_interval          30.0
connectivity_confirmation_threshold    2
local_model_name                       qwen3:1.7b
local_model_base_url                   http://127.0.0.1:11434
local_model_timeout                    120.0
```

---

# Variáveis de ambiente

A configuração vigente de `nexus/config/settings.py` reconhece:

| Grupo | Variáveis |
|---|---|
| Núcleo | `NEXUS_NODE_NAME`, `NEXUS_OFFLINE_MODE` |
| Conectividade | `NEXUS_CONNECTIVITY_MONITOR_INTERVAL`, `NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD` |
| PostgreSQL | `NEXUS_DATABASE_PROVIDER`, `NEXUS_DATABASE_HOST`, `NEXUS_DATABASE_PORT`, `NEXUS_DATABASE_NAME`, `NEXUS_DATABASE_USER`, `NEXUS_DATABASE_PASSWORD`, `NEXUS_DATABASE_CONNECT_TIMEOUT` |
| Ollama local | `NEXUS_LOCAL_MODEL_NAME`, `NEXUS_LOCAL_MODEL_BASE_URL`, `NEXUS_LOCAL_MODEL_TIMEOUT` |
| Voz | `NEXUS_VOSK_MODEL_PATH` |
| Diretórios padrão XDG | `XDG_DATA_HOME`, `XDG_STATE_HOME` |

A senha `NEXUS_DATABASE_PASSWORD` é obrigatória para inicializar a
aplicação. `NEXUS_DATABASE_PROVIDER` aceita somente `postgresql` e
o host do banco e a origem HTTP do Ollama são restritos a loopback.
O modelo de voz deve estar descompactado em um diretório local; o extra
`.[voice]` instala a biblioteca Python, **não** baixa seus pesos.

---

# Configurações deliberadamente ausentes na v0.3.1

Não existe:

```text
NEXUS_MODEL_PROVIDER
NEXUS_PROVIDER_FALLBACK
NEXUS_OPENAI_API_KEY
NEXUS_ANTHROPIC_API_KEY
NEXUS_GEMINI_API_KEY
```

Existe apenas um provider de produção:

```text
ollama
```

---

# Runtime e conectividade

Fluxo:

```text
ConnectivityManager
       │
       ▼
network_online
       │
       ▼
ConnectivityRuntimeEvaluator
       │
       ▼
ONLINE / OFFLINE / DEGRADED
       │
       ▼
RuntimeStateController
```

Estados:

```text
ONLINE
OFFLINE
DEGRADED
```

---

# Semântica de DEGRADED

Com threshold default `2`:

```text
ONLINE
   │
   │ primeira observação OFFLINE
   ▼
DEGRADED
   │
   │ segunda observação OFFLINE
   ▼
OFFLINE
```

e:

```text
OFFLINE
   │
   │ primeira observação ONLINE
   ▼
DEGRADED
   │
   │ segunda observação ONLINE
   ▼
ONLINE
```

`DEGRADED` não representa automaticamente falha da Model Layer.

---

# Event Architecture

O Nexus possui:

```text
NexusEvent
EventBus
EventType
```

O EventBus suporta:

* subscribe;
* unsubscribe;
* publish;
* clear;
* contagem de handlers;
* sincronização interna.

O catálogo contém tipos para capacidades atuais e futuras.

A existência de um tipo de evento não implica implementação da funcionalidade correspondente.

---

# Database

Runtime atual:

```text
PostgreSQL local (Psycopg 3)
```

Tabela estrutural:

```text
system_events
```

Campos:

```text
id
event_type
message
created_at
```

O database atual não representa a futura Persistent Memory.

O provider é construído sem I/O; a conexão e a criação da tabela ocorrem
durante `initialize()`. Um PostgreSQL acessível no loopback, um usuário e
um banco já criados são pré-requisitos para executar `nexus.main`.

Configuração por ambiente:

| Variável | Padrão | Regra |
| --- | --- | --- |
| `NEXUS_DATABASE_PROVIDER` | `postgresql` | Único provider suportado |
| `NEXUS_DATABASE_HOST` | `127.0.0.1` | Somente `127.0.0.1`, `localhost` ou `::1` |
| `NEXUS_DATABASE_PORT` | `5432` | Porta de 1 a 65535 |
| `NEXUS_DATABASE_NAME` | `nexus` | Nome não vazio |
| `NEXUS_DATABASE_USER` | `nexus` | Usuário não vazio |
| `NEXUS_DATABASE_PASSWORD` | sem valor | Obrigatória ao compor a aplicação; não é registrada em logs |
| `NEXUS_DATABASE_CONNECT_TIMEOUT` | `5.0` | Segundos, número finito maior que zero |

Guarde a senha fora do repositório e forneça-a ao processo antes da execução.

---

# Logging

Logging principal:

* console;
* arquivo;
* biblioteca padrão;
* formato estruturado.

O security audit log é separado.

---

# Security Architecture

Princípio:

```text
Modelo propõe.

SecurityGate autoriza.

ToolExecutor executa.
```

Arquitetura planejada:

```text
Model Layer
     │
     ▼
Agent / Planner
     │
     ▼
ToolRegistry
     │
     ▼
ToolExecutor
     │
     ▼
SecurityGate
     │
     ▼
Tool
```

---

# SecurityGate

Uma `SecurityRequest` possui:

```text
action
description
risk_level
data
tool_name
resources
path (compatibilidade para chamadas diretas antigas)
```

Avaliação:

1. tool registration;
2. tool permission;
3. validação de cada recurso declarado pela ferramenta;
4. risk policy;
5. audit.

Decisões:

```text
ALLOW
CONFIRM
DENY
```

Cada ferramenta interna declara `sensitive_resources(**kwargs)`: caminhos
de arquivo, diretório e workspace são avaliados antes de `execute()`.
Na `v0.3.4`, o contrato de cada ferramenta também vincula cada recurso à
entrada que o origina; recursos omitidos ou divergentes bloqueiam a chamada.
Declarações ausentes ou inválidas são negadas e auditadas. A decisão
`CONFIRM` exige uma resposta humana explícita antes de executar. Uma recusa,
ausência de terminal ou falha na confirmação bloqueia a chamada; a política
e os recursos são revalidados após a resposta. A decisão e o resultado da
execução ficam no log de auditoria. O código de ferramentas internas é confiável;
uma ferramenta externa que declare falsamente seus recursos exige revisão
antes de ser registrada.

---

# Path Security

A política protege diretórios críticos como:

```text
/boot
/etc
/bin
/sbin
/usr
/var
/root
/sys
/proc
/dev
/run
/lib
/lib64
/opt
/srv
/snap
```

e áreas sensíveis do usuário:

```text
~/.ssh
~/.gnupg
~/.aws
~/.docker
~/.kube
~/.config
~/.local/share/keyrings
```

---

# Audit Log

Registra:

```text
timestamp
tool_name
action
risk_level
decision
reason
path
outcome
```

Outcomes de execução:

```text
SUCCESS
ERROR
EXCEPTION
```

---

# Tool Architecture

```text
NexusTool
    │
    ├── name
    ├── description
    ├── risk_level
    ├── contract: entradas, recursos, permissão e saídas
    └── execute()
```

O `ToolRegistry` exige um `ToolContract` coerente com o nome, a descrição e
o risco da ferramenta. `registry.contracts()` expõe os contratos em uma
estrutura JSON compatível com integrações futuras. `ToolExecutor` valida os
argumentos antes de declarar recursos e consultar o `SecurityGate`; campos
extras, valores de tipo errado e recursos divergentes são negados e auditados.
Depois de `execute()`, o retorno é conferido contra as saídas declaradas.
`ToolResult.as_dict()` produz `success`, `tool_name`, `data` e um erro com
`code` e `message` quando a chamada falha. Nenhum modelo executa ferramentas
diretamente nesta versão.

Ferramentas implementadas:

```text
ListDirectoryTool
ReadFileTool
SystemInfoTool
TerminalSandboxTool
```

---

# Terminal Sandbox

O `TerminalSandboxTool` executa comandos em Docker.

Configuração atual inclui:

```text
image: ubuntu:24.04
network: none
root filesystem: read-only
/tmp: tmpfs
memory: 256 MiB
CPU: 0.5
PIDs: 64
no-new-privileges
capabilities: dropped
user: 1000:1000
timeout: 30 seconds
output limit: 64 KiB
```

Workspace opcional é montado:

```text
/workspace
```

como read-only.

---

# Mediação de recursos da v0.3.2

Fluxo implementado para as ferramentas internas:

```text
Tool
   │
   ├── declara caminhos do host usados nesta chamada
   ▼
ToolExecutor
   │
   ▼
SecurityGate
   │
   ▼
PathSecurity / policies
```

`ListDirectoryTool` declara inclusive o default `.`;
`ReadFileTool` declara o arquivo; `TerminalSandboxTool` declara o
`workspace` quando fornecido; `SystemInfoTool` declara explicitamente
nenhum caminho. Um symlink que resolve para fora da área permitida é negado.
As chamadas devem entrar por `ToolExecutor`; invocar diretamente
`tool.execute()` é uso interno fora da fronteira de autorização.

---

# Prompt Injection

Conteúdo de:

* web;
* PDFs;
* documentos;
* imagens;
* arquivos;
* páginas;
* mensagens externas;

deve ser considerado:

```text
UNTRUSTED DATA
```

Ação proposta por conteúdo externo não equivale a autorização.

---

# Dependências

## Runtime Python

A versão atual exige **Python >= 3.12** e a dependência de banco
`psycopg[binary]==3.3.6`, declarada tanto em `pyproject.toml`
quanto em `requirements/base.txt`. Portanto, a observação histórica
de que o runtime não possui dependências Python externas **não se aplica
à v0.3.8**. O aplicativo utiliza PostgreSQL local.

## Desenvolvimento e voz

O extra `.[dev]` instala `pytest==9.1.1`; o extra opcional
`.[voice]` instala `vosk>=0.3.45,<0.4`. O arquivo
`requirements/dev.txt` referencia `requirements/base.txt` e fixa
o pytest.

## Dependências externas por capacidade

- **PostgreSQL local:** obrigatório para a inicialização; preparar banco,
  usuário e senha antes de abrir a aplicação.
- **Ollama e modelo `qwen3:1.7b`:** inferência local, instalados à parte.
- **Tk / sessão gráfica Linux:** janela desktop; em Debian/Ubuntu,
  instalar `python3-tk`.
- **eSpeak NG, RHVoice Letícia, PipeWire/ALSA:** vozes locais e captura pelo
  dispositivo padrão do PipeWire (`pw-record`) ou ALSA (`arecord`), com Vosk.
- **Piper e voz `pt_BR-faber-medium`:** síntese masculina neural local
  opcional, oferecida pelo instalador após as dependências principais.
- **Docker:** execução opcional de comandos isolados, com aprovação
  humana, sem rede e com limites de recursos.
- **Git e pytest:** ferramentas de desenvolvimento e validação.

---

# Instalação

Baseline:

```text
Linux
Python 3.12
Git
PostgreSQL local
```

Desenvolvimento:

```text
pytest
```

Inferência:

```text
Ollama
```

Sandbox:

```text
Docker
```

GPU dedicada não é requisito arquitetural.

---

# Ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

---

# Ollama

Modelo baseline:

```bash
ollama pull qwen3:1.7b
```

Comandos úteis:

```bash
ollama list
ollama ps
ollama run qwen3:1.7b
```

---

# Executando o Nexus

`NEXUS_DATABASE_PASSWORD` deve estar definido e o PostgreSQL local deve
aceitar a conexão com o banco e o usuário configurados. A janela precisa de
uma sessão gráfica Linux e do módulo Tk do Python (em Debian/Ubuntu, o pacote
do sistema `python3-tk`). Para conversar, o Ollama local e o modelo configurado
também precisam estar disponíveis.

```bash
nexus-core
```

O entrypoint `python -m nexus.main` também abre a janela a partir da raiz
do projeto. `nexus-core --desktop` é equivalente. No ambiente sem interface
gráfica, `nexus-core --status` mostra o estado do núcleo no terminal.

Na janela, digite a pergunta e use **Enviar** ou **Ctrl+Enter**. O modelo pode
responder em linguagem natural ou propor uma ferramenta. A composição atual
registra `system_info`, `list_directory`, `read_file`, `file_metadata`,
`terminal_sandbox`, `desktop_window_info`, `desktop_type_text` e
`desktop_navigate`.
Leitura de arquivos passa pela política de caminhos permitidos. Cada comando
do sandbox Docker exige confirmação individual com operação e recursos
visíveis; fechar a janela recusa confirmações pendentes. A conversa mantém
até seis turnos recentes na memória do processo, sem persistir mensagens.
Cada turno faz no máximo uma chamada de ferramenta, sem loop autônomo.

## Voz local na janela

O instalador guiado Ubuntu inclui os utilitários de áudio, o extra Python de
voz e o modelo Vosk português após confirmação do download. Oferece ainda
Piper e o modelo neural masculino em download separado, além da voz feminina
RHVoice nos pacotes Ubuntu `multiverse`. Para quem usa
instalação manual ou deseja reparar um componente isolado:

```bash
# Debian/Ubuntu
sudo apt install espeak-ng alsa-utils python3-tk
python -m pip install -e '.[voice]'
```

Instale um modelo Vosk em português no computador. O modelo leve de referência
é `vosk-model-small-pt-0.3` (31 MB, Apache 2.0), listado na
[página oficial dos modelos Vosk](https://alphacephei.com/vosk/models).
Descompacte-o em
`~/.local/share/nexus-core/voice/vosk-model-small-pt-0.3` ou indique outro
diretório absoluto já descompactado:

```bash
mkdir -p "$HOME/.local/share/nexus-core/voice" "$HOME/Downloads"
curl -fL --retry 3 -o "$HOME/Downloads/vosk-model-small-pt-0.3.zip" \
  "https://alphacephei.com/vosk/models/vosk-model-small-pt-0.3.zip"
unzip -q "$HOME/Downloads/vosk-model-small-pt-0.3.zip" \
  -d "$HOME/.local/share/nexus-core/voice"
~/.local/bin/nexus-core --voice-check | python3 -m json.tool
```

Se o modelo já estiver em outra pasta, use o caminho da pasta que contém os
arquivos do modelo e inicie o programa no mesmo terminal:

```bash
export NEXUS_VOSK_MODEL_PATH="$HOME/modelos/vosk-model-small-pt-0.3"
~/.local/bin/nexus-core --voice-check | python3 -m json.tool
~/.local/bin/nexus-core --desktop
```

Ao abrir a janela, o assistente começa a escutar automaticamente. O Vosk detecta
o fim de cada fala pela pausa e o texto reconhecido entra na mesma conversa,
passando pelo Agent com Ollama, `ToolExecutor` e `SecurityGate`. A escuta é
suspensa durante o processamento e a leitura da resposta para evitar retorno
da própria voz ao microfone. Após responder, volta a escutar automaticamente.
Use **Pausar escuta** e **Retomar escuta**, `Ctrl+Shift+M`, ou diga
**“pare de escutar”** para pausar; depois de pausado, retome pelo botão ou
pelo atalho. Diga **“desligue o assistente”**
ou use o botão **Desligar assistente** para encerrar a janela. Nenhum desses
comandos de controle é encaminhado ao Ollama. A captura usa segmentos de até
30 segundos, reiniciados automaticamente após silêncio. Não há envio do áudio
a serviços remotos; os dados da captura ficam na memória até a transcrição.
Selecione **Feminina** ou **Masculina** para a saída sintetizada em português
brasileiro, ou diga **“Use voz feminina”** / **“Use voz masculina”** enquanto
a escuta estiver ativa. Desligue **Ler respostas em voz alta** quando quiser
apenas texto; escolher outra voz não reativa a saída falada.
A opção masculina usa Piper quando o modelo está instalado; a feminina usa
RHVoice Letícia quando instalado. Na ausência dos respectivos componentes,
ambas usam eSpeak NG. O texto funciona mesmo sem os
componentes de voz; a interface mostra uma mensagem se faltar o microfone,
o executável de áudio ou o modelo de reconhecimento.

Para executar um comando no sandbox Docker, com aprovação presencial no
terminal e workspace opcional montado somente para leitura:

```bash
nexus-core --sandbox-command 'pwd' --workspace "$PWD"
```

O prompt mostra o comando e os recursos. Somente a resposta literal `sim`
autoriza aquela chamada; sem terminal interativo a operação é negada. O
PostgreSQL local deve estar disponível antes de iniciar a aplicação. Dados
e logs ficam no diretório do usuário conforme `XDG_DATA_HOME` e
`XDG_STATE_HOME` (padrões `~/.local/share/nexus-core` e
`~/.local/state/nexus-core/logs`).

Com Ollama local ativo e o modelo configurado disponível, o primeiro Agent
aceita uma solicitação de cada vez:

```bash
nexus-core --agent-prompt 'Proponha terminal_sandbox com o comando pwd'
```

O modelo devolve uma resposta de texto ou propõe **uma** ferramenta em JSON.
A aplicação valida o contrato e envia a proposta ao `ToolExecutor`, que
aplica a política, registra auditoria e pede confirmação humana quando
necessária. Uma proposta de comando requer confirmação presencial e Docker
operacional. O comando de terminal `--agent-prompt` permanece para uma
solicitação isolada; a janela mantém o contexto curto da conversa. A política
de permissão não é alterada pelo modelo. Se ele estiver indisponível, a
solicitação falha sem executar ferramentas.

---

# Exemplo de ModelRouter

```python
from nexus.config.settings import settings
from nexus.models.contracts import ModelRequest
from nexus.models.model_factory import build_model_router


router = build_model_router(settings)

response = router.generate(
    ModelRequest(
        prompt="Olá, Nexus.",
    )
)

print(response.content)
```

---

# Testes

Comando para uma instalação de desenvolvimento:

```bash
python -m pip install -e '.[dev,voice]'
PYTHONPATH="$PWD" pytest -q
```

**Evidência oficial da v0.3.8:** o workflow
[CI / run 37879650437](https://github.com/ricardogomesbarreto/Nexus-Core/actions/runs/37879650437),
executado em 09/10/2026, registrou:

```text
625 passed, 2 warnings in 5.56s
```

Os dois avisos vieram de `tests/test_tools.py`, em casos do
`terminal_sandbox`, durante a finalização de objetos Tkinter
(`RuntimeError: main thread is not in main loop` capturado pelo
pytest como `PytestUnraisableExceptionWarning`). Eles **não**
representam falhas de teste, mas são uma pendência a investigar.

A CI configura PostgreSQL 16, Docker e `xvfb-run` para testes da
janela. A saída eSpeak NG é exercitada com o executável real; já a
captura por microfone e os fluxos Vosk de escuta contínua usam
substitutos controlados nos testes, não hardware físico. A presença
dos componentes na CI não certifica compatibilidade com todos os
equipamentos Linux.

Em sistemas sem Docker, PostgreSQL de testes ou display gráfico,
alguns testes de integração são pulados conforme os pré-requisitos;
o total local pode divergir do workflow de referência. Para a
integração PostgreSQL real de teste, configurar
`NEXUS_TEST_POSTGRES_PASSWORD` para o banco descartável `nexus_test`.

---

# Estratégia de testes

A suíte prioriza:

* determinismo;
* isolamento;
* fake transports;
* fake providers;
* ausência de inferência real;
* validação de contratos;
* regressão;
* compatibilidade;
* lifecycle;
* concurrency;
* segurança;
* boundaries arquiteturais.

---

# Estrutura do projeto

```text
Nexus-Core/
│
├── README.md
│
├── requirements/
│   ├── base.txt
│   └── dev.txt
│
├── scripts/
│
├── nexus/
│   │
│   ├── brains/
│   ├── config/
│   ├── context/
│   ├── core/
│   ├── database/
│   ├── events/
│   ├── knowledge/
│   ├── memory/
│   │
│   ├── models/
│   │   ├── contracts.py
│   │   ├── local_model.py
│   │   ├── local_model_factory.py
│   │   ├── model_factory.py
│   │   ├── ollama_provider.py
│   │   ├── ollama_transport.py
│   │   ├── provider.py
│   │   └── router.py
│   │
│   ├── monitoring/
│   ├── security/
│   ├── tools/
│   └── main.py
│
└── tests/
```

Diretórios de scaffolding não representam capacidades concluídas.

---

# Histórico de releases

O histórico abaixo documenta a evolução incremental da arquitetura.

Cada release adiciona uma nova responsabilidade sem antecipar artificialmente capacidades das etapas seguintes.

---

## v0.1.0 — Foundation

### Objetivo

Criar a primeira fundação executável do Nexus Core.

### Entregue

* estrutura inicial do projeto;
* package `nexus`;
* organização modular inicial;
* configuração central;
* logging;
* database local;
* persistência local de eventos;
* arquitetura inicial da aplicação;
* diretórios de dados e logs;
* primeira separação entre infraestrutura e futuras capacidades de IA.

### Impacto arquitetural

A release estabeleceu a base sobre a qual os demais subsistemas passaram a ser adicionados.

Antes de agentes, modelos, memória ou automação, o projeto recebeu uma infraestrutura mínima capaz de:

```text
configurar
inicializar
registrar
persistir
encerrar
```

### Limites

Ainda não existiam:

* EventBus formal;
* SecurityGate;
* Tool System;
* runtime connectivity;
* modelos;
* Agent;
* memória.

---

## v0.1.1 — Infrastructure Core

### Objetivo

Consolidar a infraestrutura central criada na fundação.

### Entregue

* evolução do núcleo da aplicação;
* composição mais clara dos componentes de infraestrutura;
* lifecycle centralizado;
* endurecimento de logging e database;
* preparação para módulos desacoplados;
* separação progressiva de responsabilidades.

### Impacto arquitetural

A aplicação passou a ter uma base mais adequada para receber componentes independentes sem transformar o entrypoint em um monólito.

A direção passou a ser:

```text
NexusApplication
      │
      ├── Infrastructure Component A
      ├── Infrastructure Component B
      └── Future Components
```

### Limites

A release continuava focada em infraestrutura.

Ainda não introduzia autorização, tools ou inteligência.

---

## v0.1.2 — Event Architecture

### Objetivo

Criar uma arquitetura interna de comunicação desacoplada por eventos.

### Entregue

* `NexusEvent`;
* `EventBus`;
* catálogo de tipos de evento;
* subscribe;
* unsubscribe;
* publish;
* múltiplos handlers;
* desacoplamento entre produtores e consumidores;
* timestamps de evento;
* preparação para eventos de sistema, segurança, rede, tarefas e futuras capacidades.

### Impacto arquitetural

Componentes passaram a poder se comunicar sem referência direta entre si.

```text
Producer
   │
   ▼
EventBus
   │
   ├── Handler A
   ├── Handler B
   └── Handler C
```

Isso criou uma base importante para lifecycle, conectividade e observabilidade.

### Limites

A presença de eventos como voice, vision ou memory no catálogo não significava implementação dessas capacidades.

---

## v0.1.3 — Security Gate

### Objetivo

Criar a primeira fronteira central de autorização do Nexus Core.

### Entregue

* `SecurityGate`;
* `SecurityRequest`;
* `SecurityResult`;
* decisões explícitas de segurança;
* risk-based evaluation;
* separação entre solicitação e autorização;
* base para políticas de acesso;
* princípio de fail-safe authorization.

### Impacto arquitetural

Foi estabelecida a regra:

```text
operação potencialmente sensível
        │
        ▼
SecurityGate
        │
        ├── ALLOW
        ├── CONFIRM
        └── DENY
```

A partir dessa versão, autoridade operacional deixou de ser tratada como consequência implícita de uma chamada de função.

### Limites

Ainda faltavam:

* arquitetura formal de tools;
* path security;
* permissões específicas por ferramenta;
* audit log completo.

---

## v0.1.4 — Tool Architecture

### Objetivo

Criar uma camada formal para capacidades executáveis.

### Entregue

* `NexusTool`;
* `ToolResult`;
* `ToolRegistry`;
* `ToolExecutor`;
* nomes e descrições de tools;
* níveis de risco;
* registro explícito;
* lookup de ferramentas;
* execução controlada;
* integração inicial com o `SecurityGate`;
* rejeição de tool desconhecida.

### Impacto arquitetural

Foi criada a separação:

```text
Tool Definition
      │
      ▼
ToolRegistry
      │
      ▼
ToolExecutor
      │
      ▼
SecurityGate
      │
      ▼
Execution
```

Essa arquitetura se tornaria posteriormente a base para tool calling controlado.

### Limites

Modelos ainda não participavam da cadeia.

---

## v0.1.5 — Path Security

### Objetivo

Evitar que operações de filesystem fossem autorizadas apenas pelo nome da tool.

### Entregue

* `PathSecurity`;
* resolução explícita de paths;
* delimitação de área autorizada;
* proteção de diretórios críticos do sistema;
* proteção de áreas sensíveis do usuário;
* rejeição de paths fora da região permitida;
* prevenção de acesso direto a caminhos protegidos.

### Impacto arquitetural

A autorização passou a considerar:

```text
ação
tool
risco
path
```

em vez de apenas:

```text
ação
```

Isso reduziu a superfície de acesso acidental ou indevido ao host.

### Limites

A mediação ainda depende do recurso ser corretamente representado no `SecurityRequest`.

Na `v0.3.2`, as ferramentas internas passaram a declarar os recursos
usados em cada chamada, e o executor nega declarações ausentes.

---

## v0.1.6 — Tool Permissions + Audit Log

### Objetivo

Adicionar governança explícita por ferramenta e rastreabilidade.

### Entregue

* `ToolPermissionPolicy`;
* registro individual de tools;
* maximum risk por ferramenta;
* rejeição de tools não registradas;
* `AuditLogger`;
* registros de decisão;
* timestamps UTC;
* razão da decisão;
* tool name;
* action;
* risk level;
* path quando aplicável;
* base para rastreamento de execução.

### Impacto arquitetural

O SecurityGate passou a combinar:

```text
Tool Permission
       +
Path Security
       +
Risk Policy
       +
Audit
```

Essa versão estabeleceu auditabilidade como requisito de arquitetura, e não apenas debugging.

---

## v0.1.7 — Secure File Tools

### Objetivo

Introduzir as primeiras ferramentas reais de filesystem sob a arquitetura de segurança.

### Entregue

* `ListDirectoryTool`;
* `ReadFileTool`;
* integração das file tools ao Tool System;
* leitura de arquivos de texto;
* validação de existência;
* validação de tipo;
* tratamento de permission errors;
* tratamento de filesystem errors;
* limite de tamanho para leitura;
* rejeição de conteúdo não UTF-8;
* mediação de path pelo fluxo de segurança.

### Impacto arquitetural

Pela primeira vez, a cadeia:

```text
ToolRegistry
      │
      ▼
ToolExecutor
      │
      ▼
SecurityGate
      │
      ▼
PathSecurity
      │
      ▼
Filesystem Tool
```

passou a operar sobre recursos reais.

### Limites

As ferramentas eram deliberadamente restritas.

Não existia shell livre ou automação de desktop.

---

## v0.1.8 — Terminal Sandbox

### Objetivo

Adicionar execução de comandos sem conceder shell irrestrito no host.

### Entregue

* `TerminalSandboxTool`;
* execução dentro de Docker;
* isolamento do host;
* ausência de rede no container;
* root filesystem read-only;
* `/tmp` temporário;
* limites de recursos;
* limite de processos;
* timeout;
* captura controlada de stdout/stderr;
* limite de output;
* remoção do container após execução;
* risk level superior às file tools;
* integração com o modelo de autorização.

### Impacto arquitetural

O projeto passou a separar:

```text
comando solicitado

de

execução direta no host
```

A direção passou a ser:

```text
Command
   │
   ▼
SecurityGate
   │
   ▼
TerminalSandboxTool
   │
   ▼
Docker
```

### Limites

O sandbox não representa autorização automática.

A política default continua tratando operações `MEDIUM` como dependentes de confirmação.

---

## v0.1.9 — Health Check & Application Status

### Objetivo

Tornar o estado estrutural da aplicação observável.

### Entregue

* `HealthStatus`;
* readiness estrutural;
* status dos principais componentes;
* painel textual;
* lifecycle de status;
* integração de health com `NexusApplication`;
* shutdown garantido pelo entrypoint;
* visualização operacional do estado do core.

### Impacto arquitetural

O projeto ganhou uma projeção explícita de estado:

```text
Core
Configuration
Database
Logger
EventBus
SecurityGate
ToolRegistry
Terminal Sandbox
Health Monitor
```

Essa camada posteriormente passou a incorporar runtime connectivity e Model Layer.

---

# Série v0.2.x — Runtime e conectividade

A série `v0.2.x` transformou conectividade em um subsistema formal de runtime.

---

## v0.2.0 — Connectivity & Runtime Modes

### Objetivo

Introduzir observação de conectividade externa e modos formais de execução.

### Entregue

* `ConnectivityManager`;
* `ConnectivityStatus`;
* `RuntimeMode`;
* `ONLINE`;
* `OFFLINE`;
* `DEGRADED`;
* `offline_mode`;
* eventos de conectividade;
* determinação inicial do runtime;
* separação inicial entre execução local e disponibilidade externa.

### Impacto arquitetural

Foi criada a distinção:

```text
Nexus running
```

não implica:

```text
Internet available
```

A aplicação passou a possuir semântica explícita de operação online e offline.

### Baseline histórico

```text
87 tests passing
```

---

## v0.2.1 — Runtime State Controller

### Objetivo

Substituir estado de runtime disperso por uma fonte autoritativa.

### Entregue

* `RuntimeStateController`;
* estado centralizado;
* `mode`;
* `reason`;
* `changed_at`;
* transições formais;
* validação de transições;
* integração com a aplicação;
* preservação dos eventos iniciais;
* base para snapshots e concorrência futura.

### Impacto arquitetural

O runtime passou a seguir:

```text
Observation
     │
     ▼
RuntimeStateController
     │
     ▼
Authoritative Runtime State
```

Em vez de múltiplos componentes manterem interpretações independentes do estado.

### Baseline histórico

```text
97 tests passing
```

---

## v0.2.2 — Continuous Connectivity Monitoring

### Objetivo

Transformar conectividade de uma verificação pontual em monitoramento contínuo.

### Entregue

* `ConnectivityMonitor`;
* worker `Nexus-ConnectivityMonitor`;
* polling periódico;
* intervalo configurável;
* snapshots;
* sincronização de health;
* locks;
* stop event;
* shutdown responsivo;
* lifecycle endurecido;
* isolamento de falhas;
* monitor independente do fluxo principal da aplicação.

### Impacto arquitetural

A conectividade passou de:

```text
startup check
```

para:

```text
startup check
      +
continuous observation
```

O monitor passou a alimentar o runtime sem bloquear a aplicação principal.

### Baseline histórico

```text
134 tests passing
```

---

## v0.2.3 — Automatic DEGRADED Runtime Detection

### Objetivo

Evitar mudanças de estado instáveis causadas por uma única observação divergente.

### Entregue

* `ConnectivityRuntimeEvaluator`;
* `ConnectivityRuntimeEvaluation`;
* `DEGRADED` automático;
* confirmação simétrica;
* confirmation threshold;
* threshold default `2`;
* cancelamento de mudança pendente;
* tratamento de oscilação;
* separação de rede e runtime;
* eventos independentes;
* serialização de ciclos;
* invariants de inicialização;
* interpretação determinística da conectividade.

### Impacto arquitetural

Foi estabelecido o modelo:

```text
raw observation
      │
      ▼
runtime interpretation
      │
      ▼
stable state
```

Uma única divergência passa temporariamente por:

```text
DEGRADED
```

antes de alterar o estado estável.

### Exemplo

```text
ONLINE
   │
   │ 1ª observação OFFLINE
   ▼
DEGRADED
   │
   │ 2ª observação OFFLINE
   ▼
OFFLINE
```

### Baseline histórico

```text
151 tests passing
```

---

## v0.2.4 — Environment & Runtime Configuration

### Objetivo

Transformar configuração em um boundary formal, validado e determinístico.

### Entregue

* `ConfigurationError`;
* `load_settings()`;
* leitura controlada de `os.environ`;
* mappings explícitos para testes;
* `Settings(frozen=True)`;
* defaults centralizados;
* allowlist de environment variables;
* parsing booleano estrito;
* parsing numérico;
* normalização;
* validação;
* fail-fast;
* proteção de paths;
* proteção de version;
* proteção de app name;
* testes determinísticos;
* nenhuma dependência Python adicional;
* nenhum `.env` automático;
* nenhum `python-dotenv`;
* nenhum perfil artificial;
* nenhum reload dinâmico.

### Impacto arquitetural

Configuração deixou de ser estado global mutável informal e passou a seguir:

```text
Environment
     │
     ▼
parse
     │
     ▼
normalize
     │
     ▼
validate
     │
     ▼
Settings(frozen=True)
```

### Baseline histórico

```text
184 tests passing
```

---

# Série v0.3.x — Inteligência e Model Layer

A série `v0.3.x` introduz inteligência local sem romper a fronteira entre inteligência e autoridade operacional.

---

## v0.3.0 — Local Model Layer

### Objetivo

Introduzir a primeira integração formal de um modelo de linguagem local ao Nexus Core.

### Entregue

* `LocalModelRequest`;
* `LocalModelResponse`;
* contratos imutáveis;
* validação tipada;
* `LocalModelValidationError`;
* `LocalModelProtocolError`;
* `LocalModelClient`;
* request boundary explícito;
* payload não-streaming;
* system prompt;
* temperature;
* context length;
* `think`;
* model name;
* timeout;
* parsing de resposta;
* validação de resposta final;
* rejeição de `done=False`;
* `OllamaTransport`;
* `OllamaTransportError`;
* `OllamaUnavailableError`;
* `OllamaTimeoutError`;
* `OllamaHTTPError`;
* `OllamaInvalidJSONError`;
* integração com `/api/chat`;
* JSON pela biblioteca padrão;
* endpoint HTTP local;
* política loopback-only;
* bloqueio de hosts externos;
* bloqueio de LAN;
* bloqueio de credentials;
* bloqueio de custom paths;
* bloqueio de query;
* bloqueio de fragments;
* `NEXUS_LOCAL_MODEL_NAME`;
* `NEXUS_LOCAL_MODEL_BASE_URL`;
* `NEXUS_LOCAL_MODEL_TIMEOUT`;
* `build_local_model_client()`;
* composição lazy;
* integração com `NexusApplication`;
* health estrutural;
* label `Local Model Layer`;
* operação compatível com forced offline;
* nenhuma inferência durante startup;
* nenhuma inferência na suíte unitária;
* smoke tests reais separados;
* modelo técnico de referência `qwen3:1.7b`;
* backend técnico de referência Ollama;
* nenhuma autoridade direta sobre tools;
* nenhuma dependência Python externa adicional;
* regressão arquitetural completa.

### Arquitetura da release

```text
LocalModelRequest
        │
        ▼
LocalModelClient
        │
        ▼
OllamaTransport
        │
        ▼
HTTP loopback
        │
        ▼
Ollama
        │
        ▼
Local Model
```

### Princípios consolidados

#### Local First

Inferência através de backend local.

#### Contract First

Entrada e saída possuem contratos formais.

#### Runtime Validation

Type hints não são a única defesa.

#### Fail Explicitly

Falhas são diferenciadas entre:

```text
validation
protocol
transport
```

#### Resource Discipline

Startup não carrega o modelo.

#### Test Determinism

A suíte unitária não depende de LLM real.

#### Separation of Concerns

`LocalModelClient` não implementa HTTP.

`OllamaTransport` não define semântica do contrato de alto nível.

#### Security First

O modelo não recebe acesso às tools.

### Limites deliberados

A `v0.3.0` não introduziu:

* streaming;
* provider abstraction;
* model routing;
* online providers;
* Agent;
* Planner;
* tool calling;
* memory;
* Knowledge Base;
* voice;
* vision;
* desktop automation.

### Baseline histórico

```text
338 tests passing
```

---

## v0.3.1 — Provider Abstraction & Model Routing

### Status

```text
IMPLEMENTATION COMPLETE
RELEASED
```

### Objetivo

Remover o acoplamento conceitual entre a Model Layer e uma implementação concreta de provider sem adicionar cloud providers ou routing heurístico.

### Entregue

#### Contratos genéricos

* `ModelRequest`;
* `ModelResponse`;
* `ModelError`;
* `ModelValidationError`;
* `ModelProtocolError`;
* `ModelProviderError`;
* `ModelProviderUnavailableError`;
* `ModelProviderTimeoutError`.

#### Provider abstraction

* `ModelProvider`;
* `typing.Protocol`;
* `runtime_checkable`;
* `provider_id`;
* contrato estrutural `generate()`.

#### Ollama provider

* `OllamaProvider`;
* conversão `ModelRequest → Ollama payload`;
* conversão `Ollama response → ModelResponse`;
* protocolo não-streaming;
* validação de resposta;
* normalização de transport errors.

#### Model routing

* `ModelRouter`;
* provider registry;
* default provider;
* provider selection explícita;
* validação do provider;
* duplicate provider rejection;
* unknown provider rejection;
* request boundary validation;
* response boundary validation.

#### Routing errors

* `ModelRoutingError`;
* `InvalidModelProviderError`;
* `InvalidModelProviderIdError`;
* `UnknownModelProviderError`;
* `DuplicateModelProviderError`.

Toda a família de routing passa a pertencer à hierarquia:

```text
ModelError
```

#### Factory

* `build_model_router()`;
* composição `OllamaTransport → OllamaProvider → ModelRouter`;
* nenhuma conexão com backend durante construção.

#### NexusApplication

* `_model_router`;
* propriedade lazy `model_router`;
* única composição de provider;
* nenhum backend contact durante construção;
* nenhum backend contact obrigatório durante `initialize()`.

#### Health

API principal:

```text
model_layer
```

Compatibilidade:

```text
local_model_layer
```

ambas representando o mesmo backing state.

#### UI

Label atualizado:

```text
Model Layer
```

#### Compatibilidade v0.3.0

Preservados:

* `LocalModelRequest`;
* `LocalModelResponse`;
* `LocalModelValidationError`;
* `LocalModelProtocolError`;
* `LocalModelClient`;
* `build_local_model_client()`.

#### Compatibilidade de erros

O caminho genérico utiliza erros `Model*`.

O facade legado preserva os transport errors da `v0.3.0`.

```text
NEW

ModelRouter
   → OllamaProvider
   → Model* errors
```

```text
LEGACY

LocalModelClient
   → OllamaProvider
   → original OllamaTransportError
```

#### Arquitetura

```text
NexusApplication
        │
        ▼
ModelRouter
        │
        ▼
ModelProvider
        │
        ▼
OllamaProvider
        │
        ▼
OllamaTransport
        │
        ▼
Ollama
```

### Provider de produção

Somente:

```text
ollama
```

### Não implementado

A release deliberadamente não adiciona:

* online provider;
* cloud API;
* credenciais;
* fallback;
* availability probes;
* provider discovery;
* model discovery;
* load balancing;
* cost routing;
* latency routing;
* AI routing;
* streaming;
* Agent;
* Planner;
* tool calling.

### Segurança

A Model Layer continua sem dependência de:

```text
SecurityGate
ToolRegistry
ToolExecutor
TerminalSandboxTool
filesystem tools
```

Isso preserva:

```text
intelligence != authority
```

### Baseline validado

```text
493 tests passing
493 tests collected
```

---

## v0.3.1.1 — Desktop Visual Identity Foundation

Marca e iconografia desktop nativa Nexus Line em Wine Red (`#722F37`),
manifesto de 18 ícones e testes de integridade dos SVGs e do logotipo.
A identidade era um conjunto de assets; a janela foi introduzida em `v0.3.6`.

## v0.3.1.2 — PostgreSQL Database Provider Foundation

Introduz `DatabaseProvider`, `PostgreSQLProvider`, a factory de composição,
configuração validada via ambiente e Psycopg 3. O serviço conecta durante a
inicialização, mantém `system_events` e fecha no encerramento. Testes
usam providers falsos quando não requerem o servidor PostgreSQL.

## v0.3.1.3 — Release Configuration Corrections

O commit etiquetado como `v0.3.1.3` corrigiu regressões dos testes de
configuração, mas ainda exibia `0.3.1.2` em `Settings.version` e mantinha
o README em `v0.3.1.1`. Esta revisão posterior no `main` alinha a versão
exibida, os testes e a documentação à implementação efetiva. A tag
existente não foi reescrita.

---

## v0.3.2 — Security Resource Mediation

Release concluída: declaração explícita dos caminhos sensíveis
por ferramenta, avaliação de todos pelo `SecurityGate`, mediação de
`TerminalSandboxTool.workspace` e do default de `ListDirectoryTool`,
negação de declarações ausentes ou inválidas, auditoria de todos os
caminhos e testes de escape por symlink. A Model Layer ainda não chama
ferramentas.

---

## v0.3.3 — Explicit Confirmation & Authorization

O `ToolExecutor` trata `CONFIRM` como uma autorização individual: solicita
decisão por um handler separado da Model Layer, registra aprovação ou recusa
e reavalia recursos e política após a resposta. Sem handler, sem terminal
visível, diante de erro ou de qualquer resposta diferente de `sim`, a
execução é negada. `DENY` nunca apresenta pedido de confirmação.

O comando Linux `nexus-core --sandbox-command` expõe o fluxo para o sandbox
Docker. Os logs e dados locais seguem os diretórios XDG do usuário. A CI
verifica Python 3.12, PostgreSQL real e a suíte Docker no Linux.

---

## v0.3.4 — Structured Tool Contracts

Cada ferramenta interna declara um contrato imutável com entradas tipadas,
valores padrão, recursos vinculados às entradas, nível de permissão e saídas.
O registro recusa contratos ausentes ou incoerentes. Antes da autorização, o
executor valida os parâmetros e compara os caminhos declarados com os caminhos
esperados; depois da execução, valida nome, estado e dados do resultado.
Rejeições e retornos inválidos são auditados com códigos de erro estáveis.

Os contratos podem ser inspecionados por `ToolRegistry.contracts()` e
serializados em JSON. A interface de terminal, a confirmação humana e o
PostgreSQL local continuam sendo os componentes de execução desta versão.
O Agent/Planner foi introduzido em `v0.3.5`.

---

## v0.3.5 — Controlled Agent & Tool Calling

O primeiro `AgentPlanner` traduz uma solicitação em resposta de texto ou
proposta de **uma** chamada. O formato JSON é validado estritamente: objetos
com campos extras, chaves duplicadas, respostas incompletas, ferramentas fora
do registro e argumentos inválidos são recusados e auditados. Conteúdo do
modelo nunca autoriza a si mesmo; cada chamada atravessa o contrato da
ferramenta, o `ToolExecutor`, o `SecurityGate` e a confirmação humana quando
a política exige. Erros do modelo não disparam execução. A composição é lazy
e o CLI `--agent-prompt` expõe o fluxo no desktop Linux.

Fluxo implementado:

```text
Model Layer
     │
     ▼
Agent / Planner
     │
     ▼
ToolRegistry
     │
     ▼
ToolExecutor
     │
     ▼
SecurityGate
     │
     ▼
Tool
```

Esta release limita o Agent a uma proposta por solicitação; não há loop
autônomo nem acesso direto do provider às ferramentas. O PostgreSQL local
permanece obrigatório para inicializar a aplicação.

---

## v0.3.6 — Native Desktop Conversation Foundation

A janela nativa Tk no Linux apresenta a conversa, respostas e resultados das
ferramentas. O histórico de seis turnos é efêmero e limitado em tamanho; o
modelo recebe o contexto de forma estruturada. A inferência ocorre em um
worker para manter a janela responsiva, enquanto a autorização aparece na
thread gráfica e cada solicitação ao `ToolExecutor` continua mediada pelo
`SecurityGate`. Ações de risco exigem confirmação individual. O CLI continua
disponível para estado, prompts isolados e comandos no sandbox.

O assistente pode responder perguntas e executar apenas as ferramentas
registradas. Outras ações no computador exigem contratos e políticas próprios
em releases futuras; a janela não concede acesso irrestrito ao sistema.

---

## v0.3.7 — Local Voice Conversation

A janela recebe fala sob demanda pelo microfone por até oito segundos. O
`arecord` captura WAV mono PCM 16 kHz e o Vosk com um modelo local português
transcreve para texto; não há escuta permanente. O texto reconhecido entra na
mesma `ChatSession`, e o Ollama continua como modelo de raciocínio para
respostas e propostas de ferramenta. eSpeak NG lê as respostas com variante
feminina ou masculina selecionada na janela; o usuário pode desligar a leitura.
Os processos de áudio podem ser encerrados ao fechar a janela. Ausência dos
componentes opcionais não impede a conversa por texto.

Uma transcrição não ganha autorização especial: propostas continuam limitadas
a uma chamada por turno e passam pelo contrato, `ToolExecutor`, `SecurityGate`
e confirmação individual quando necessária. A CI valida as duas variantes
reais de síntese, a janela Tk, PostgreSQL e Docker no Linux.

---

# Roadmap

O roadmap é evolutivo. Cada release adiciona uma responsabilidade
pequena, clara e verificável.

## v0.3.8 — Continuous Local Voice Conversation

**Marco concluído e publicado.** A evolução v0.3.9 é tratada na seção seguinte.

A escuta automática inicia na janela desktop e termina por pausa ou encerramento
explícito. A detecção local de fim de fala usa Vosk; a saída usa eSpeak NG com
voz feminina ou masculina. O fluxo suspende a captação enquanto responde,
retoma em seguida e mantém autorização individual para ações no computador.
Sem dependências de voz instaladas, o texto permanece disponível e a janela
exibe o motivo da falha. A CI testa o fluxo de conversa e os controles de pausa.

---

## v0.3.9 — Expanded Desktop Capabilities & Hardening

Versão v0.3.9: adiciona `file_metadata`, endurece a abertura de caminhos
contra troca de symlinks e torna o workspace Docker um snapshot privado e
limitado. A interface Tk exibe a marca local e sincroniza o encerramento dos
workers. A publicação depende da CI e da revisão final.

---

# Confiabilidade, bootstrap e updates

Sequência planejada:

```text
Environment Detection
        │
        ▼
Dependency Doctor
        │
        ▼
Bootstrap / Preflight
        │
        ▼
Update Manager
        │
        ▼
Self-Recovery
```

Estados desejados de diagnóstico:

```text
OK
MISSING
OUTDATED
INCOMPATIBLE
DEGRADED
ERROR
```

Updates não devem executar cegamente:

```text
sudo apt upgrade
root escalation
arbitrary package mutation
```

Fluxo desejado:

```text
Detect
  │
  ▼
Compare Compatibility
  │
  ▼
Plan
  │
  ▼
Update Authorized Component
  │
  ▼
Integrity Check
  │
  ▼
Smoke
  │
  ├── Accept
  └── Rollback / Degraded
```

---

# Memória e conhecimento

## v0.4.0 — Persistent Memory Foundation

**Implementado:** armazenamento explícito no PostgreSQL, listagem e busca
literal, retenção e expiração, exclusão individual e total, auditoria sem
conteúdo e comandos CLI. Sem gravação automática do chat ou injeção
de memórias no prompt do agente nesta fase.

---

## v0.4.1 — Knowledge Base

**Implementado:** ingestão opt-in de documentos TXT/Markdown até 256 KiB,
indexação e pesquisa PostgreSQL GIN, deduplicação SHA-256, identificação
de origem, auditoria sem conteúdo, exclusão em cascata e contexto com memória
**somente por solicitação explícita**. Não há OCR, embeddings ou injeção
automática de conteúdo no prompt do Ollama.

---

# Voz

## v0.5.0 — Voice Foundation

**Implementado:** speech-to-text local Vosk/ALSA e text-to-speech local
eSpeak NG (base v0.3.7/v0.3.8), escuta contínua com pausa, frase de
ativação **opcional** "Nexus" no início da transcrição e
`nexus-core --voice-check` para diagnóstico sem captura.
O filtro não é um mecanismo separado de wake-word detection.
Homologação em hardware físico ainda pendente.

---

# Visão

## v0.6.0 — Vision & Screen Understanding Foundation

**Implementado:** leitura autorizada de imagens, captura sob comando de um
único quadro de câmera ou tela, validação/remoção de metadados via Pillow,
análise multimodal sob demanda no Ollama loopback e diagnóstico local.
Nenhuma captura automática, OCR, armazenamento ou integração na GUI.

### v0.6.1 — Vision Desktop Integration (implementado)

A janela Tk disponibiliza ações de Imagem/Tela/Câmera, pergunta e
consentimento explícitos por captura, análise assíncrona com
Ollama local e contexto textual efêmero para perguntas subsequentes.
Nenhuma imagem é persistida ou capturada automaticamente.

### v0.6.2 — Guided Autonomy & Conversation (implementado)

Todas as fontes de visão na GUI respondem com eSpeak NG quando a
leitura de voz está habilitada. A nova ação **Sugerir** bloqueia
a execução de ferramentas, mesmo quando sugeridas pelo modelo.
A ação **Cancelar** descarta resultados pendentes, previne novas
execuções após cancelamento e mantém a janela responsiva.

### v0.6.3 — Conversation Reliability (implementado)

Isolamento de gerações de Vosk/eSpeak NG, prevenção de escutas ALSA
sobrepostas, descarte de áudios obsoletos, cancelamento de confirmações
pendentes e testes de integridade do repositório.

**Próximo marco:** v0.7.x — Controlled Desktop Automation, com
autorização explícita, segurança e rastreabilidade.

---

# Automação

## v0.7.0 — Controlled Desktop Automation Foundation (implementado)

Consulta pontual de ID/título de janela ativa X11; digitação curta em
janela explicitamente identificada após confirmação humana por ação.
Registros de autorização e execução pelo SecurityGate; limites estritos
de entrada e timeout; nenhum shell, clique ou macro autônoma.
Automações host X11 não são executadas no sandbox de comandos Docker.

### v0.7.1 — Controlled Desktop Navigation (implementado)

Nova ferramenta `desktop_navigate`: quatro operações de navegação
por uma tecla direcionada a janela X11 identificada, com autorização
humana para cada ação, verificação de ID/título após consentimento,
sem atalhos livres, shell, macros ou cliques. Testes de segurança e
diagnósticos executados na CI.

### v0.7.2 — Desktop Interaction Safety & Diagnostics (implementado)

Diagnóstico passivo com estado de prontidão, motivo de indisponibilidade,
ações permitidas e limites de digitação/consentimento. Testes cobrem
as variantes X11 local, Wayland, display remoto e dependência ausente.
Não afirma compatibilidade física com aplicativos específicos.

### v0.7.3 — Desktop Target Integrity (código integrado; não publicada)

Consulta e confirmação apresentam ID, título, PID e classe da janela.
Digitação/navegação exigem os quatro atributos e os revalidam após o
consentimento. Metadados ausentes ou divergentes impedem o envio do
evento. Testes com subprocessos simulados foram acrescentados;
a validação em desktop X11 físico permanece pendente.

---

# Hardware e distribuição

## v0.8.x — Devices & Distributed Architecture

**v0.8.0–v0.8.2 (código integrado; sem release estável):** catálogo local validado de Arduino/ESP32, instalador Linux guiado, atualizações verificadas, Ubuntu 24.04 LTS como baseline e diagnóstico passivo multi-distro. **Futuro:** descoberta expressamente autorizada, provisionamento de nós, autenticação, transporte seguro, telemetria real e comunicação distribuída. Nenhuma dessas extensões futuras está disponível hoje.

Para microcontroladores:

```text
C / C++
```

é a direção preferencial.

---

# Interface multimodal

## v0.9.x — Multimodal Interface

O código v0.9.0–v0.9.12 já integra privacidade multimodal, atalhos,
comandos falados locais, análise visual por ação autorizada e verificação do
login PostgreSQL antes da ativação pelo instalador. A homologação
física e publicação estável continuam pendentes. Evoluções futuras incluem:

* interfaces acessíveis e multimodais avançadas;
* visão;
* status;
* integração de dispositivos.

**Estimativa de planejamento para concluir a linha 0.9.x no Ubuntu Desktop
(CI 24.04; aceite físico por versão pendente):** v0.9.12 integrada ao código,
com seu aceite físico e dois marcos de desenvolvimento restantes sujeitos
aos resultados dos testes:

| Marco proposto | Critério principal |
| --- | --- |
| v0.9.11 | Implementado no código: login PostgreSQL antes de ativar o instalador; diagnóstico e orientação Ollama/Vosk sem alegar teste físico. |
| v0.9.12 | Código integrado para ações desktop autorizadas por operação e frase exata de pasta; homologação física pendente. Teclado em outras janelas continua X11. |
| v0.9.13 | Encadear tarefas limitadas sob aprovações individuais, cancelamento e trilha de auditoria; hoje cada turno executa no máximo uma ferramenta. |
| v0.9.14 | Corrigir falhas encontradas no aceite físico Ubuntu/X11, instalação, voz, visão, Ollama e recuperação; verificar pacote e documentação antes de propor release. |

A quantidade é uma **estimativa**, não um compromisso de terminar em v0.9.14:
novas falhas podem exigir versões adicionais. “Fazer tudo no computador” não
é uma capacidade certificável sem delimitar ações e permissões. A publicação
estável exige CI no commit final da `main` e homologação física registrada.

---

# v1.0 — Production Baseline

Objetivo:

* instalação reproduzível;
* segurança validada;
* recovery;
* documentação;
* observabilidade;
* interfaces estáveis;
* portabilidade;
* capacidades locais úteis.

---

# Tecnologias atuais

```text
Primary Platform:     Linux
Runtime:              Python 3.12
Database:             PostgreSQL (local, Psycopg 3)
Tests:                pytest
Sandbox:              Docker
Local Model Runtime:  Ollama
Reference Model:      qwen3:1.7b
Version Control:      Git
Remote:               GitHub
```

---

# Tecnologias candidatas futuras

```text
whisper.cpp
openWakeWord
Piper
ComfyUI
PySide6
AppArmor
polkit
systemd
Podman rootless
Docker rootless
```

A presença na lista não representa decisão definitiva.

---

# Filosofia Local First

O Nexus Core deve continuar útil quando:

```text
Internet unavailable
```

Capacidades locais devem continuar locais quando isso for tecnicamente razoável.

---

# Privacidade

Princípios:

* processamento local quando viável;
* dados locais por default;
* nenhuma telemetria obrigatória;
* nenhuma API cloud obrigatória;
* nenhum envio silencioso de conteúdo;
* credenciais fora do código;
* integrações externas futuras explícitas e substituíveis.

---

# Observabilidade

O Nexus utiliza:

* logging;
* health;
* runtime state;
* snapshots;
* EventBus;
* security audit;
* erros explícitos.

---

# Fronteira entre inteligência e execução

Na `v0.3.1`:

```text
ModelRouter
     │
     ▼
ModelProvider
```

não está conectado a:

```text
ToolExecutor
SecurityGate
TerminalSandboxTool
Filesystem Tools
```

Essa separação é deliberada.

---

# Limitações atuais

Ainda não existem:

* memória persistente;
* Knowledge Base;
* visão;
* desktop automation;
* provider discovery;
* model discovery;
* provider health probes;
* fallback;
* streaming;
* cloud providers;
* dependency doctor;
* bootstrap automático;
* update manager;
* self-recovery;
* distributed nodes;
* device integration.

---

# Requirements e portabilidade

O projeto não deve ser documentado para uma máquina específica.

Baseline:

> **Linux systems with constrained compute resources; no dependency on dedicated GPU.**

Diagnósticos futuros devem detectar genericamente:

* sistema operacional;
* distribuição;
* CPU architecture;
* recursos;
* Python;
* dependências;
* Ollama;
* modelos;
* Docker;
* database;
* paths;
* permissions;
* configuração;
* serviços.

---

# Critérios de qualidade para releases

Uma release só deve ser fechada quando houver consistência entre:

```text
implementation
tests
architecture
documentation
requirements
roadmap
version
Git
tag
remote
```

Fluxo:

```text
planning
   │
   ▼
implementation
   │
   ▼
tests
   │
   ▼
architecture review
   │
   ▼
README
   │
   ▼
requirements
   │
   ▼
version
   │
   ▼
smoke
   │
   ▼
Git verification
   │
   ▼
versioned commit
   │
   ▼
annotated tag
   │
   ▼
push
   │
   ▼
remote verification
```

---

# Convenção de commits

Formato:

```text
<type>: Nexus Core v<VERSION> <description>
```

Exemplos:

```text
feat: Nexus Core v0.2.0 Implement Connectivity and Runtime Modes

feat: Nexus Core v0.2.1 Implement Runtime State Controller

feat: Nexus Core v0.2.2 Implement Continuous Connectivity Monitoring

feat: Nexus Core v0.2.3 Implement Automatic DEGRADED Runtime Detection

feat: Nexus Core v0.2.4 Implement Environment and Runtime Configuration

feat: Nexus Core v0.3.0 Implement Local Model Layer
```

---

# Tags

Releases versionadas utilizam tags Git.

Exemplos:

```text
v0.2.0
v0.2.1
v0.2.2
v0.2.3
v0.2.4
v0.3.0
v0.3.1
```

A `v0.3.1` foi fechada com tag anotada.

As tags `v0.3.1.1`, `v0.3.1.2`, `v0.3.1.3`, `v0.3.2`, `v0.3.3`, `v0.3.4`, `v0.3.5`, `v0.3.6`, `v0.3.7` e `v0.3.8` já existem.

---

# Política de desenvolvimento

Mudanças devem respeitar:

* uma capacidade pequena por release;
* testes antes do fechamento;
* nenhuma mudança silenciosa de arquitetura;
* nenhuma ampliação acidental de escopo;
* nenhuma dependência proprietária obrigatória;
* nenhuma alteração retroativa de release já publicada sem patch deliberado;
* compatibilidade quando contratos públicos são preservados.

---

# Licença

O código-fonte e a documentação do Nexus Core são licenciados sob
[MIT](LICENSE). A licença permite uso, modificação e redistribuição,
mantendo o aviso de copyright. A disponibilização pública do repositório
depende da visibilidade configurada no GitHub; uma licença, por si só,
não altera a visibilidade.

Licenças de:

* Ollama;
* Docker;
* bibliotecas;
* ferramentas;
* model weights;

devem ser consideradas separadamente.

---

# Status

```text
────────────────────────────────────────────────────────
Project:               Nexus Core
Code Version:          v0.9.12 (INTEGRATED IN MAIN; NOT RELEASED)
Release Name:          Authorized Desktop Actions
Release Tag:          v0.9.12 NOT YET PUBLISHED (PHYSICAL ACCEPTANCE REQUIRED)
Implementation:        ONE HOME CHILD BY EXACT PHRASE; APPROVED APP LAUNCH
Release Validation:    GITHUB ACTIONS CI REQUIRED FOR PUBLICATION
Tests:                 PYTHON 3.12 / POSTGRESQL 16 / DOCKER / XVFB / ESPEAK NG
Primary Platform:      Linux
Runtime Baseline:      Python 3.12
Database:              PostgreSQL (loopback, Psycopg 3)
License:               MIT
Linux Entry Point:     nexus-core
Sandbox:               Docker
Model Runtime:         Ollama
Reference Model:       qwen3:1.7b
Production Provider:   ollama
Desktop Interface:     NATIVE TK CONVERSATION (LINUX)
Voice:                 ESPEAK NG F/M; VOSK AUTOMATIC LISTENING WITH PAUSE
Agent / Tool Calling:  ONE PROPOSAL PER TURN, EXECUTOR MEDIATED
Development Status:    ACTIVE
────────────────────────────────────────────────────────
```

---

**Nexus Core**

Assistente pessoal de inteligência artificial **local-first**, construído sobre segurança, modularidade, controle operacional e evolução incremental.
