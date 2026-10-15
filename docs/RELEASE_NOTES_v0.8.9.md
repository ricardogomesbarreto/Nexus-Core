# NEXUS CORE v0.8.9 — Ubuntu Activation Journal & Offline Repair

## Objetivo e origem documental

Concluir uma melhoria concreta de integridade na linha `v0.8.x — Devices, Linux Setup & Updates`, após as verificações da v0.8.7 e o inicializador protegido da v0.8.8. O código prévio trocava os links `previous` e `current` por operações de filesystem separadas. Se o sistema encerrasse após modificar `previous`, mas antes de modificar `current`, o histórico da versão anterior poderia ficar incorreto. A v0.8.9 registra uma **intenção local de ativação** antes de modificar os links e oferece reparo controlado.

## Implementação

- Gerenciador `nexus/updates/manager.py`: antes de uma atualização que substitua uma versão existente, escreve `.activation-intent.json` com modo `0600`, via arquivo temporário, `fsync` e troca atômica. O registro contém somente nomes de versões `from`, `to` e `previous_before`, sem dados, credenciais, caminhos ou payloads de pacotes.
- O gerenciador **não** inicia nova ativação quando existe um registro anterior incompleto, nem sobrescreve um registro que foi transformado em symlink. A exclusividade da v0.8.6 (`flock`) continua obrigatória.
- O inicializador gerenciado da v0.8.8 recusa executar a versão enquanto há registro de ativação pendente: não presume que a interrupção possa ser reparada automaticamente.
- A ferramenta standalone `~/.local/bin/nexus-core-recover` da v0.8.5 é ampliada com:
  - `--activation-status`: consulta offline e somente leitura, sem iniciar banco, rede ou aplicativo; estados possíveis `clear`, `interrupted` e `invalid_record`.
  - `--repair-activation`: somente terminal interativo e confirmação exata **`REPARAR`**, sob o mesmo lock do instalador. Valida formato estrito, permissões de propriedade, nomes de versões, executáveis e os links `current`/`previous`. Desativa auto-update antes de modificar links e jamais altera `current` automaticamente.
- Quando a atualização não chegou a modificar `current`, o reparo restaura `previous` para o valor anterior ao início. Quando `current` já aponta à versão candidata completa, o reparo confirma que `previous` aponta à versão anterior correta. Em ambos os casos, elimina o registro **somente depois** de reconciliar os links.
- Testes simulando término durante a troca de `current`, falha após selecionar a versão candidata, primeiro upgrade sem `previous`, JSON adulterado/symlink, autorização ausente, operações concorrentes e comando standalone executado fora do checkout.

## Comandos locais após instalar a v0.8.9

```bash
# Os comandos não instalam pacotes nem se conectam à internet:
~/.local/bin/nexus-core-recover --activation-status

# Somente quando o status indicar interrupted e o usuário concordar:
~/.local/bin/nexus-core-recover --repair-activation
# Confirmar digitando REPARAR, em terminal interativo.
```

**Atenção:** o reparo não faz rollback de esquema PostgreSQL, não restaura memória, modelos, credenciais ou serviços, não faz download de versões, não elimina backups e não reinicia o aplicativo. Ele concilia apenas as referências entre versões **já existentes**, encerrando com segurança se encontrar um estado fora das combinações permitidas. O backup e a homologação física continuam obrigações separadas.

## Limitações explicitamente preservadas

- O registro de ativação **não transforma duas trocas de symlink em uma transação atômica conjunta**; é um mecanismo de detecção e reparo de interrupção, com autorização explícita. Uma queda durante o próprio reparo pode exigir repetição manual.
- A primeira instalação, quando ainda não existe `current`, não possui uma versão anterior para registrar. A proteção descrita se aplica a atualizações.
- Dependências de Python ainda não têm lockfile transitivo integral/assinatura independente. A verificação de código executável não é um atestado criptográfico completo.
- Um script `~/.local/bin/nexus-core` antigo, instalado antes desta versão, só recebe as novas proteções após reinstalação/atualização **explícita do inicializador**; a atualização de wheel não deve ser descrita como atualização automática desse arquivo externo ao venv.
- GitHub Actions com Xvfb não é hardware real. Ubuntu Desktop 24.04 LTS continua o primeiro alvo, com teste real X11, interface, PostgreSQL, Ollama, áudio e câmera pendente de aceite. Demais distribuições Linux não estão homologadas.

## Status e gates

Código da `main` até v0.8.2, última release publicada **v0.7.2**. Esta versão é desenvolvida como PR empilhado sobre **#20 — v0.8.8**, com dependências anteriores #15–#19. Não publicar tag/release até integração na ordem, CI no SHA final, validação física e revisão explícita. Workflow `release-v0.8.9.yml` permanece sem publicação por `if: ${{ false }}`.
