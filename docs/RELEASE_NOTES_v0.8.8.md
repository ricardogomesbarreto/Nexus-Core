# NEXUS CORE v0.8.8 — Managed Launcher Integrity

## Objetivo

A v0.8.8 corrige a integridade da **entrada principal da instalação gerenciada no Ubuntu Desktop 24.04 LTS**. O instalador anterior mantinha um caminho `home` no script de entrada para localizar o Python, mas o processo `nexus.updates.launcher` podia recalcular o diretório da instalação a partir de `XDG_DATA_HOME`, cujo valor pode mudar entre a instalação e a execução. Além disso, antes de `execv`, a entrada precisava validar de forma restritiva o link `current` e o binário Python selecionado.

## Entregas

- Novo arquivo `nexus/updates/managed_entrypoint.py`, **autônomo e somente biblioteca padrão Python**. `scripts/install_linux.py` gera uma cópia em `~/.local/bin/nexus-core` com caminho gerenciado e credenciais opcionais fixados pelo próprio instalador; não depende do checkout GitHub nem importa código do ambiente virtual antes da validação.
- Na execução: recusa `root`; requer instalação/versões privadas pertencentes ao usuário; `current` precisa ser symlink para **um diretório imediato dentro de `versions`** chamado conforme `vMAJOR.MINOR.PATCH`; binário `bin/python` precisa ser arquivo regular, do mesmo usuário, executável, não gravável por outros e não symlink.
- Depois da validação, define `NEXUS_MANAGED_HOME` para o diretório fixado, ativa `NEXUS_RUNNING_MANAGED=1` e executa **`python -I -m nexus.updates.launcher`** do ambiente verificado. O `manager.managed_home()` lê o caminho fixado no processo gerenciado, sem depender de uma mudança posterior em `XDG_DATA_HOME`.
- Leitura opcional de senha local limitada a arquivo JSON regular sem symlink, pertencente ao usuário, com no máximo 4 KiB e modo privado; jamais imprime senha e preserva senha já definida no ambiente.
- Tanto instalação inicial quanto atualização gerenciada restringem as permissões de pasta da versão candidata a `0700` **antes de selecioná-la**, compatibilizando o caminho com a validação nova.
- Testes de symlink externo, executável adulterado, diretório público, senha insegura, preservação das opções de usuário e **execução real do script gerado por um Python do sistema sem checkout nem alteração dos modelos/serviços**.
- Nenhuma alteração da janela Tk, da marca Wine Red, das permissões para voz/visão/câmera, do PostgreSQL ou do Ollama.

## Limites

A checagem da propriedade dos arquivos e de symlinks reduz ataques triviais, mas não fornece assinatura criptográfica do ambiente completo nem impede alterações maliciosas feitas pelo **próprio usuário** durante a execução. O sistema ainda exige consentimento das ferramentas de automação X11 e nenhuma versão estável pode ser publicada sem homologação em máquina Ubuntu física.

A entrada não repara versões quebradas e não executa atualização quando se pede diagnóstico passivo; caso `current` esteja inválido, o usuário deve utilizar a ferramenta independente `nexus-core-recover --status`, introduzida na v0.8.5. Atualização/rollback continuam protegidos por lock da v0.8.6, e as verificações de pré-ativação da v0.8.7 permanecem obrigatórias.

## Validação e publicação

Executar CI completa Ubuntu 24.04 + Python 3.12 + PostgreSQL 16 + Docker + Xvfb, regressões do instalador/launcher e teste externo do script copiado. A v0.8.8 depende do PR **#19** (v0.8.7), depois dos PRs #15–#18. A `main` contém código até v0.8.2; última release pública: **v0.7.2**.

A publicação automática da v0.8.8 continuará desativada por um workflow separado com `if: ${{ false }}`. Integração ordenada, CI no commit final e testes reais de Ubuntu, voz, câmera, X11 e atualização/recuperação continuam necessários para a homologação estável.
