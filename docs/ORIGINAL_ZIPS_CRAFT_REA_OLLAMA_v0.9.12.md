# NEXUS CORE v0.9.12 — Integração a partir dos cinco ZIPs originais

## Inventário dos anexos inspecionados em 17/10/2026

| Anexo | Contrato comprovado no código-fonte | Integração no NEXUS CORE |
| --- | --- | --- |
| PhotoCraft Rust | apps/photocraft-cli/src/lib.rs: info <arquivo> -> JSON, convert <in> <out> | conversão existente; nova inspeção de metadados |
| WordCraft Rust | apps/wordcraft-cli/src/main.rs e crates/engine/src/cmd/file.rs: info <arquivo> -> JSON | conversão existente; nova inspeção de metadados |
| PdfCraft Rust | apps/pdfcraft-cli/src/main.rs: info <pdf> -> JSON; render <pdf> --page N --dpi 96 --out <png> | extração existente; novas inspeção e prévia PNG |
| REA Node/TypeScript | package.json: rea-agents 6.5.0, bin rea; scripts/rea.mjs exige dist/cli-runtime compilado | análise estática própria (sem executar REA) |
| Ollama Go | go.mod e API local | permanece como motor de IA já utilizado, serviço sob demanda |

Fontes: ZIPs originais anexados pelo operador, sem executar scripts de build
ou instalar dependências externas. Os executáveis **não acompanham** estes
ZIPs de código-fonte e **não foram executados no Ubuntu físico** nesta etapa.

## Duas funcionalidades de conversa adicionadas

1. Pedido exato de metadados usa a ferramenta craft_inspect_local:

       Consulte os metadados do arquivo /home/usuario/Documentos/relatorio.pdf
       Mostre os metadados da imagem /home/usuario/Imagens/foto.png
       Consulte os metadados do documento /home/usuario/Documentos/relatorio.docx

   PhotoCraft, WordCraft e PdfCraft devem estar instalados como binários
   independentes. Cada leitura passa por confirmação humana e PathSecurity,
   faz uma cópia temporária privada de até 20 MiB, invoca apenas o subcomando
   info fixo, aceita JSON de até 512 KiB, e devolve somente campos numéricos
   e booleanos em lista explícita. Autor, título, caminho do CLI, textos,
   nomes de camadas e metadados livres não são reproduzidos.

2. Pedido exato de prévia gera um **arquivo PNG novo** por PdfCraft:

       Renderize a página 2 do PDF /home/usuario/Documentos/estudo.pdf em /home/usuario/Imagens/pagina2.png

   A ferramenta pdf_render_local aceita uma única página de 1 a 5000, DPI
   96 fixo, entrada PDF de até 20 MiB, PNG de até 25 MiB e imagem até 8 MP,
   de no máximo 4096 px por eixo. A saída é criada com O_EXCL/O_NOFOLLOW e
   permissão 0600. A ferramenta não substitui o PDF ou PNG preexistente.
   A assinatura e o cabeçalho são checados, mas não constituem auditoria
   completa do PNG. O CLI tem timeout de 90 s.

Ambas funcionam pela conversa nativa, sem novos botões do programa original,
seguem autorização por chamada, não usam CLI MCP, serviços remotos, npx,
Ghidra ou execução dos binários sob análise pelo REA. O parser de comandos
explícitos não precisa acordar o Ollama para identificar os caminhos.

## Diagnóstico dos CLIs originais: gates físicos

O comando padrão verifica presença e resposta a --help. O --smoke executa
operações sintéticas básicas. A nova opção --advanced, somente com --smoke,
testa também info dos três CLIs e render do PdfCraft:

    cd "$HOME/Projetos/Nexus-Core"
    python3 scripts/validate_craft_cli.py
    python3 scripts/validate_craft_cli.py --smoke --advanced
    python3 scripts/validate_craft_cli.py --rea

A opção --rea verifica somente rea --help (não executa analisadores).
Testes reais exigem instalar separadamente versões confiáveis dos CLIs,
conferindo checksums e versões. **Binários de terceiros não são sandbox**
apenas por serem executados em diretório temporário: eles têm permissões
normais da conta Linux e podem acessar rede e outros arquivos.

## Restrições de homologação

- A CI do GitHub executa testes com fixtures e substitutos de subprocessos:
  ela prova integração Python e política de autorizações, não homologa os
  CLIs oficiais de terceiros no Ubuntu 26.04.
- Fazer teste manual dos CLIs no notebook, confirmando fonte, saída,
  ausência de alteração do original, CPU/RAM e permissões.
- Para o REA completo, construir integração isolada e versionada após
  análise separada das centenas de capacidades Node/MCP e dependências.
- A instalação Ollama/PostgreSQL não é modificada. Sem autostart e sem novos
  serviços ao login. Nenhum download, tag ou release antecipado.
- Manter v0.9.12 até aceite físico de voz, câmera, visão, Wayland e CLIs.
