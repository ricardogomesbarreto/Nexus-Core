# Nexus Core 0.9.17 — uma janela por sessão

Esta etapa reforça o encerramento automático da v0.9.16. Se a janela já
estiver aberta, uma segunda tentativa de iniciar o desktop apresenta uma
mensagem e não executa outra instância. A segunda tentativa tampouco para
PostgreSQL e Ollama da primeira janela. O comando `nexus_core_session.sh stop`
adiará a parada enquanto a janela permanecer ativa.

A trava é um arquivo privado em `XDG_RUNTIME_DIR/nexus-core/desktop.lock`;
uma trava mal formada ou apontando para link simbólico é rejeitada. A
exclusão usa `flock` do Linux, incluído entre os requisitos verificados pelo
instalador Ubuntu, sem permitir autoinicialização dos serviços.
Quando a última janela fecha, a lógica da v0.9.16 continua tentando parar
apenas as instâncias que o Nexus iniciou e registrou, com autenticação
administrativa se necessário. O perfil `eco` permanece disponível e o banco
principal continua PostgreSQL local.

## Validação pendente no notebook

Abra uma janela com `NEXUS_RESOURCE_PROFILE=eco bash
scripts/nexus_core_session.sh desktop`. Em outro terminal, tente abrir outra
janela e executar `bash scripts/nexus_core_session.sh stop`. A primeira janela
deve continuar operando. Feche-a pelo botão **Desligar assistente** e confirme
com `bash scripts/nexus_core_session.sh status` que os serviços iniciados pelo
Nexus foram parados. Se `sudo` não estiver autenticado e não houver agente
gráfico para `pkexec`, a parada poderá exigir o comando manual `stop`.

Os testes automatizados exercitam a concorrência e o bloqueio entre
processos simulados; não comprovam a parada física no Ubuntu 26.04 Wayland,
a interface de senha nem o consumo real de RAM no notebook. Esta é uma
versão de código; não há tag estável até o aceite físico e os gates de
publicação.
