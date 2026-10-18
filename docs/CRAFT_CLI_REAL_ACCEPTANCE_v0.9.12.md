# NEXUS CORE v0.9.12 — Validação física dos CLIs Craft e REA

## Contexto

Este roteiro verifica **executáveis reais** instalados no Ubuntu 26.04. A CI verifica
o diagnóstico e os fixtures com dublês de teste; ela não prova que esses três
CLIs estão instalados e operantes no notebook do operador. A tag candidata
`v0.9.12-rc.1` pode identificar código testado na CI; não publicar release
estável com base exclusivamente em mocks.

### Contratos oficiais verificados nas fontes upstream

- [PhotoCraft CLI](https://github.com/storytold/photocraft/blob/main/apps/photocraft-cli/src/lib.rs): `photocraft-cli convert <in> <out>`.
- [WordCraft CLI](https://github.com/storytold/wordcraft): `wordcraft-cli convert <in> <out>`.
- [PdfCraft CLI](https://github.com/storytold/pdfcraft/blob/main/apps/pdfcraft-cli/src/main.rs): `pdfcraft-cli text <file.pdf>` escreve texto em stdout.
- [REA](https://github.com/Opiuz/REA): `rea` é um executável separado Node/TypeScript, não um módulo Python do Nexus. Seu motor avançado ainda não está integrado.

O Nexus já utiliza esses formatos de argumentos em `craft_convert_local`. O
script abaixo verifica se os comandos funcionam na versão **efetivamente
instalada**. Os ZIPs de origem não são binários compilados.

## Ubuntu 26.04 — Primeiro diagnóstico

Atualize o repositório depois do merge da PR. Instale cada CLI apenas de uma
fonte confiável, revisando integridade e versão (sem instalação automática
pelo Nexus).

```bash
cd "$HOME/Projetos/Nexus-Core"
command -v photocraft-cli
command -v wordcraft-cli
command -v pdfcraft-cli
python3 scripts/validate_craft_cli.py
```

O padrão executa somente `--help`. O estado `cli_detectado` confirma presença
e execução da ajuda, **não** confirma conversão. Ausência/falha produz exit code 1.

## Smoke tests REAIS (opt-in)

```bash
cd "$HOME/Projetos/Nexus-Core"
python3 scripts/validate_craft_cli.py --smoke
python3 scripts/validate_craft_cli.py --smoke --advanced
```

Com `--smoke` o script executa os **CLIs instalados**, cada um com
uma amostra criada no diretório privado temporário do sistema:

| CLI | Entrada sintética | Operação executada | Verificação |
| --- | --- | --- | --- |
| PhotoCraft | PNG RGB 1x1 | `convert foto.png foto.webp` | Assinatura RIFF/WebP |
| WordCraft | DOCX OOXML simples | `convert documento.docx documento.pdf` | Assinatura PDF |
| PdfCraft | PDF com o texto NEXUS CORE CLI | `text documento.pdf` | Texto esperado em stdout |

O limite é de 60 segundos por operação e 25 MiB para validar cada saída. O
diretório temporário é excluído ao final; não usa documentos pessoais,
não inicia Ollama, PostgreSQL, Docker, MCP, serviços REA nem faz downloads.

`--advanced` adiciona `info` dos três motores, `wordcraft-cli text` sobre o
DOCX sintético, `pdfcraft-cli render` em PNG com blocos/CRC verificados e
`pdfcraft-cli extract` da página 1 e `combine` de dois PDFs sintéticos
para PDF com cabeçalho, `startxref` e `%%EOF`. Um resultado de estrutura válida não certifica fidelidade do
documento ou isolamento do executável; abra e confira cópias autorizadas em
leitores independentes antes de homologar a capacidade.

Saída esperada (somente quando **todos realmente passarem**):

```text
[CLI-LOCAL] ferramenta=PhotoCraft estado=passou teste=conversao_real
[CLI-LOCAL] ferramenta=WordCraft estado=passou teste=conversao_real
[CLI-LOCAL] ferramenta=PdfCraft estado=passou teste=conversao_real
```

**Segurança:** pasta temporária e argumentos fixos NÃO são sandbox. O
executável externo roda com as permissões da sua conta e pode, por si
mesmo, acessar outros arquivos e a rede. Execute somente software confiável,
verificado, e não confunda retorno 0 com segurança certificada.

## REA: enriquecimento estático e próximos gates

O analisador estático próprio do Nexus apresenta agora:

- ELF: arquitetura identificada (x86/x86_64/ARM/AArch64/RISC-V),
  tipo ELF e endereço de entrada declarado quando o cabeçalho permite;
- PE: quantidade de seções declarada e variante PE32/PE32+;
- ZIP/APK/JAR: contagens de entradas criptografadas e caminhos atípicos,
  sem revelar nomes nem extrair arquivos.

Esses **metadados estruturais** não são análise comportamental,
descompilação ou detecção de malware. A ferramenta continua limitada a
128 MiB, leitura autorizada `SecurityGate`, escopo HOME e nenhum servidor,
rede ou execução de alvo.

Para verificar apenas a instalação opcional do CLI REA:

```bash
python3 scripts/validate_craft_cli.py --rea
```

Essa opção executa apenas `rea --help` (sem analisar arquivo, sem `rea setup`,
sem `npx`, sem Hopper/Ghidra, sem servidor MCP). Integração REA avançada
com formatos de evidências, isolamento real e CLI versionado exige uma
próxima revisão de segurança antes de liberar operações no assistente.

### Critérios que continuam pendentes

- Executar e registrar `--smoke` em cada CLI real do Ubuntu 26.04.
- Aceite físico de REA opcional, sem instalar automaticamente motores pesados.
- Homologação da escuta contínua, áudio/vozes, câmera, Wayland/X11 e
  restauração/autorizações, conforme roteiros de aceite anteriores.
- Manter serviços locais sob demanda; **não** criar tag/release **estável**
  v0.9.12 até todos os gates exigidos serem aprovados. A tag `-rc.1` não
  é estável e não satisfaz esse aceite.

## Formatos opcionais extras — etapa complementar 0.9.12

- PhotoCraft: conversão TIFF (`.tif`/`.tiff`) incluída nas extensões de
  entrada e saída; saída verificada pela assinatura TIFF antes de salvar.
- WordCraft: formatos RTF (entrada/saída) e ODT (saída), com validação mínima
  dos cabeçalhos. Dependem da CLI compilada e instalada pelo usuário.
- PhotoCraft (edição interna com Pillow): adicionados autocontraste, sépia,
  espelhamento horizontal e vertical, clareamento e contraste diretamente na
  janela de conversa do NEXUS (sem utilizar o CLI externo).

A CI cobre argumentos fixos, cabeçalhos, permissões, originais intactos e
regressões; **não** homologa formatos reais TIFF/ODT/RTF no notebook até
serem testados com as respectivas CLIs instaladas.

## Contratos originais e testes avançados

Os cinco ZIPs originais foram inspecionados. O comando opcional
`python3 scripts/validate_craft_cli.py --smoke --advanced` executa, quando
instalados os binários, `info` do PhotoCraft, WordCraft e PdfCraft e
`render --page 1 --dpi 96` do PdfCraft, em fixtures sintéticas. A CI não
certifica esses executáveis; exige verificação física no Ubuntu.
