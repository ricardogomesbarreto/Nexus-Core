# NEXUS CORE v0.9.12-rc.3 — candidato para testes no Ubuntu

**Tipo: pré-lançamento de código, não release estável.**

A tag e os artefatos representam o **commit exato da `main` aprovado
pelo workflow CI de `push`**, e não uma confirmação de compatibilidade
física ou de funcionamento de todos os programas externos. O número do
pacote Python permanece `0.9.12` durante a fase candidata.

## Funcionalidades incluídas no candidato

- Interface desktop Tk profissional com identidade oficial NEXUS CORE
  (vinho #722F37), cabeçalho, chat, histórico local, atalhos,
  acessibilidade, controle de leitura e painel de permissões.
- Conversa via Ollama local; perfis de consumo de recursos, diagnósticos e
  serviços PostgreSQL/Ollama sob demanda, sem habilitação no boot.
- Captação de voz, síntese local e captura autorizada de imagem, tela e
  câmera, com condições de cancelamento e auditoria.
- Edição não destrutiva de imagens, cartazes e operações básicas de
  geometria; preservação de alfa PNG/WebP e composição branca em JPEG.
- Metadados e conversões opcionais de imagens/documentos, texto de
  documentos e PDF; visualização e extração de páginas PDF; junção
  autorizada de dois PDFs em uma saída nova; uso restrito de CLIs
  externos, **somente se instalados e compatíveis**.
- Triagem offline autorizada de arquivos e formatos ELF/PE/WASM/ZIP,
  sem executar o arquivo inspecionado e sem incorporar o runtime REA
  profundo, Ghidra ou MCP automaticamente.
- Interface pública de capacidades apresentada como funções do
  **NEXUS CORE**; proveniência de componentes na documentação de engenharia.

## O que foi testado automaticamente

- O workflow CI testa Python 3.12 no Ubuntu 24.04 com PostgreSQL 16
  em serviço de CI e display virtual Xvfb.
- Testes de permissões, limites de saída, comportamento com falha,
  privacidade, UI, componentes documentais, analisadores e regressão.
- O publicador somente age se o próprio `workflow_run` corresponde a um
  `push` da `main` com conclusão `success`; compara a versão
  `0.9.12` e o SHA atual de `origin/main` com o SHA testado. A tag
  `v0.9.12-rc.3` é imutável, e qualquer conflito de SHA interrompe
  a operação. O wheel tem SHA-256 anexo em `SHA256SUMS`.
- A tag de código e o artefato de distribuição só são criados
  **depois** desses gates. Antes de instalação, verificar o hash.

## O que ainda não pode ser declarado homologado

O [roteiro físico](UBUNTU_PHYSICAL_ACCEPTANCE_v0.9.12.md)
registrou em **18/10/2026** 11 verificações aprovadas e **10 pendentes**:
as operações manuais do desktop, continuidade de escuta, respostas visuais,
permissões, desempenho e uso de teclado em Wayland não tiveram aceite final.
O teste isolado de microfone/modelo/câmera não representa o funcionamento
contínuo desses dispositivos. O ciclo de posse e parada de serviços deve
ser repetido no notebook real.

PhotoCraft, WordCraft, PdfCraft e REA externos permanecem sujeitos à
compilação, instalação, integridade e smoke tests **reais** no Ubuntu 26.04.
Mocks em CI não fornecem essa prova. Binários de terceiros executam sob as
permissões do usuário e não recebem isolamento apenas por usar pasta temporária.

**Não publicar `v0.9.12` estável** enquanto G0 não estiver concluído.
O workflow estável `release-v0.9.12.yml` segue com bloqueio explícito.
Não mexer em tags `rc.1`, `rc.2` ou `rc.3` já existentes.

## Instalação e verificação

Esta candidata é um **pacote para testadores técnicos**; prefira atualizar
o checkout do GitHub e usar o instalador do projeto, evitando instalar em
um ambiente desconhecido automaticamente:

    cd "$HOME/Projetos/Nexus-Core"
    git switch main && git pull --ff-only
    bash scripts/nexus_core_session.sh start
    python3 scripts/install_linux.py
    NEXUS_RESOURCE_PROFILE=eco bash scripts/nexus_core_session.sh desktop

Para testar os binários opcionais, somente depois de conferir sua origem
e aceitar a execução:

    python3 scripts/validate_craft_cli.py --smoke --advanced
    ~/.local/bin/nexus-core --acceptance-log

Ao encerrar o assistente, se nenhum outro aplicativo precisar dos serviços:

    bash scripts/nexus_core_session.sh stop

**Arquivos do candidato:** wheel Python, arquivo `SHA256SUMS` e código
fonte versionado. As próximas etapas estão no
[roadmap e nos gates da v0.9.12](ROADMAP_v0.9.12_RELEASE_STATUS.md).
