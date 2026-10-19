# Inventário de funções locais e lacunas — 19/10/2026

Esta matriz compara os cinco ZIPs originais fornecidos pelo operador com a
implementação da `main`. Os nomes das fontes aparecem **somente neste registro
técnico** para rastrear licenças, contratos e testes. Na janela, na fala e nos
diagnósticos de uso, as funções pertencem ao NEXUS CORE. A presença de código
no ZIP não instala um programa no Ubuntu nem homologa sua execução.

**Estados:** `integrado` = implementação Nexus coberta por testes de código;
`parcial` = subconjunto; `pendente` = sem ferramenta Nexus equivalente;
`físico` = ainda não testado no Ubuntu real. A candidata `rc.3` é um snapshot
anterior a estas funções da `main`; a versão estável continua sob G0.

| Fonte auditada | Já integrado ao Nexus Core | Ainda faltando diretamente dessa fonte | Gate |
| --- | --- | --- | --- |
| `photocraft-main(1).zip`, `crates/algo/src/histogram.rs`, `apps/photocraft-cli/` | Efeitos locais, geometria, conversão opcional e **resumo de luminosidade/cores** sob confirmação (`image_colors_local`); físico pendente | Histograma RGB interativo, máscaras/camadas, curvas, ajustes reversíveis, pintura, texto/vetor, PSD em camadas, gestão de cor e aceleração GPU | G2: escolher operações pequenas, definir formato de trabalho e medir fidelidade/RAM; não importar editor inteiro |
| `wordcraft-main(1).zip`, `apps/wordcraft-cli/src/main.rs` | Conversão, metadados e texto extraído em cópia; físico pendente | Estrutura de parágrafos/tabelas, renderização de páginas, estilos, revisão, comentários, referências, edição tipada com `run`, preservação do layout e ida-e-volta DOCX/ODT | G3: contratos tipados, documentos de teste reais, leitor independente; nenhuma edição estruturada anunciada |
| `pdfcraft-main(1).zip`, `apps/pdfcraft-cli/src/main.rs` (`edit`, `extract`, `combine`, `split`) | Texto, metadados, prévia, extração, junção de dois PDFs e **giro/movimento de páginas em novo arquivo** (`pdf_organize_local`); CLI opcional, físico pendente | Divisão em vários arquivos, exclusão/inserção de páginas, busca, comentários, formulários, redação verificável, OCR, assinaturas e criptografia | G4: validar número e ordem das páginas com parser independente e arquivos multipágina; proteger saídas múltiplas/efeitos jurídicos |
| `rea-main(1).zip`, `README.md` e catálogo de ferramentas | Evidências estáticas de formatos e SHA-256, sem executar o alvo; código integrado, físico pendente | Desmontagem/decompilação profunda, comparação de versões, análise de runtime, memória/processos, integrações externas de JADX/Ghidra/WABT e relatórios especializados | G5: escopo autorizado, processo isolado, contratos e corpus defensivo antes de qualquer execução externa |
| `ollama-main(1).zip`, `README.md` e `api/types.go` | API local de chat/visão, consulta de modelos e recursos, retenção limitada; físico pendente | Streaming de tokens e fala interrompível, `/api/show` no diagnóstico, seleção de modelos por memória, fallback visual, embeddings/pesquisa semântica | G6: medir latência e RAM no notebook, cancelar inferência, manter serviços sob demanda |

## Alterações implementadas nesta revisão

- **PDF, giro:** “Gire as páginas 1,3 do PDF `/home/.../a.pdf` em 90 graus e
  salve em `/home/.../girado.pdf`”. Somente 90, 180 ou 270 graus; até 20 páginas
  distintas. O executável opcional recebe uma cópia temporária; a saída nova
  é validada estruturalmente, privada (`0600`) e não substitui arquivos.
- **PDF, movimento:** “Mova a página 2 do PDF `/home/.../a.pdf` para a posição
  1 e salve em `/home/.../ordenado.pdf`”. Uma página por pedido; posição
  de 1 a 5000. O conteúdo e a posição real dependem de teste multipágina
  com o motor instalado. A confirmação mostra a ação e os dois caminhos.
- **Foto, análise de luminosidade:** “Analise as cores da foto
  `/home/.../foto.png`”. Retorna largura/altura, média 0–255 e porcentagens
  de pixels escuros e claros. O cálculo usa Pillow local, exige permissão de
  leitura, limita bytes/dimensões e não grava nem transmite a foto. É um resumo
  numérico, não reconhecimento de objetos nem editor de histograma RGB.
- O diagnóstico de CLI exige que o executável de PDF anuncie `edit`. O smoke
  avançado executa giro de um PDF sintético somente com `--smoke --advanced`
  explícitos. Esses testes automatizados usam dublês de programa; **não**
  certificam o executável real do notebook.

## Pendências ordenadas

1. **G0 — obrigatório para estabilidade:** repetir o roteiro físico da 0.9.12
   no mesmo SHA da `main`, incluindo chat, voz contínua, câmera/visão, Wayland,
   serviços, ações autorizadas, consumo, instalação e recuperação. O último
   registro ainda tinha 11 verificações aprovadas e 10 pendentes.
2. **G1/G4 — CLIs opcionais:** identificar origem, licença, versão, hash e
   compatibilidade no Ubuntu; executar smoke real, conferir páginas e
   metadados por leitor independente; ausente é pendente. Divisão de PDF
   requer desenho de saídas múltiplas que não deixe resultados parciais.
3. **G2/G3 — edição profissional:** selecionar operações com benefício claro
   e saída verificável; preservar originais, fidelidade de camadas e layout.
   Geração livre de fotos exige modelo local adequado à RAM e licença.
4. **G5 — análise autorizada:** expandir parser estático com corpus e limites;
   funções dinâmicas precisam isolamento e consentimento próprios.
5. **G6/G7 — resposta fluida:** streaming/cancelamento, voz e câmera em
   concorrência, testes de qualidade/latência reais e acessibilidade da GUI.

Não há plano de importar todos os códigos-fonte ou telas dos ZIPs para dentro
do processo Python. Cada função só passa a “integrada” após contrato,
permissões, testes e registro explícito de limites; o teste físico é uma
evidência separada da CI.
