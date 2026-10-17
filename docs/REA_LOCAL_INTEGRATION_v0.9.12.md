# REA + NEXUS CORE — Integração offline de inspeção estática v0.9.12

## Origem e compatibilidade

O anexo `rea-main.zip` foi inspecionado sem execução de código. Ele contém
**REA: Reverse Engineer Anything**, licença MIT, pacote npm `rea-agents`
v6.5.0, feito em Node.js/TypeScript (Node 22.19+, 24.11+ ou 26+).
O projeto oferece análise mais abrangente via CLI, MCP e ferramentas externas,
incluindo JavaScript/Electron, binários nativos, APK/JAR, WASM, Ghidra,
IDA, Hopper, observação de runtime e rede. Essas funcionalidades têm
dependências, limites de segurança e custos de CPU/RAM distintos.

A integração atual **não** instala nem executa o pacote anexado,
`npx`, MCP, Ghidra, depuradores, programas sob análise ou conectores de rede.
Nenhuma dependência Node/Rust passa a ser obrigatória no NEXUS CORE.
O código implementa um **subconjunto estático independente**, alcançado
pela conversa ou por transcrição da voz, sem abrir a interface de outro
programa. Não é uma incorporação integral do REA e não afirma ser seu motor
nativo de decompilação.

## Capacidades verificáveis adicionadas

| Recurso | NEXUS CORE v0.9.12 | Limite |
| --- | --- | --- |
| ELF Linux/Unix | Reconhece assinatura, classe 32/64 bits e código da arquitetura | Não reconstrói funções ou pseudocódigo |
| PE/MZ Windows | Identifica MZ/PE e código da arquitetura quando disponível na amostra | Não executa a aplicação |
| Mach-O | Identifica magic number nativo ou fat | Não descompila |
| WASM | Identifica magic number e versão | Não produz WAT |
| APK/JAR/ZIP | Lê somente índice ZIP, conta entradas, identifica AndroidManifest e DEX | Não extrai nem decompila bytecode |
| JavaScript/TypeScript | Detecta arquivo UTF-8 e conta referências sintáticas básicas | Não constrói grafo de importações completo nem executa JS |
| Electron ASAR | Reconhece extensão e documenta a necessidade de REA opcional | Não extrai/inspeciona o bundle |
| PDF/imagem | Detecta assinaturas PDF/PNG/JPEG | Conteúdo visual/textual é tratado nas integrações existentes |
| Integridade | Calcula SHA-256 e tamanho por streaming local, com limite de 128 MiB | Não certifica origem ou segurança do arquivo |

A leitura é mediada pelo `SecurityGate`, exige autorização individual,
só admite arquivo regular dentro da HOME não protegida e não segue links
simbólicos. O analisador usa descritores abertos e memória limitada:
não executa, descompacta, carrega em runtime ou salva o arquivo analisado.
Arquivos ZIP com índice maior que 3.000 entradas ou tamanho descompactado
declarado acima de 4 GiB são recusados. O cálculo de hash não requer rede.

**Não se deve usar o relatório como prova de ausência de malware, licença
válida ou de autorização para engenharia reversa.** Inspecione somente arquivos
próprios ou para os quais exista autorização de análise. Nenhuma função
de bypass de DRM, exploração ou interceptação de tráfego foi integrada.

## Exemplos na janela do NEXUS CORE

Abra `Testar funções → REA: inspeção estática local` para ver as instruções.
Para demonstrar com um ELF do próprio sistema, copie primeiro o arquivo para
sua HOME, respeitando o escopo autorizado:

```bash
mkdir -p "$HOME/NexusTestes"
cp /usr/bin/true "$HOME/NexusTestes/teste.elf"
printf 'import exemplo from "exemplo";\nexport const valor = 1;\n' > "$HOME/NexusTestes/teste.js"
```

Depois digite na conversa, adaptando o caminho ao usuário real:

```text
Analise o arquivo /home/usuario/NexusTestes/teste.elf
Inspecione o arquivo /home/usuario/NexusTestes/teste.js
Analise o aplicativo /home/usuario/Downloads/exemplo.apk
```

Para validar as permissões, negue a primeira solicitação e repita
autorizando a segunda. Os logs `TESTE-LOCAL` apresentam estados de
autorização e ferramentas sem registrar bytes analisados. Conversão
de documentos permanece sob PdfCraft/WordCraft/PhotoCraft e respectivas
limitações de binários opcionais. A análise estática do REA não utiliza
seus CLIs, não gera fotografias novas e não altera arquivos.

