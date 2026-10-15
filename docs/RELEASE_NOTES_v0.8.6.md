# NEXUS CORE v0.8.6 — Ubuntu Maintenance Coordination

## Motivação e aderência ao roadmap

Após a auditoria documental da v0.8.5, o próximo passo prioritário é reduzir riscos de **concorrência entre instalação, atualização automática e recuperação offline**. O NEXUS CORE segue como aplicativo Linux desktop local, gratuito/open source, com Ubuntu 24.04 LTS como primeiro alvo, PostgreSQL e Ollama locais, interface Tk e identidade visual preservadas.

## Entregas de engenharia

- Lock de manutenção compartilhado `.maintenance.lock`, usando `fcntl.flock(LOCK_EX | LOCK_NB)` do kernel Linux. O lock é aberto em diretório privado e validado: usuário proprietário, arquivo regular, permissões não acessíveis por outros usuários, sem seguir symlinks e link count único.
- Recuperação `nexus-core-recover --rollback` (stdlib independente do venv), instalação inicial `scripts/install_linux.py`, preparação de release e ativação de atualização usam **o mesmo lock não bloqueante**. Quando outro processo está em manutenção, a operação atual falha explicitamente, sem executar `pip`, trocar `current` ou sobrescrever os apontadores.
- Para downloads disparados após consulta HTTPS, autorização de auto-update é **revalidada após obter o lock**. Isso impede que uma consulta de rede iniciada antes de um rollback reactive o staging depois da desativação.
- Comandos de diagnóstico e inspeção no launcher gerenciado (`--version`, `--help`, `--platform-check`, `--ubuntu-doctor`, `--ubuntu-preflight`, `--desktop-check`, `--voice-check`, `--vision-check`, `--devices-check` e `--devices-preview-stdin`) **não iniciam instalação, staging nem acesso ao GitHub por esse mecanismo**. O comando normal para abrir a aplicação preserva atualização opt-in.
- Após ativar com sucesso um novo venv, uma falha isolada ao excluir o marcador de staging **não exclui o venv selecionado**. Limpeza de venv por falha verifica o destino atual e nunca remove aquele apontado por `current`.
- A validação de `.current-next` ocorre antes de alterar o link `previous`, reduzindo estados inconsistentes em falhas de arquivo temporário.
- Testes de concorrência de locks, symlink malicioso, permissões abertas, rollback simultâneo, tentativa de staging/instalação concorrente e diagnósticos sem acesso a atualizações, preservando a suíte anterior.

## Limites reais

- `flock` coordena **os processos que usam o lock**; ele não impede que um usuário edite manualmente a pasta, não autentica outros processos da sessão gráfica e não substitui validações de integridade.
- O lock persiste como arquivo seguro; a exclusividade é liberada pelo sistema automaticamente quando o descritor fecha ou o processo morre. Sem varredura de processos externos ou serviços.
- `current` é trocado atomicamente como um link, mas `current` e `previous` **não formam uma transação de sistema de arquivos de duas entradas**. Uma falha excepcional no intervalo entre os links ainda requer recuperação/inspeção manual. Esta versão não promete atomicidade global, rollback de migrações PostgreSQL ou restaurar dados.
- O atualizador continua opt-in, HTTPS e digest SHA-256 de release; dependências Python transitivas não possuem lockfile integral e não há assinatura independente/attestation.
- O diagnóstico não certifica microfone, câmera, áudio, modelo Ollama carregado ou interação física X11. Testes reais Ubuntu Desktop permanecem pendentes.
- Não habilita instalação automática em Debian, Arch, Fedora ou SteamOS, nem altera a interface gráfica ou amplia autonomia/sensores.

## Validação e release

- Testar na CI Ubuntu 24.04/Python 3.12/PostgreSQL 16/Docker/Xvfb com suíte completa e testes específicos da v0.8.6.
- Esta versão é um PR **empilhado sobre #17 v0.8.5**, por sua vez dependente de #16 v0.8.4 e #15 v0.8.3. `main` contém código até v0.8.2; última release estável ainda **v0.7.2**.
- Nenhuma tag/release v0.8.6 deve ser produzida até integração ordenada, CI do commit exato em `main` e homologação real X11, Ubuntu, voz, visão, banco, Ollama e atualização/rollback. O workflow de publicação permanece desabilitado.
