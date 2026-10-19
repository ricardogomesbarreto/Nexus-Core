# NEXUS CORE — Capacidades offline e critérios de aceite v0.9.12

Revisão: 19/10/2026. Anexo examinado: `project-nomad-main.zip` (755 entradas, CRC válido).
Origem: servidor AdonisJS/Node/React, orquestrador de serviços Docker,
licença Apache-2.0. **Não foi copiada a implementação nem iniciados
contêineres**. O produto resultante conserva identidade NEXUS CORE,
desktop local, PostgreSQL como banco único, permissão por operação
e serviços sob demanda.

## Matriz real — oito capacidades do ZIP

| Capacidade observada | Estado NEXUS CORE nesta etapa | Próxima implementação |
| --- | --- | --- |
| Biblioteca Kiwix/ZIM | Diagnóstico passivo da presença de `kiwix-serve`; sem leitor nem indexação ZIM | Navegação ZIM autorizada, catálogos e download opcional com verificação de tamanho, licença e origem |
| Assistente Ollama + Qdrant | Ollama, documentos TXT/MD e busca textual **PostgreSQL** já existem; vetor **não** existe | Semântica opcional com pgvector **no PostgreSQL** (não tornar Qdrant obrigatório), ingestão consentida |
| Educação Kolibri | Detecção passiva do executável, sem servidor | Adapter opcional para cursos/progresso com autorização e dados isolados |
| Mapas ProtoMaps | Detecção passiva de utilitário `pmtiles`; sem mapa pronto | Leitor de PMTiles em tela local, pesquisa, dados regionais opt-in sem rede |
| Ferramentas CyberChef | **Implementado subset original:** SHA-256, Base64, hexadecimal, URL percent-encoding e ROT13; até 8 KiB | Receitas tipadas adicionais após revisão; Base64/ROT13 não são criptografia |
| Notas FlatNotes | **Implementado:** criação de arquivo `.md` privado `0600` via SecurityGate, saída nova; leitura/lista já existiam | Edição versionada, tags e busca no PostgreSQL, sem rodar FlatNotes |
| Benchmark | Diagnóstico existente de RAM/CPU e recursos local; **sem score ou leaderboard** | Ensaio de desempenho opt-in, métricas reprodutíveis, ranking remoto jamais padrão |
| Catálogo Supply Depot | Somente detecção `docker` no PATH; **sem executar Docker, socket ou instalação** | Catálogo aprovado, imagens fixadas por digest, verificação de licenças e volumes e confirmação antes de criar contêiner |

A presença de um executável no PATH **não** prova execução, integridade,
homologação ou disponibilidade dos serviços. As integrações opcionais
não devem aumentar RAM ou consumo no boot. Todos os downloads,
instalações, serviços e recursos sensíveis exigem escolhas explícitas
e limites próprios. Não montar o socket Docker no assistente.

## Implementado no código do NEXUS CORE

- `nexus/tools/offline_workspace.py`: notas locais protegidas, operações
  determinísticas de dados e inventário passivo.
- `nexus/agent/planner.py`: frases portuguesas explícitas no turno atual,
  sem autorização por histórico ou parâmetros deduzidos pelo modelo.
- `nexus/desktop/window.py`: guia rápido com diagnóstico local sem rede.
- `nexus/voice/local.py`: correção de alinhamento de amostras PCM de
  16 bits nos limites arbitrários dos chunks devolvidos pelo Linux.
- Testes de segurança, limites, conteúdo original intacto e
  comportamento sem inicialização de contêineres.

Exemplos de conversa (substitua o HOME fictício pelo real):

    Crie uma nota com o texto "Planejar a semana" em /home/usuario/Notas/semana.md
    Calcule SHA-256 do texto "exemplo"
    Codifique em base64 o texto "ação"
    Decodifique base64 "YQ=="
    Codifique em hexadecimal o texto "abc"

A pasta de notas precisa existir; criá-la também exige autorização.
Dados privados escritos no chat podem constar no histórico local
do usuário; não inserir senhas.

## G0 da release estável 0.9.12 continua pendente

O último registro no Ubuntu 26.04 apresentava **11 PASSOU / 10 PENDENTE**.
A escuta contínua havia falhado, e análise de câmera demorou cerca
de 119 s e leitura da resposta 23 s em uma sessão anterior.
A correção de amostras PCM elimina uma causa possível de corrupção,
**não equivale** a duas conversas reais homologadas.

1. Microfone: duas perguntas distintas consecutivas na GUI, fala audível,
   pausa/retomada, teste real PipeWire/ALSA e confirmação por voz/texto/botões.
2. Câmera e tela: consentimento por captura, prévia e resposta coerente,
   cancelamento e tempo/consumo medidos.
3. Modelo eco: RAM/swap, `ollama ps`, carga/descarga real e
   `nexus-core --resource-check` antes/depois.
4. Serviços: PostgreSQL/Ollama preexistentes vs. iniciados pelo NEXUS,
   sem autostart e sem parar serviços de outros programas.
5. Interface: foco, histórico, layout Wayland e ações X11 somente no X11.
6. Arquivos: fidelidade, origem intacta, destinos novos e smoke real
   das ferramentas opcionais confiáveis.

Os recursos avançados do ZIP (servidor de biblioteca, educação, mapas,
RAG vetorial, benchmarking com pontuação e instalação de contêineres)
**ainda não estão disponíveis integralmente** na aplicação.

### Sequência sugerida

P1: resolver/medir escuta, câmera, visão e consumo físico e liberar gate G0.
P2: indexador local ZIM, leitor de cursos como serviço opcional e
notas com edição segura por versão.
P3: mapas PMTiles e busca por embeddings opcionais em PostgreSQL.
P4: receitas de dados, benchmark reproduzível e catálogo local
de apps com isolamento e aprovação explícita.

O código após a tag `v0.9.12-rc.3` demanda CI própria; tags
candidatas são imutáveis. Nenhuma release estável pode ser
declarada sem o aceite físico.
