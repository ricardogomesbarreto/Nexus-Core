# Recursos locais e aceite pendente — 19/10/2026

O pacote de referência desta etapa reúne uma plataforma de serviços web em
contêineres. O Nexus Core continua aplicativo nativo Linux, com PostgreSQL
local e Ollama sob demanda. As ideias aproveitadas são implementadas como
recursos próprios; nenhum serviço web do pacote é iniciado na instalação.

| Capacidade solicitada | Estado no Nexus Core após esta revisão | Lacuna real |
| --- | --- | --- |
| Biblioteca de informação offline | Painel nativo de importação explícita de `.txt`/`.md`, pesquisa de trechos no PostgreSQL e exclusão com confirmação | Leitor de acervos enciclopédicos e outros formatos, downloads, referências verificadas e pesquisa por voz |
| Assistente com documentos e busca semântica | Pergunta explícita sobre até três trechos textuais ao Ollama local, mostrando os trechos e seus IDs; sem acesso a ferramentas | Embeddings vetoriais, seleção semântica, provas de veracidade da resposta; não anunciar busca semântica |
| Educação offline | Documentos textuais podem ser indexados explicitamente | Cursos, perfis, progresso e multiusuário não integrados |
| Mapas offline | Nenhum mapa é carregado | Pacotes regionais, renderização, busca geográfica e licença/distribuição dos dados |
| Ferramentas de dados | Painel nativo e `--data-tool`: SHA-256, Base64, hexadecimal e URL para texto UTF-8 limitado | Criptografia autenticada, formatos binários e outras receitas não integradas; codificação/hash não fornecem sigilo |
| Anotações | Painel nativo e CLI de notas Markdown em PostgreSQL, criação/edição/exclusão voluntárias | Sincronização, anexos e acesso por voz/chat sob SecurityGate ainda não integrados |
| Medição de sistema | Medição voluntária e limitada de CPU (`--benchmark`) e diagnóstico passivo de RAM/swap (`--resource-check`) | Pontuação comparável entre hardware e ranking comunitário ausentes; nenhum dado é enviado |
| Catálogo de aplicativos | Abertura controlada de alguns aplicativos do desktop já existe | Instalação por catálogo e orquestração de contêineres não integradas; precisam limites de armazenamento, isolamento, autenticação e licença |

## Mudanças de código nesta revisão

- O teste de **duas falas** agora só registra um turno depois de uma resposta
  bem-sucedida em voz e da retomada da escuta. Transcrever duas frases não
  certifica conversa contínua. Erro de fala, pausa ou cancelamento deixam o
  diagnóstico pendente. Logs não incluem o conteúdo da fala.
- O menu **Recursos** oferece **Anotações locais**, **Ferramentas de dados** e
  **Medir CPU local**, além da **Biblioteca local**. Anotações somente entram no PostgreSQL quando o usuário
  salva; exclusão pergunta antes de agir. A leitura da lista abre conexão
  somente ao abrir o painel. O painel de anotações usa trabalhador separado
  da thread Tk. Nada é adicionado automaticamente ao contexto do modelo.
- Entradas de dados são limitadas a 64 KiB; saídas codificadas têm o mesmo
  limite. Decodificação exige UTF-8 válido. O benchmark usa uma alocação de
  1 MiB e uma janela aproximada de 400 ms; sua taxa SHA-256 não é uma medida
  de temperatura, autonomia ou capacidade de inferência.
- A biblioteca importa textos UTF-8 até 256 KiB do diretório pessoal com
  acesso seguro por descritor, exige ação explícita na janela e mostra os
  trechos realmente selecionados pela busca textual. **Perguntar aos
  documentos** envia somente esses trechos ao Ollama em loopback e não oferece
  ferramentas de execução ao modelo; a resposta gerada precisa ser conferida
  nos trechos mostrados. Sem resultados, o Ollama não é acionado.

## O que o ZIP contém e o que falta para a proposta

