# NEXUS CORE v0.9.19 — Auditoria da suíte offline (8 capacidades)

**Auditoria realizada sobre o código de desenvolvimento do PR #102.**
Diferenças entre *implementação nativa equivalente*, *conector real* e
*funções de terceiros ainda não integradas* são intencionais e não devem
ser confundidas.

| Capability / Projeto original | Código existente | Estado real | Próximo gate |
|---|---|---|---|
| Information Library — **Kiwix** | `nexus/knowledge/offline_catalog.py`, `zim_article.py` | **Parcial**: inventário e artigo pontual de ZIM, zimdump opcional; sem biblioteca Kiwix completa | Testar ZIM real e licença/conteúdos |
| AI Assistant — **Ollama + Qdrant** | `nexus/models/`, `nexus/knowledge/store.py`, `semantic_local.py` | **Parcial/equivalente nativo**: chat Ollama, PostgreSQL FTS, amostra temporária de oito trechos e índice persistente opt-in de até 256 vetores em PostgreSQL; Qdrant **não integrado** | Testar qualidade, RAM, troca de modelo e PostgreSQL real no notebook; corpus acima de 256 exige outra arquitetura |
| Education Platform — **Kolibri** | `nexus/study/offline_course.py`, `course_panel.py`, `knowledge/kolibri_export.py` | **Parcial**: cursos TXT/MD nativos, exercícios e progresso opcional PostgreSQL; apenas inspeção de metadados Kolibri, sem aulas Kolibri completas e sem multiusuário Kolibri | Exportação real, consentimento, segurança e execução sob demanda |
| Offline Maps — **ProtoMaps** | `nexus/maps/local.py`, `nexus/desktop/maps_panel.py` | **Parcial**: abrir mosaicos raster PMTiles com limites e navegação; sem renderizador vetorial, download de regiões ou busca de lugares | Arquivo raster real, uso de RAM, licenças e renderização |
| Data Tools — **CyberChef** | `nexus/tools/data_local.py`, interface de dados | **Parcial/equivalente nativo**: SHA-256/512, SHA3-256, BLAKE2b-256, Base32/64, hex, URL, ROT13 e JSON; receitas até oito passos, 64 KiB por etapa; **não é o CyberChef completo** | Testar fluxos reais e ampliar operações apenas com casos de uso definidos |
| Notes — **FlatNotes** | `nexus/notes/store.py`, painel de notas | **Equivalente nativo parcial**: Markdown CRUD e FTS no PostgreSQL; sem servidor/aplicativo FlatNotes | Experiência de edição, pesquisa e testes de escala |
| System Benchmark — Built-in | `nexus/platforms/benchmark.py` | **Parcial**: medição voluntária de SHA-256 e cópia em RAM, ~800 ms e 8 MiB de buffers; não é escore geral; sem disco, tags/ranking | Validar dados no hardware e decidir se IO/etiquetas oferecem valor sem desgaste ou telemetria |
| Supply Depot — Built-in | `nexus/desktop/apps_catalog.py`, `nexus/tools/local_container.py` | **Parcial/equivalente nativo**: catálogo restrito de aplicativos locais; execução voluntária de imagem OCI já instalada e identificada por SHA-256, somente com Podman local sem root/cgroups v2. Sem catálogo de instalação ou gerência persistente de contêineres | Testar Podman físico Ubuntu/Fedora, limites reais, falhas/cancelamento e política para eventual catálogo instalável |

## Política de desenvolvimento

O NEXUS CORE continua sendo **assistente geral local-first**, não uma
distribuição de serviços pesados. Kiwix, Kolibri, Qdrant e outros produtos
não serão iniciados, instalados, baixados ou sincronizados automaticamente.

- Não copiar código AGPL de terceiros para o projeto MIT.
- A integração futura de terceiros deve respeitar licenças, recursos de
  hardware e permissões. A referência conceitual não equivale ao código original.
- PostgreSQL permanece como banco único do núcleo; Qdrant futuro seria
  **opcional**, nunca uma dependência obrigatória para computadores fracos.
- A execução integral de plataformas externas que mantenham seus próprios
  bancos não foi incorporada ao núcleo; equivalentes nativos devem deixar
  explícita a cobertura parcial e manter o PostgreSQL como única persistência
  de dados do assistente.
- Funcionalidade de rede/comunidade/leaderboard nunca deve transmitir
  conteúdo ou pontuação sem consentimento explícito. Não há servidor
  comunitário no escopo atual.
- Fedora 43–45: a adaptação de instalação e diagnóstico está em desenvolvimento
  no PR #102. Não declarar compatibilidade total sem execução física Fedora
  e CI aprovada no SHA final.