## Dependências avançadas para futura avaliação separada

A capacidade completa do REA exigirá um projeto de integração separado
com fronteiras explícitas de autorização para cada modalidade:

- CLI Node `rea-agents` de origem confiável e versão fixada;
- validação dos contratos reais do CLI, formato JSON e versões compatíveis;
- isolamento de execução e de rede, limite de CPU/memória/tempo/output,
  com prevenção de leitura de dados não autorizados;
- opções Ghidra/IDA/Hopper de licença e instalação geridas pelo usuário;
- escopos independentes para depuração de processos, navegador, rede e
  dispositivos, jamais autorizados por uma leitura estática;
- testes físicos em Ubuntu/Debian e posteriormente outras distribuições.

**Não incluir o arquivo ZIP original ou seus milhares de arquivos
automaticamente no repositório NEXUS CORE.** O anexo não é um pacote
instalado, e nenhuma comprovação de execução do REA completo foi feita.

## Falha no instalador PostgreSQL — corrigida no código

O notebook registrou que `python3 scripts/install_linux.py` interrompia
a instalação porque o PostgreSQL estava parado. Quando iniciado em seguida
pelo script de sessão, a janela conseguiu autenticar e abrir normalmente.

O instalador agora verifica `pg_isready` antes da autenticação final.
Se a porta 5432 estiver parada, consulta `pg_lsclusters --no-header`,
seleciona **exatamente um** cluster configurado para essa porta (18/main
no notebook informado) e **pede autorização explícita** para executar
`sudo systemctl start postgresql@18-main.service`. Não inicia o
cluster 16/main em 5433, não altera senhas/dados e não habilita
autostart. Uma recusa adia a instalação, mantendo a versão anterior.
`pg_isready` somente atesta prontidão do servidor; `SELECT 1`
autenticado no `--ubuntu-preflight` continua obrigatório.

Também é válido iniciar manualmente os serviços **antes** de instalar:

```bash
cd "$HOME/Projetos/Nexus-Core"
bash scripts/nexus_core_session.sh start
python3 scripts/install_linux.py
```

A saída `not-found` para `nexus-core-ollama.service` e
`disabled` para `ollama.service` é compatível com uso da unidade
**global** Ollama sem unidade do usuário: não é falha e não exige instalar
uma segunda instância do Ollama.

## Critérios de aceite

- Testes automatizados reais de parsers estáticos, autorizações,
  symlink, formatos falsos, limites ZIP, e fluxo de chat sem Ollama.
- Testes do instalador para PostgreSQL disponível, parado, recusa,
  cluster ambíguo e porta inválida — sem chamar sudo de verdade.
- CI GitHub Actions Ubuntu 24.04/Python 3.12/PostgreSQL 16/Xvfb verde
  no commit final da PR.
- Aceite no Ubuntu físico de leitura de ELF, JS e APK próprios,
  negação/aprovação, histórico de conversas e inicialização com
  PostgreSQL desligado. **Sem tag/release v0.9.12 até homologação.**

## Ampliação segura de metadados e validação externa v0.9.12

A inspeção offline agora inclui arquitetura/tipo/entrada declarada do ELF,
variante e seções declaradas PE e contagens ZIP criptografadas/caminhos
atípicos sem exibir os nomes dos membros. Esses dados não demonstram
segurança, vulnerabilidade ou comportamento real do aplicativo.

O teste de CLIs opcionais foi documentado em
[CRAFT_CLI_REAL_ACCEPTANCE_v0.9.12.md](CRAFT_CLI_REAL_ACCEPTANCE_v0.9.12.md).
A verificação somente de ajuda não valida conversão; para testar binários
reais o operador deve executar voluntariamente o smoke test no Ubuntu.

## Etapa complementar — estrutura WASM e arquivos empacotados

A análise **própria e offline** lê envelopes de seções WASM até 128 KiB,
com máximo de 512 seções e decodificação limitada de inteiros ULEB128.
Ela conta seções por categoria (imports, exports, código etc.), mas **não**
lê nomes, não valida o conteúdo semântico, não executa WASM e marca relatórios
parciais quando o arquivo excede a amostra. Estruturas de seção inválidas
são rejeitadas.

O índice ZIP passou a identificar contêineres DOCX/ODT por membros estruturais,
contar arquivos `.so` e ABIs Android conhecidas, entradas de assinatura,
links simbólicos e caminhos atípicos. Os resultados são apenas indícios do
índice e não verificam autenticidade, integridade de membros ou vírus.
Nenhum conteúdo interno é aberto ou descompactado.
