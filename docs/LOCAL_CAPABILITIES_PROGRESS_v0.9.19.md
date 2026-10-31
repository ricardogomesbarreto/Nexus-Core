# NEXUS CORE v0.9.19 — avanço verificável da suíte local

Estado: desenvolvimento no PR #102, sem aceite físico e sem tag estável.

## Entregue nesta rodada

- Ferramentas de dados: hashes SHA-256/512, SHA3-256 e BLAKE2b-256;
  Base32/64, hexadecimal, URL, ROT13 e formatação/minificação JSON. Receitas
  opcionais de 1 a 8 operações, até 64 KiB de entrada **e de cada resultado**.
  O terminal usa entrada padrão; a janela processa apenas após clique.
  Nada é enviado para o Ollama nem salvo no banco.
- Medição local voluntária de SHA-256 e cópia em RAM. O modo completo faz
  duas fases de cerca de 400 ms, com dois buffers de 4 MiB; sem disco, rede,
  pontuação ou ranking. Os resultados são indicativos e dependem da carga
  do computador durante o teste.
- Catálogo nativo e restrito de aplicativos: navegador padrão, gerenciador
  de arquivos e terminal. Mostra disponibilidade sem abrir programas;
  cada abertura é por clique. Arquivos e terminal pedem confirmação.
  O navegador usa a configuração padrão do desktop, inclusive Brave quando
  configurado assim pelo usuário. Não há instalação automática.
- Imagem local opcional: ID completo `sha256:` já presente no Podman rootless,
  cgroups v2 e runtime local. O usuário confirma cada execução na interface
  ou digita `sim` em um terminal interativo. O Nexus não aceita nome de
  registro/tag, comando livre nem montagem de arquivos. Usa
  `--pull=never`, rede desativada, filesystem somente leitura, volumes da
  imagem ignorados, sem privilégios, 256 MiB de memória, 1 CPU, 64 processos,
  até 20 segundos e 16 KiB de saída. Registra autorização/resultado na
  auditoria local; uma janela fechada solicita cancelamento. É execução
  efêmera, não um gerenciador de serviços. Exemplo de teste com uma imagem
  aprovada e já instalada: `nexus-core --local-image-run sha256:ID_COMPLETO`.
- Índice semântico PostgreSQL opt-in: até 16 trechos iniciais por documento
  e 256 vetores no total. O Ollama gera vetores somente mediante confirmação
  na Biblioteca ou comando explícito. Uma consulta gera um vetor da pergunta,
  compara até 256 vetores em memória limitada e mostra as fontes; exclusão
  do documento remove seus vetores por cascata. Não há outro serviço de banco
  e nenhuma varredura/indexação automática. [Detalhes e teste](SEMANTIC_INDEX_v0.9.19.md).

## Pendências que estas mudanças não encerram

A [auditoria de cobertura](OFFLINE_SUITE_STATUS_v0.9.19.md) continua sendo a
referência para oito capacidades. A biblioteca ZIM requer teste com arquivo
real e não oferece busca integral. O índice semântico agora persiste amostras
limitadas, sem indexação total de corpus grande. Cursos nativos e notas não equivalem a plataformas de
terceiros com serviços próprios. Mapas vetoriais, pesquisa geográfica,
catálogo de instalação, gerência persistente de contêineres, ranking comunitário e integração integral
de ferramentas externas permanecem pendentes. A operação deve continuar
local e leve, com PostgreSQL como banco do assistente.

## Validação

- Testes dirigidos de vetores, limites e CLI; UI de catálogo exige display
  virtual ou desktop real para exercício de botões.
- Suíte local: 1.948 aprovados e 149 ignorados neste ambiente sem hardware,
  display e PostgreSQL autenticado. Os novos testes usam
  um runtime simulado; não comprovam isolamento, limites ou execução física
  em Podman. CI do novo SHA e aceite Ubuntu/Fedora
  ainda necessários antes de considerar qualquer release estável.
