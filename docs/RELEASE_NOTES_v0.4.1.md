# Nexus Core v0.4.1 — Knowledge Base

## Entregas

- Biblioteca de documentos locais opt-in, com importação somente de `.txt` e `.md` UTF-8 autorizados pelo `PathSecurity`.
- Proteção de acesso por descritores de arquivo, sem seguir links simbólicos, com limite de 256 KiB por documento e máximo de 320 chunks.
- PostgreSQL local: deduplicação SHA-256, trechos de até 1.000 caracteres, índice de pesquisa full-text GIN e pesquisa literal parametrizada.
- Listagem, pesquisa e exclusão por ID, com cascata para os chunks, auditoria de metadados sem conteúdo e identificação do documento de origem.
- Comandos CLI `--knowledge-import`, `--knowledge-list`, `--knowledge-search`, `--knowledge-context`, `--knowledge-delete` e `--knowledge-limit`.
- Contexto combinado com memórias da v0.4.0 só mediante `--knowledge-context ... --knowledge-with-memory`; nada é enviado automaticamente ao Ollama.
- Testes de contratos, caminhos protegidos, resistência a symlinks e integração real com PostgreSQL 16.

## Limites

Documentos e metadados de origem são persistidos em texto claro no PostgreSQL local. A biblioteca é lexical, não vetorial; não suporta PDF, DOCX, OCR, ingestão de pastas ou indexação contínua. Dados não são enviados automaticamente para serviços externos ou ao agente. A voz com microfone físico não é homologada na CI.

## Critério de release

A tag deve apontar para o commit exato da `main` cujo workflow CI foi aprovado.
