# Nexus Core v0.9.12 — Authorized Desktop Actions

**Estado: código de desenvolvimento v0.9.12 até o PR #78
integrado à `main`; 1.744 testes aprovados na CI do PR #78. Sem tag/release
estável.** O aceite físico no notebook, a CI `push` do SHA final e a revisão
explícita do workflow de publicação ainda são requisitos para release. As
integrações Craft e REA são parciais; os três CLIs Craft reais não foram
homologados no Ubuntu 26.04 do usuário. Consulte a matriz e os gates no README.

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