São **664 arquivos** (cerca de 19 MB descompactados): aplicativo web e testes
em TypeScript/React, scripts de instalação, manifestos de serviços,
catálogos de conteúdo e dois acervos ZIM pequenos de demonstração (cerca
de 4,4 MB cada). **Não há** acervos completos, cursos baixados, pacotes
regionais de mapas, modelos Ollama prontos, vozes Vosk/Piper ou executável
desktop Linux do Nexus. O conjunto original opera vários serviços em
contêineres e pelo navegador; não é um pacote instalável do Nexus.

Também faltam dados de licença, tamanho, integridade e atualização para
cada acervo que se deseje disponibilizar; memória e espaço em disco devem
ser medidos no notebook antes de baixar ou ativar serviços adicionais.
Números da comparação são inventário do arquivo recebido, não prova de
compatibilidade física ou de prontidão para distribuição. Nenhum código,
catálogo ou acervo de terceiros foi copiado para dentro do Nexus nesta etapa.

Exemplos explícitos no terminal, após instalar o checkout atual e iniciar
somente os serviços necessários à edição de notas:

```bash
printf 'Meu texto local\n' | ~/.local/bin/nexus-core --note-create 'Rascunho'
~/.local/bin/nexus-core --note-list
~/.local/bin/nexus-core --note-get 1
printf 'Texto revisado\n' | ~/.local/bin/nexus-core --note-update 1 --note-title 'Rascunho revisado'
~/.local/bin/nexus-core --note-search 'revisado'
~/.local/bin/nexus-core --knowledge-import "$HOME/Documentos/aula.md"
~/.local/bin/nexus-core --knowledge-search 'assunto'
~/.local/bin/nexus-core --knowledge-answer 'assunto'
printf 'Olá' | ~/.local/bin/nexus-core --data-tool sha256
~/.local/bin/nexus-core --benchmark
```

Não colocar informações sigilosas diretamente em argumentos de linha de
comando. A entrada padrão evita expor o corpo da nota no histórico da shell;
`--note-get` mostra o conteúdo solicitado na saída do terminal. O painel
também mostra o texto somente na janela local.

## G0: provas que ainda dependem do notebook físico

| Prioridade | Prova objetiva exigida | Estado |
| --- | --- | --- |
| Crítica: Vosk | Duas perguntas distintas, duas respostas pertinentes e faladas; logs `teste recebido` e `teste concluido` depois de `fala concluido` e `escuta iniciado` | **Pendente** no Ubuntu físico; lógica corrigida em código |
| Crítica: câmera | Permitir e negar captura, obter prévia, foto e descrição coerente; medir tempo e RAM/swap | **Pendente** |
| Alta: vozes | Ouvir feminina e masculina, pausar, retomar e cancelar durante playback | **Pendente** |
| Alta: Ollama eco | Respostas distintas, medir `--resource-check` antes/depois e `ollama ps` após a conclusão | **Pendente** |
| Alta: permissões | Negar, permitir e cancelar pela janela, texto e fala sem autorização implícita | **Pendente** |
| Alta: serviços | Testar dois cenários: serviços já ativos e iniciados pelo script; parar apenas os que têm identidade de sessão registrada | **Pendente** |
| Alta: interface | Foco, notas, histórico, câmera e diálogos em Wayland; automação de teclado em sessão X11 à parte | **Pendente** |
| Alta: arquivos | Converter/editar exemplos reais, inspecionar saídas com programa independente e testar CLIs opcionais reais | **Pendente** |
| Final: release | SHA da main com CI verde, relato físico sem falhas críticas, revisão do bloqueio do publicador estável | **Bloqueada** |

O registro anterior de 18/10 confirmou preflight/modelo, microfone e quadro
da câmera, mas deixou o aceite completo da janela pendente. Nenhum teste de CI
substitui resposta audível, qualidade da descrição visual ou parada segura
de serviços reais na máquina do operador. Não há nova tag estável nesta etapa.
