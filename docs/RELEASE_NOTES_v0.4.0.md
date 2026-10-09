# Nexus Core v0.4.0 — Persistent Memory Foundation

## Entregas

- Memórias persistidas somente por comando explícito; histórico do chat continua efêmero.
- PostgreSQL local: schema idempotente de memórias e auditoria.
- Salvar, listar, pesquisar texto literal sem diferenciar maiúsculas/minúsculas, excluir por ID, exclusão total com confirmação, expiração e retenção de 1 a 365 dias (padrão de 90).
- CLI: `--memory-add`, `--memory-add-stdin`, `--memory-list`, `--memory-search`, `--memory-delete`, `--memory-clear --memory-confirm` e `--memory-status`.
- Limites de 1.200 caracteres por memória e até 100 resultados internos.
- Auditoria registra apenas metadados, contagens e IDs; sem conteúdo ou termos de busca.

## Privacidade e limites

O conteúdo fica em **texto claro** no PostgreSQL local; argumentos da CLI podem aparecer no histórico do terminal e na lista de processos. Não inserir segredos. Memórias não são automaticamente encaminhadas ao Ollama; a versão não oferece embeddings ou memória autônoma do agente. Homologação em hardware físico de voz não é coberta pela CI.

## Qualificação

A release depende da aprovação da CI do commit exato na branch `main`, em Linux com Python 3.12, PostgreSQL 16, Docker e Tk.
