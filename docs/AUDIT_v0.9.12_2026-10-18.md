# Auditoria complementar do Nexus Core — 18/10/2026

**Escopo:** código v0.9.12 na `main` após PR #82 (`faef8cf`), cinco ZIPs
originais anexados, README canônico, testes, contratos de ferramentas,
interface, instalador e workflows de CI/publicação. São **369 arquivos
versionados no commit-base** (118 em `nexus/`, 140 em `tests/`, 44 em `docs/`).
O inventário foi automatizado; os caminhos de maior risco foram examinados
individualmente. Não é uma afirmação de revisão manual de cada linha ou de
execução dos binários Rust/Node/Go no notebook.

## Proveniência dos anexos inspecionados

Cada arquivo ZIP passou por teste CRC completo nesta sessão. SHA-256 local:

| Anexo | SHA-256 | Uso permitido no Nexus nesta etapa |
| --- | --- | --- |
| `photocraft-main(1).zip` | `17872ac5bc80e42187692cb0d006c402e08a3d56ca27ce2ec917104a74e578c4` | Contratos `convert`/`info`; edição Pillow própria; `run`, `batch`, MCP e GUI upstream não incorporados. |
| `wordcraft-main(1).zip` | `6c586688af6af733d5e4592748986895631b4706fe077cb399a8b08a77ef53b8` | CLI `text <file>` imprime texto no stdout; DOCX/ODT/RTF → TXT novo via Nexus. `inspect`, `render`, `run` e Zotero pendentes. |
| `pdfcraft-main(1).zip` | `c8b94ec6627c907e898039e3c28aeee90a048907ca4bffb90568a585606e6349` | CLI `extract <in> --pages LIST --out OUT`; lista limitada e PDF de saída novo. `edit`, `combine`, `split`, OCR, formulário e assinatura pendentes. |
| `rea-main(1).zip` | `2e82ceac46f2866e7144c4d57ab94ee0f9662512715106b030660be002356684` | Inspiração para inspeção estática própria; motor Node, depuração e desmontagem não incorporados. |
| `ollama-main(1).zip` | `ee0f333af038456ffe48ad6e1442091141b12697fc7a47918d11e527ace3f7e9` | API local de conversa/visão e diagnósticos já usada; nenhum serviço Go embutido. |

Esses hashes identificam os **anexos recebidos**, não certificam a procedência
de qualquer executável encontrado no `PATH`. Clonar/compilar upstream requer
revisão específica de lockfiles, licenças e artefatos antes da distribuição.

## Achados nesta revisão

| ID | Área | Evidência | Tratamento ou limite |
| --- | --- | --- | --- |
| B01 | Prévia PDF | `_validate_png` aceitava somente assinatura/IHDR/dimensões; bloco corrompido ou arquivo sem `IEND` podia virar imagem entregue como sucesso. | Percorre blocos, verifica limites e CRC, requer `IDAT` e `IEND` final. Não decodifica os pixels; conferir visualmente no Ubuntu. |
| B02 | Texto dos CLIs | Extração PDF anterior redirecionava stdout para arquivo temporário sem limite durante a execução; limite de 25 MiB só era aplicado ao ler depois. | Captura de texto Word/PDF passou a usar leitura incremental com limite de 25 MiB e prazo de 90 s; mata o processo imediato ao exceder. Conteúdo TXT precisa ser UTF-8 e não vazio. |
| B03 | WordCraft | O ZIP confirma `wordcraft-cli text` para texto simples, mas o Nexus oferecia apenas conversão de documentos e `info`. | `document_text` no contrato existente, pedido explícito por conversa e confirmação de origem/destino; original intacto, destino novo `0600`. |
| B04 | PdfCraft | O ZIP confirma `extract --pages`, sem operação correspondente no Nexus. | Ferramenta nova `pdf_extract_pages_local`: números 1–5000, até 20 páginas distintas, sem opções arbitrárias, cópia privada, saída de até 25 MiB e validação estrutural básica de PDF. Página inexistente precisa ser recusada pelo CLI real; ainda não há verificação independente da contagem. |
| B05 | Divulgação de funcionalidades | Diagnóstico `--craft-capabilities` da PR #82 não refletia `text` Word ou `extract` PDF recém-integrados. | Lista fixa atualizada; `available` ainda significa versão/comandos anunciados, não homologação física ou autorização permanente. |
| B06 | Aceite físico | Log anterior no Ubuntu 26.04 comprovou um reconhecimento isolado, quadro de webcam e inferência local, mas deixou pendentes escuta contínua, vozes, janela de permissão, edição real, Wayland e restauração. | G0 permanece aberto. O candidato `-rc.1` só identifica código testado na CI; release estável v0.9.12 continua bloqueada. |

## Fronteiras verificadas no código

- Ações novas entram pelo mesmo `ToolRegistry`/`ToolExecutor`/`SecurityGate`,
  passam por confirmação individual e exibem caminhos e páginas antes da
  decisão. A mensagem atual deve conter caminhos exatos; histórico de chat
  não fornece parâmetros executáveis.
- O acesso a entrada e saída usa `PathSecurity` com descritores ancorados e
  `O_NOFOLLOW`; a saída externa é lida de uma pasta temporária privada e o
  destino final é criado com `O_EXCL` e `0600`. Saídas vazias, grandes,
  corrompidas ou symlinks falham antes de publicar cópia.
- `pdf_extract_pages_local` valida formato básico (`%PDF`, `startxref`,
  `%%EOF`), **não** parseia o catálogo ou confere fidelidade, conteúdo ou
  quantidade de páginas do resultado. Comandos `run`, scripts e servidores
  MCP dos ZIPs não são expostos ao modelo.
