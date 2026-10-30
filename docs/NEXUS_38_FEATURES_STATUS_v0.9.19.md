# NEXUS CORE — Matriz de cobertura dos 38 requisitos

**Referência técnica:** análise dos três ZIPs e do código v0.9.18; mudanças desta
branch v0.9.19. **Não significa que todos foram homologados.** Definições:
**existente** = código anterior, aceite físico pode estar pendente;
**novo** = código adicionado ao PR #102, CI final pendente;
**parcial** = cobre somente parte do requisito;
**pendente** = não entregue.

## VoiceStudio (10)

| Nº | Requisito | Situação | Observações |
|---|---|---|---|
| 1 | Síntese de voz | Existente | Piper/RHVoice/eSpeak local |
| 2 | Voz masculina/feminina | Existente | Seleção na janela e prévia 0.9.18 |
| 3 | Configurar velocidade/volume/características | Novo/parcial | Velocidade 75–125%, volume 50–150%, persistidos; características avançadas pendentes |
| 4 | Reconhecimento de fala | Existente | Vosk local |
| 5 | Conversação contínua | Existente, validar | Escuta em ciclos; testar hardware |
| 6 | Ler textos/documentos em voz alta | Parcial/novo | Leitura de trecho da Biblioteca; não PDF integral |
| 7 | Transcrição de áudio | Novo | WAV PCM 16 kHz ou MP3/OGG/FLAC/M4A via FFmpeg local opcional; sem persistência |
| 8 | Pausar/interromper/retomar | Novo/parcial | SIGSTOP/SIGCONT no subprocesso de fala do Nexus, opções no menu e leitura; áudio físico ainda não validado |
| 9 | Processamento local | Existente/novo | Sem upload ou servidor adicional |
| 10 | Otimização de áudio | Pendente de medição | Perfil eco existente, latência/fluidez física não comprovadas |

## Project NOMAD (14)

| Nº | Requisito | Situação | Observações |
|---|---|---|---|
| 1 | Biblioteca offline | Existente | PostgreSQL local |
| 2 | Enciclopédias locais | Novo/parcial | Inventário e leitura de artigo por URL via zimdump opcional; busca integral pendente |
| 3 | Biblioteca de documentos | Existente | Importação opt-in TXT/MD |
| 4 | Pesquisa em documentos | Existente | PostgreSQL FTS |
| 5 | Pesquisa com IA | Existente | Perguntas sobre trechos via Ollama local |
| 6 | Cursos offline | Parcial/novo | Catálogo de materiais de curso; execução Kolibri pendente |
| 7 | Mapas offline | Parcial | Prévia PMTiles anterior |
| 8 | Notas pessoais | Existente | Markdown e PostgreSQL |
| 9 | Conversão de formatos | Existente | Ferramentas de dados locais |
| 10 | Verificação SHA-256 | Existente | Ferramentas existentes |
| 11 | Busca semântica | Novo/parcial | Embeddings Ollama local sob autorização, amostra de oito trechos recentes; sem índice vetorial completo |
| 12 | Catálogo de ferramentas | Parcial | Ferramentas internas; plugin manager ainda não integrado |
| 13 | Avaliação de desempenho | Parcial | Monitor de recursos; benchmark de modelos pendente |
| 14 | Organização de conhecimento | Existente | Biblioteca, notas e cartões por fontes |

## DeepTutor (14)

| Nº | Requisito | Situação | Observações |
|---|---|---|---|
| 1 | Tutor com IA | Novo/parcial | Orientação por níveis no Ollama local e fontes; tutor adaptativo pendente |
| 2 | Explicações personalizadas | Novo/parcial | Níveis Iniciante/Intermediário/Avançado por sessão; memória do perfil pendente |
| 3 | Aprendizagem por etapas | Novo/parcial | Prompt orienta explicação em 3 etapas com fontes; progressão adaptativa pendente |
| 4 | Perguntas e respostas | Existente | Chat e pergunta aos documentos |
| 5 | Análise de documentos | Existente | TXT/MD, contexto textual local |
| 6 | Resumos educativos | Novo/parcial | Ação dedicada na Biblioteca com Ollama local e fonte; conferir resultado |
| 7 | Exercícios personalizados | Novo/parcial | Lacunas determinísticas a partir de fonte |
| 8 | Correção de exercícios | Novo/parcial | Literal, sem análise semântica |
| 9 | Resolução orientada | Parcial | Chat geral; passos pedagógicos específicos pendentes |
| 10 | Planos de estudo | Novo/parcial | Roteiro textual com trechos no Ollama; sem plano persistente/adaptativo |
| 11 | Acompanhamento de aprendizagem | Novo/parcial | Resultado opt-in PostgreSQL, sem domínio adaptativo |
| 12 | Conversação educacional | Novo/parcial | Ação guiada da Biblioteca; modo tutor contínuo pendente |
| 13 | Revisão de conteúdos | Existente/novo | Cartões e histórico de sessões |
| 14 | Aprendizagem multimodal | Parcial | Recursos gerais de imagem/voz; tutor integrado pendente |

## Regras transversais

- Não iniciar serviços extras, não copiar código AGPL no produto MIT.
- Não adicionar downloads ou reindexar documentos sem ação explícita.
- PostgreSQL continua banco único; dados não são enviados para servidores.
- Não promover PR para release estável sem CI do SHA final e aceite Ubuntu.
