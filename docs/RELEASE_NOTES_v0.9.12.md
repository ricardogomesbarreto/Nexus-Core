# Nexus Core v0.9.12 — Authorized Desktop Actions

**Estado: código de desenvolvimento v0.9.12; PRs #83/#84 integrados à `main`,
com 1.779 testes aprovados na CI do commit `14d5f4c`. As tags candidatas
`v0.9.12-rc.1` e `v0.9.12-rc.2` apontam para os seus próprios commits.
Release estável continua pendente.** O aceite físico no notebook e a revisão explícita do
workflow de publicação ainda são requisitos para release. As
integrações Craft e REA são parciais; os três CLIs Craft reais não foram
homologados no Ubuntu 26.04 do usuário. Consulte a matriz e os gates no README.

### Correções posteriores à candidata rc.1

- Edição de imagem Pillow: preserva o canal de transparência de PNG/WebP em
  operações de cor, nitidez, blur e rotação/espelhamento; JPEG recebe fundo
  branco. Salva arquivo novo sem metadados da origem. Passou na CI; inspeção
  visual física ainda é necessária para afirmar resultado no notebook.
- O workflow de tag salta candidatas já publicadas, sem mover o ponteiro e sem
  deixar a CI futura vermelha apenas porque uma tag anterior foi preservada.
- O script de sessão rastreia apenas as instâncias que iniciar, em estado
  privado do usuário, e compara o identificador de ativação antes de parar.
  Isto corrige a parada indiscriminada de serviços preexistentes; ainda exige
  verificação física após a integração da correção.

Ao executar `nexus-core --desktop` no terminal, eventos `TESTE-LOCAL`
registram ao vivo estados e duração de chat, escuta, fala, câmera, visão e
permissões sem imprimir conteúdo privado ou produzir log por quadro.

O comando `nexus-core --acceptance-log` reúne verificações locais e perguntas
de observação física em uma saída resumida para compartilhar, sem imprimir
credenciais, transcrição ou imagens. Uso de microfone e câmera pede consentimento
separado; as observações manuais não são aprovação automática de release.

O registro físico recebido em 17/10/2026 confirmou uma transcrição Vosk no
teste isolado, mas a janela repetiu ciclos sem transcrição. O indicador de rede
alternou de estado; uma análise visual levou cerca de 119 s no notebook. A
partida dos serviços agora aguarda até 30 s pela API do Ollama, e o roteiro de
aceite separa o navegador padrão sem diálogo do gerenciador de arquivos com
confirmação. A escuta contínua e a latência visual continuam sem aceite.

## Entregas no código

**Integração em revisão — REA e instalação PostgreSQL (17/10/2026):**
a nova `inspect_artifact_local` identifica formatos binários,
APKs/JARs/ZIPs, WASM, JavaScript e Electron sem executar nem
descompilar o alvo. A leitura, sujeita ao `SecurityGate` e à
confirmação, é local e usa streaming SHA-256, limites de tamanho e
descritores sem seguir symlinks. O motor REA Node/MCP não foi
incorporado; Ghidra/IDA/Hopper e modalidades dinâmicas permanecem
opcionais e pendentes de revisão separada.

O instalador foi corrigido para detectar o cluster PostgreSQL local
parado e solicitar autorização para iniciá-lo antes da verificação
`SELECT 1` do ambiente Python, sem ativar serviços no boot. Consulte
a [documentação REA e os testes reais pendentes](REA_LOCAL_INTEGRATION_v0.9.12.md).
O conjunto só pode ser anunciado integrado após aprovação da CI
e merge; isso não representa aceite físico ou release estável.

**Auditoria corretiva complementar (17/10/2026):**
[documento e matriz de achados](AUDIT_v0.9.12_2026-10-17.md).
O instalador deixa de criar serviços Ollama habilitados automaticamente
no login; saídas dos CLIs Craft opcionais são lidas com descritores
regulares sem seguir symlinks, e rejeitam arquivo vazio ou formato
evidentemente incompatível. Imagens que disparam
`Image.DecompressionBombError` retornam erro seguro, e cartazes
suportam caminhos alternativos de fontes Linux. Os testes automatizados
não certificam os executáveis Rust externos ou a câmera e voz reais.

- Integração inicial de criação local por conversa: edição básica de foto e
  cartaz gráfico via Pillow; conversão opcional por PhotoCraft/WordCraft e
  extração de texto por PdfCraft se os CLIs estiverem instalados. Saídas novas
  sob confirmação e política de caminhos. Não equivale a geração fotográfica
  por IA nem comprova os CLIs ou o desempenho no notebook físico.

- A frase exata “Crie uma pasta chamada Projetos” e nomes simples semelhantes
  escolhem uma pasta filha da home sem esperar o modelo local. A ação ainda passa
  pelo contrato de ferramenta, `SecurityGate`, prévia do caminho, confirmação
  individual e auditoria. Nenhuma frase de consentimento é inferida pelo modelo.
- Abrir o navegador padrão por comando exato em X11/Wayland dispensa
  confirmação adicional e não recebe URL; o gerenciador de arquivos e o
  terminal continuam a exigir confirmação. Frases ambíguas não abrem apps.
