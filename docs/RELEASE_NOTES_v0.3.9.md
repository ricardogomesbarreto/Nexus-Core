# Nexus Core v0.3.9 — Expanded Desktop Capabilities & Hardening

## Entregas

- Filesystem: leituras e listagens autorizadas usam descritores ancorados no diretório HOME e bloqueiam links simbólicos, inclusive quando alterados após uma checagem de autorização.
- Novo recurso `file_metadata`: consulta informações do arquivo sem ler seu conteúdo; passa pelo mesmo sistema de contratos e pelo SecurityGate.
- Terminal sandbox: monta snapshot temporário e privado de workspace, em vez de um caminho mutável. O snapshot bloqueia links simbólicos e arquivos especiais, limita a 512 entradas / 32 MB e evita que substituições do caminho exponham arquivos externos.
- Desktop Tk: janela aguarda workers antes de destruir o interpretador; controles não criam mais objetos Tk `Variable` sujeitos a finalização em threads erradas. A marca PNG do Nexus Core aparece no cabeçalho.
- CI: usa actions/checkout@v6 e setup-python@v6 (Node 24); execuções antigas de PR são canceladas para economizar minutos de Actions.
- Regressão: testes de troca de links simbólicos, diretórios renomeados, limite de snapshot e novo contrato de metadados.

## Limites de compatibilidade

- O workspace no Docker é um **snapshot somente leitura**, não um volume que atualiza durante a execução.
- Links simbólicos em diretórios e arquivos lidos são bloqueados de modo conservador.
- O PostgreSQL permanece obrigatório no loopback e o Ollama permanece o provider local.
- Hardware físico de voz (microfone/alto-falantes) não pode ser homologado pelos testes automatizados com dispositivos simulados.

## Critério de publicação

A tag `v0.3.9` deve ser publicada **apenas após** o CI do commit da `main` ser concluído com sucesso. A homologação física de áudio deve ser registrada separadamente e não é representada como concluída automaticamente.
