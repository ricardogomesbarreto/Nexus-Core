# Adequação dos três anexos à versão 0.9.18

Os ZIPs recebidos foram lidos como material técnico. Nenhum código, binário,
interface, modelo de voz ou arquivo de conteúdo foi incorporado. O Nexus Core
continua sob MIT, com PostgreSQL como único banco, Ollama local quando
solicitado, interface desktop nativa e serviços sob demanda. Nomes de
terceiros não aparecem como marcas dos recursos na janela do assistente.

| Arquivo recebido | Capacidades observadas | Recurso próprio nesta versão | Ainda fora do escopo leve |
| --- | --- | --- | --- |
| `VoiceStudio-main.zip` (AGPL-3.0) | Prévia, gerenciamento de motores, ditado, desenho/clonagem e edição de voz | Amostra curta da voz feminina/masculina já instalada, sem baixar nada | Clonagem, treinamento, motores GGUF, servidor/API, Electron, catálogos pesados e modelos adicionais |
| `DeepTutor-main.zip` (Apache-2.0) | Bibliotecas, leitura com fontes, questões, prática e revisão | Cartões voluntários vinculados a trechos da biblioteca PostgreSQL; revisão local simples | Geração automática de questões, RAG adicional, web/contas, gráficos de domínio, pipelines de pesquisa |
| `project-nomad-main(2).zip` (Apache-2.0) | Acervo offline, notas, dados, mapas, Ollama, catálogo de apps e Docker | A biblioteca, as notas, ferramentas de dados e mapas locais existentes recebem agora prática offline vinculada a fontes | Servidores Kiwix/Kolibri/Qdrant, Docker no login, download de catálogos, portas abertas e painel web |

O objetivo das três fontes é distinto do assistente de voz local com memória
limitada. O ZIP do estúdio de voz é AGPL: copiar sua implementação para o
aplicativo MIT exigiria uma revisão específica de licença e distribuição.
Esta versão implementa código original e não redistribui artefatos de nenhum
dos anexos. Materiais e modelos externos podem ter licenças próprias.

**Teste físico pendente:** executar no Ubuntu do operador a criação, revisão
e exclusão de cartões, prévia das duas vozes, escuta contínua, câmera, RAM e
swap em perfil `eco`, serviços sob demanda e arquivos reais. A CI com display
virtual e PostgreSQL de teste verifica o código, não o hardware ou a
adequação pedagógica da rotina.
