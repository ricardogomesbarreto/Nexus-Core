# NEXUS CORE v0.9.19 — Auditoria da suíte offline (8 capacidades)

**Auditoria realizada sobre o código de desenvolvimento do PR #102.**
Diferenças entre *implementação nativa equivalente*, *conector real* e
*funções de terceiros ainda não integradas* são intencionais e não devem
ser confundidas.

| Capability / Projeto original | Código existente | Estado real | Próximo gate |
|---|---|---|---|
| Information Library — **Kiwix** | `nexus/knowledge/offline_catalog.py`, `zim_article.py` | **Parcial**: inventário e artigo pontual de ZIM, zimdump opcional; sem biblioteca Kiwix completa | Testar ZIM real e licença/conteúdos |
| AI Assistant — **Ollama + Qdrant** | `nexus/models/`, `nexus/knowledge/store.py`, `semantic_local.py` | **Parcial**: chat Ollama, PostgreSQL local, pesquisa FTS e comparação de até oito trechos; Qdrant **não integrado** | Medir RAM, qualidade e avaliar índice vetorial opcional sem daemon obrigatório |
| Education Platform — **Kolibri** | `nexus/study/offline_course.py`, `course_panel.py`, `knowledge/kolibri_export.py` | **Parcial**: cursos TXT/MD nativos, exercícios e progresso opcional PostgreSQL; apenas inspeção de metadados Kolibri, sem aulas Kolibri completas e sem multiusuário Kolibri | Exportação real, consentimento, segurança e execução sob demanda |
| Offline Maps — **ProtoMaps** | `nexus/maps/local.py`, `nexus/desktop/maps_panel.py` | **Parcial**: abrir mosaicos raster PMTiles com limites e navegação; sem renderizador vetorial, download de regiões ou busca de lugares | Arquivo raster real, uso de RAM, licenças e renderização |
| Data Tools — **CyberChef** | `nexus/tools/data_local.py`, interface de dados | **Parcial/equivalente nativo**: SHA-256, Base64, hex e URL (até 64 KiB); **não é o CyberChef completo** | Outras operações locais aprovadas e testes de vetores |
| Notes — **FlatNotes** | `nexus/notes/store.py`, painel de notas | **Equivalente nativo parcial**: Markdown CRUD e FTS no PostgreSQL; sem servidor/aplicativo FlatNotes | Experiência de edição, pesquisa e testes de escala |
| System Benchmark — Built-in | `nexus/platforms/benchmark.py` | **Parcial**: SHA-256 local por 400 ms, não representa desempenho geral; sem Builder Tags/ranking | Benchmark CPU/RAM/IO calibrado e opt-in, sem telemetria externa |
| Supply Depot — Built-in | `nexus/tools/terminal.py` | **Não implementado**: Docker sandbox autorizado não é catálogo de aplicativos, nem provisiona contêineres BYO | Catálogo assinado/allowlisted, política de volumes e isolamento, opt-in |

## Política de desenvolvimento

O NEXUS CORE continua sendo **assistente geral local-first**, não uma
distribuição de serviços pesados. Kiwix, Kolibri, Qdrant e outros produtos
não serão iniciados, instalados, baixados ou sincronizados automaticamente.

- Não copiar código AGPL de terceiros para o projeto MIT.
- A integração futura de terceiros deve respeitar licenças, recursos de
  hardware e permissões. A referência conceitual não equivale ao código original.
- PostgreSQL permanece como banco único do núcleo; Qdrant futuro seria
  **opcional**, nunca uma dependência obrigatória para computadores fracos.
- Funcionalidade de rede/comunidade/leaderboard nunca deve transmitir
  conteúdo ou pontuação sem consentimento explícito. Não há servidor
  comunitário no escopo atual.
- Fedora 43–45: a adaptação de instalação e diagnóstico está em desenvolvimento
  no PR #102. Não declarar compatibilidade total sem execução física Fedora
  e CI aprovada no SHA final.