- O Linux do usuário permanece local; PostgreSQL é o único banco principal.
  Ações Craft não instalam componentes nem ativam serviços no login.

## Validação e riscos remanescentes

Antes desta PR, a CI do PR #82 aprovou **1.752 testes** no Ubuntu 24.04,
Python 3.12, PostgreSQL 16 e Xvfb. Nesta alteração: `compileall` e
`git diff --check` são executados localmente; a CI de PR e a CI `push` da
`main` devem confirmar a suíte completa e o SHA final. Testes das novas
ações exercitam negação, permissões, argumentos fixos, páginas inválidas,
saída excessiva/corrompida, symlink, preservação de original e roteamento
apenas pela mensagem atual. O smoke `--advanced` foi ampliado para executar
`wordcraft-cli text` e `pdfcraft-cli extract` sobre amostras sintéticas **quando
esses binários confiáveis estiverem instalados**.

1. **Executável externo não é sandbox.** `--help`, conversão e extração
   executam código com o usuário Linux e podem ter acesso a arquivos, variáveis
   de ambiente e rede. O Nexus não distribui nem comprova hashes de binários
   Craft; G1 exige origem, licença e isolamento real antes de ampliar o uso.
2. **Desempenho/cancelamento:** ações Craft têm timeout, mas o botão de
   cancelamento da GUI não interrompe imediatamente todos os subprocessos
   externos em andamento. Ensaiar duração/RAM no perfil `eco` e projetar
   cancelamento de processo seguro sem encerrar serviços de terceiros.
3. **Saída documental:** o cabeçalho de PDF, CRC PNG e UTF-8 são validações
   mínimas, não prova de abertura em outros leitores, layout, ordem de páginas,
   texto completo ou qualidade visual. Usar corpus autorizado em G3/G4.
4. **Hardware físico:** Ubuntu 26.04/Python 3.14/Wayland, microfone Vosk
   contínuo, vozes, câmera, vídeo, Ollama local e PostgreSQL parado/reiniciado
   precisam de novo registro em `--acceptance-log` no SHA final.
5. **Tags:** `v0.9.12-rc.1` é candidata e pode ser criada uma vez após CI
   `push` verde para o SHA corrente da `main`. A automação recusa mover a tag
   ou publicar release estável. A tag v0.9.12 e o workflow de publicação
   estável permanecem bloqueados até o G0 físico.

**Próximo gate:** atualizar e instalar no notebook; rodar `--craft-capabilities`,
`--acceptance-log` e `scripts/validate_craft_cli.py --smoke --advanced` com
binários reais verificados, anotar quais estão ausentes e testar os dois
pedidos documentais em arquivos de teste próprios. Compartilhar somente logs
sanitizados, sem senhas, conteúdo de documentos ou fotos.

## Complemento após a candidata rc.2 — ciclo de serviços

Em 18/10, a `main` avançou para `14d5f4c`, marcada pela candidata imutável
`v0.9.12-rc.2`. A CI do **SHA exato** aprovou **1.779 testes**; a última
release estável publicada no GitHub permanece `v0.7.2`. O inventário agora
contém **372 arquivos versionados** (119 em `nexus/`, 141 em `tests/`,
45 em `docs/`). Todos os caminhos foram inventariados; `compileall`
varreu os módulos Python e uma busca textual não encontrou referência ao
banco legado. Os caminhos críticos de mídia, sessão, segurança, instalador,
publicação e documentação foram inspecionados diretamente. Essa cobertura
não afirma leitura manual de cada linha ou teste de hardware.

**S01 — parada de serviços de terceiros (corrigido no código, teste físico
pendente).** `scripts/nexus_core_session.sh stop` enviava `systemctl stop`
para Ollama e PostgreSQL mesmo quando `start` os encontrara em execução.
Isso contrariava a regra de serviços sob demanda do projeto e podia
interromper NUTRA, ERP, ADV ou outro aplicativo do usuário. Agora `start`
registra em `XDG_RUNTIME_DIR/nexus-core` apenas unidades que ele iniciou,
com permissão privada e `InvocationID` da ativação. `stop` compara a unidade
e o identificador antes de parar; serviços preexistentes ou reiniciados por
outro processo ficam intactos. Sem diretório runtime privado, a inicialização
de um serviço indisponível é recusada em vez de prometer uma parada segura.
Os testes simulados cobrem preexistência, início próprio, reinício externo e
segunda parada; o Ubuntu real ainda precisa reproduzir o ciclo. Se outro
aplicativo passar a usar uma unidade iniciada pelo Nexus na mesma ativação,
o script não consegue detectar esse compartilhamento: feche esses
aplicativos antes de chamar `stop`.

**D01 — README desatualizado (corrigido).** O cabeçalho ainda tratava a
`rc.2` como futura e citava somente os testes do PR #82, embora o PR #84
e a CI da `main` tivessem terminado. Foram atualizados o estado das tags,
matriz de edição e instruções de serviços, preservando o histórico de
versões antigas como histórico.

**Contagem de versões:** o plano histórico estima **dois marcos de código
após 0.9.12**, `0.9.13` (tarefas encadeadas com autorização por etapa) e
`0.9.14` (correções do aceite), além da promoção **estável de 0.9.12**.
O roadmap canônico G0–G8 não fixa uma contagem de releases para chegar à
`1.0`: falhas reais podem exigir mais marcos. G0 permanece aberto por escuta
contínua, vozes, câmera e desempenho, ações na GUI, Wayland/X11, restauração
e CLIs externos ainda sem aceite físico. Portanto o incremento numérico
para `0.9.13` não é justificado somente por esta auditoria.
