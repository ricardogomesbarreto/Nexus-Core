# NEXUS CORE v0.8.7 — Ubuntu Pre-Activation Validation

## Objetivo

O marco v0.8.7 reforça a instalação e a atualização **antes da seleção de uma nova versão** no Ubuntu Desktop 24.04 LTS. A v0.8.6 já coordena a manutenção via `flock`; agora um ambiente Python recém-instalado também precisa passar por uma validação mínima, determinística, limitada e **sem inicialização do assistente completo**.

O NEXUS CORE continua aplicativo desktop Linux **local, gratuito, open source**, com PostgreSQL local, Ollama local, voz/visão autorizadas e interface Tk/identidade Nexus Line sem alteração. Outras distribuições continuam fora do instalador homologado.

## Entregas técnicas

- Novo módulo `nexus/updates/verification.py` centraliza validações sem efeitos colaterais da instalação e da atualização gerenciada.
- Antes de atualizar `current` ou `previous`, o atualizador executa, **no novo ambiente Python**:
  1. `python -I -m pip check`: verifica conflitos das dependências instaladas.
  2. `python -I -m nexus.main --version`: exige versão idêntica à release verificada.
  3. `python -I -m nexus.main --platform-check`: exige JSON de diagnóstico **somente leitura**, `mode=passive`, `changes_performed=false`, Ubuntu 24.04 LTS, Python suportado e nenhuma ferramenta essencial ausente.
- A flag Python `-I` remove `PYTHONPATH`/importação implícita do checkout, reduzindo o risco de validar por engano o código-fonte ou outro pacote fora do venv.
- Timeout de 30/20/20 s, saída de erro descartada, saída de diagnóstico validada/limitada; mensagens de erro sanitizadas, sem expor argumentos de configuração sensíveis.
- Se qualquer etapa falhar, a versão anteriormente selecionada permanece ativa; a instalação candidata não é escolhida. O gerenciador elimina somente a candidata não selecionada.
- O instalador Ubuntu também aplica `pip check`, versão e diagnóstico passivo **antes** de ativar o ambiente novo.
- Testes de regressão e novos testes de falha por versão falsa, saída inválida, dependências conflitantes, relatório com efeitos colaterais, Python desatualizado, pacote essencial ausente, instalação em outra distro e subprocesso encerrado com erro.

## Limites

Esta é **validação de pré-ativação**, não uma execução completa do assistente. `pip check` não garante integridade criptográfica de todas as dependências, e o diagnóstico não inicia PostgreSQL/Ollama, não faz inferência, não testa persistência, áudio, microfone, câmera, teclado, GPU, permissões reais ou comportamento de uma janela X11. A atualização continua exigindo wheel oficial com hash verificado; falta assinatura independente e lockfile integral com hashes de dependências.

A troca de links `current` e `previous` ainda não constitui transação atômica conjunta, apesar de coordenação por `flock`. Não desfaz migrações nem altera dados PostgreSQL. É necessária homologação real em Ubuntu Desktop 24.04 LTS antes de qualquer release estável.

## Evidência e política de publicação

- CI com `ubuntu-24.04`, Python 3.12, PostgreSQL 16, Docker e Xvfb.
- Versão v0.8.7 criada em PR empilhado **sobre #18 (v0.8.6)**, após #17, #16 e #15. `main` ainda contém código até 0.8.2; última release pública v0.7.2.
- Publicação automática desativada: workflow da v0.8.7 requer disparo manual mas possui `if: ${{ false }}`, impossível publicar enquanto esse bloqueio não for removido por alteração separada autorizada com aceite físico documentado.
- Sem alterar visual, autoconfirmações, dispositivos, modelos e outros produtos NEXUS.