- A prévia da câmera oferece **Tentar novamente**, com autorização por nova
  foto. Entradas com sinal contínuo e sem palavras do Vosk encerram a tentativa
  após oito segundos; a qualidade de voz exige teste no equipamento real.
- A pergunta falada da janela de autorização respeita a escuta pausada e
  orienta responder por botão ou texto nesse estado.
- O workflow de publicação manual v0.9.11 usa o SHA do evento correto e exige
  uma CI `push` bem-sucedida para o commit exato da `main`. A mesma proteção
  prepara o workflow v0.9.12. Ambos continuam bloqueados por `if: false`.

## Limites e aceite

O comando de pasta aceita apenas uma filha imediata da home e não interpreta
caminhos arbitrários. A fala pode transcrever um nome diferente; conferir o
alvo mostrado antes de aprovar é obrigatório. Digitação e navegação em janelas
de terceiros continuam restritas a X11; não existe controle de teclado
Wayland homologado. Abrir um aplicativo confirma somente a solicitação de
abertura, não o comportamento posterior do aplicativo.

O [roteiro de aceite físico](UBUNTU_PHYSICAL_ACCEPTANCE_v0.9.12.md) começa
pendente. CI, Xvfb e mocks não comprovam inferência Ollama, áudio, webcam,
automação X11 nem recuperação no notebook do usuário. Nenhuma tag v0.9.12
deve ser criada sem registrar esses resultados, obter CI no SHA final da
`main` e revisar expressamente o bloqueio do workflow de release.

## Desenvolvimento complementar — integrações locais avançadas (sem release)

- O ZIP original PdfCraft define `combine A B --out NEW`. O Nexus passa a
  aceitar “Junte os PDFs /home/.../a.pdf e /home/.../b.pdf em
  /home/.../combinado.pdf” na conversa, com confirmação das duas origens e
  destino, limite de 10 MiB por entrada, 25 MiB de saída e 90 segundos de
  execução; usa cópias temporárias privadas e salva somente arquivo novo.
  `--craft-capabilities` e o roteiro `validate_craft_cli.py --smoke --advanced`
  cobrem agora o comando. Testes de código e CLI simulado não comprovam que a
  junção real preserve páginas, metadados ou fidelidade no notebook.
- WordCraft `text` exporta DOCX/ODT/RTF para TXT UTF-8 novo com leitura de
  stdout limitada a 25 MiB e 90 segundos. PdfCraft `extract` copia até 20
  páginas explicitamente listadas para um PDF novo, sem alterar a origem.
  Ambos passam por confirmação individual e pelos caminhos protegidos.
- Validação da prévia PNG inclui CRC/blocos completos; o smoke `--advanced`
  testa também WordCraft `text` e PdfCraft `extract` sobre fixtures sintéticos.
  Executáveis reais, fidelidade, página efetiva e leitura independente do
  PDF ainda dependem do Ubuntu físico.

- Inspeção REA estática de envelopes WASM, com limite de 128 KiB, contagens
  por tipo e reconhecimento explícito de prefixo parcial. Nenhuma execução,
  descompilação, rede, MCP ou depuração.
- Índice de contêineres DOCX/ODT e características APK/ZIP adicionais,
  incluindo ABIs, bibliotecas nativas, symlinks e entradas de assinatura.
- Seis efeitos extras de fotografia via Pillow e conversões opcionais TIFF,
  ODT e RTF via CLIs Craft existentes.
- Recorte e redimensionamento de fotos PNG/JPEG/WebP por medidas explícitas
  na conversa, com confirmação, origem preservada e destino novo privado.
  A orientação EXIF é aplicada; a cópia não retém metadados da origem.
  Tamanho e dimensões são limitados. Testes no notebook e aceite continuam
  pendentes; essa entrega não altera o número de versão nem cria tag.
- Interface: prévia reduzida das imagens novas dentro do Nexus, acionada
  pela pessoa após a edição, sem abrir o editor externo ou gravar cópia;
  cabeçalho/barra de conversa reorganizados e autorização com detalhes
  roláveis. A identidade vinho e as decisões de permissão são preservadas.
  CI e aceite na sessão Wayland física permanecem necessários.
- Testes de autorização, arquivos inválidos e regressões, com aceite real
  dos CLIs e hardware ainda obrigatório. Serviço do sistema sempre sob demanda.

## Aditivo de integração dos ZIPs originais — sem publicação de release

- Novo `craft_inspect_local`: subcomandos `info` dos três Craft, JSON limitado
  e saída sanitizada; exige confirmação individual e arquivo autorizado.
- Novo `pdf_render_local`: uma página PDF por chamada, DPI fixo, saída PNG
  nova sem sobrescrita, tamanho e dimensões limitados.
- CLI de aceite `--smoke --advanced` exercita as operações originais sem dados
  pessoais quando os binários estiverem presentes.
- Motores REA externos/Node e modelos Ollama não são reinstalados, alterados
  ou habilitados automaticamente. v0.9.12 mantém gates físicos pendentes.
