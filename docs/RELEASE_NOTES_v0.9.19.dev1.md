# NEXUS CORE v0.9.19.dev1 — revisão de desenvolvimento

Continua no PR #102 em Draft, sem tag ou release estável. Mantém o desktop
Linux local, Ollama sob demanda e PostgreSQL como único banco do assistente.

- Nova pergunta fundamentada no índice opcional: embedding local da pergunta,
  até três trechos indexados, resposta pelo Ollama local e fontes exibidas.
  Requer confirmação na janela; o CLI exige `--embedding-model`. Não executa
  ferramentas do agente nem grava a resposta.
- Sem vetores ou modelo compatível, não inicia o modelo de conversa. A rotina
  de busca textual e a amostra temporária de oito trechos seguem disponíveis.
- Auditoria da cobertura dos três ZIPs atualizada: os recursos nativos são
  parciais e os produtos externos não estão embutidos no NEXUS CORE.

A CI do SHA final e o aceite físico Ubuntu/Fedora ainda são obrigatórios antes
de promover a versão. Em particular, medir latência, RAM e swap durante a
pergunta, conferir se a resposta cita os trechos reais e exercitar voz,
câmera, recuperação e serviços no notebook.
