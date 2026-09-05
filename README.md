# Nexus Core

Assistente pessoal de inteligência artificial **local-first, multimodal, modular, seguro e orientado a agentes**.

> **Versão estável atual:** `v0.2.2 — Continuous Connectivity Monitoring`
> **Próxima versão planejada:** `v0.2.3 — Automatic DEGRADED Runtime Detection`
> **Status:** Development
> **Test baseline:** `134 passed`

---

## Visão geral

O **Nexus Core** é a infraestrutura central de um assistente pessoal de inteligência artificial projetado para operar prioritariamente de forma local, preservando privacidade, controle operacional, segurança e independência de serviços externos.

O projeto é desenvolvido incrementalmente.

Antes da integração de modelos de inteligência artificial, memória, voz, visão, automação ou interfaces multimodais, o Nexus Core estabelece primeiro uma fundação sólida de:

* segurança;
* autorização;
* execução controlada;
* runtime;
* observabilidade;
* conectividade;
* lifecycle;
* testabilidade;
* governança;
* rastreabilidade.

O objetivo de longo prazo é construir um assistente capaz de oferecer:

* conversação por texto e voz;
* operação offline e online;
* modelos de IA locais;
* integração opcional com provedores online;
* memória persistente;
* Knowledge Base;
* visão computacional;
* interpretação de tela;
* automação controlada do desktop;
* desenvolvimento de software assistido;
* leitura e análise de arquivos;
* pesquisa web;
* geração multimídia;
* arquitetura orientada a agentes;
* integração com Arduino e ESP32;
* comunicação com dispositivos externos;
* arquitetura distribuída entre computadores e dispositivos;
* interface gráfica multimodal.

O Nexus Core **não** é projetado como um LLM com acesso irrestrito ao computador.

A arquitetura estabelece fronteiras explícitas entre:

```text
INTELIGÊNCIA
DECISÃO
AUTORIZAÇÃO
EXECUÇÃO
```

---

# Princípios de engenharia

O desenvolvimento do Nexus Core segue princípios estruturais que devem permanecer válidos durante toda a evolução do projeto.

* **Open Source**
* **Local First**
* **Security First**
* **Privacy First**
* **Least Privilege**
* **Defense in Depth**
* **Modularidade**
* **Testabilidade**
* **Observabilidade**
* **Auditabilidade**
* **Determinismo quando aplicável**
* **Isolamento de falhas**
* **Contratos explícitos entre componentes**
* **Evolução incremental**
* **Compatibilidade controlada**
* **Regressão automatizada**
* **Separação de responsabilidades**
* **Fail-safe defaults**

Segurança não é tratada como uma funcionalidade adicionada posteriormente.

Ela faz parte da fundação arquitetural do Nexus Core.

---

# Estado atual

A versão `v0.2.2` consolida o **monitoramento contínuo de conectividade** do Nexus Core, permitindo transições automáticas e controladas entre `ONLINE` e `OFFLINE`.

O estado inicial continua sendo determinado durante `NexusApplication.initialize()`.

Quando:

```text
offline_mode = False
```

um `ConnectivityMonitor` é iniciado e passa a verificar periodicamente a conectividade externa.

Quando ocorre uma mudança efetiva de conectividade, o estado de runtime é atualizado de maneira controlada e os eventos correspondentes são publicados.

Atualmente o projeto possui:

* Núcleo da aplicação
* Configuração tipada
* Logging estruturado
* Banco de dados SQLite
* EventBus
* Catálogo de eventos
* Health Status
* Health Check
* Connectivity Manager
* Connectivity Monitor
* Runtime Mode
* Runtime State Controller
* Runtime snapshots
* Health runtime snapshots
* Estados `ONLINE`, `OFFLINE` e `DEGRADED`
* Arquitetura modular de ferramentas
* Tool Registry
* Tool Executor
* Security Gate
* Política de risco
* Permissões por ferramenta
* Segurança de caminhos
* Audit Log
* Ferramentas seguras de filesystem
* Terminal Sandbox isolado com Docker
* Painel de status
* Lifecycle controlado da aplicação
* Suíte automatizada de testes

O valor `DEGRADED` já existe no domínio de runtime, mas sua determinação automática ainda **não** faz parte da implementação atual.

---

## Baseline atual

```text
Version:       v0.2.2
Tests:         134 passed
Runtime:       Python 3.12
Database:      SQLite
Sandbox:       Docker
Branch model:  main
Status:        DEVELOPMENT
```

---

# Arquitetura atual

```text
NEXUS CORE
│
└── NexusApplication
    │
    ├── Configuration
    │
    ├── Logger
    │
    ├── Database
    │   └── SQLite
    │
    ├── EventBus
    │   └── NexusEvent
    │
    ├── ConnectivityManager
    │   └── Point-in-time connectivity check
    │
    ├── ConnectivityMonitor
    │   └── Nexus-ConnectivityMonitor
    │       ├── Periodic polling
    │       ├── Transition detection
    │       ├── Failure containment
    │       └── Graceful shutdown
    │
    ├── RuntimeStateController
    │   ├── Authoritative runtime state
    │   ├── Atomic transitions
    │   └── Immutable snapshots
    │
    ├── HealthStatus
    │   └── Runtime observability projection
    │
    ├── SecurityGate
    │   ├── Risk Policy
    │   ├── Tool Permissions
    │   ├── Path Security
    │   └── Audit Log
    │
    └── Tool System
        ├── NexusTool
        ├── ToolResult
        ├── ToolRegistry
        ├── ToolExecutor
        ├── Filesystem Tools
        └── TerminalSandboxTool
            └── Docker
```

O `RuntimeStateController` é a **fonte autoritativa** do estado operacional.

O `HealthStatus` mantém uma projeção voltada à observabilidade.

Quando componentes concorrentes precisam observar:

```text
network_online
runtime_mode
runtime_reason
```

como uma única unidade lógica, devem utilizar:

```python
health.runtime_snapshot()
```

O `ConnectivityMonitor` coordena verificações periódicas, detecção de transições e atualização do estado de runtime.

---

# Fluxo de autoridade

Uma das regras fundamentais do Nexus Core é que a futura camada de inteligência artificial **não terá autoridade direta sobre o sistema operacional**.

O modelo arquitetural é:

```text
INTELIGÊNCIA
     │
     ▼
PLANEJAMENTO / DECISÃO
     │
     ▼
TOOL REGISTRY
     │
     ▼
TOOL EXECUTOR
     │
     ▼
SECURITY GATE
     │
     ├── autorizado
     │      │
     │      ▼
     │    TOOL
     │      │
     │      ▼
     │  EXECUÇÃO CONTROLADA
     │
     └── negado
            │
            ▼
         BLOQUEIO
```

O modelo de IA poderá **propor** ações.

O `ToolExecutor` será responsável por coordenar sua execução.

O `SecurityGate` será responsável por determinar se a operação é permitida.

O modelo nunca receberá autoridade arbitrária sobre o host.

---

# NexusApplication

`NexusApplication` coordena o ciclo de vida dos principais componentes do Nexus Core.

Durante a inicialização atual, a aplicação:

1. Inicializa o sistema de logging.
2. Inicializa o banco SQLite.
3. Inicializa o `EventBus`.
4. Inicializa o `SecurityGate`.
5. Inicializa o `ToolRegistry`.
6. Registra as ferramentas disponíveis.
7. Inicializa o `ToolExecutor`.
8. Inicializa o `ConnectivityManager`.
9. Verifica a política `offline_mode`.
10. Quando permitido, executa uma verificação inicial de conectividade.
11. Determina o modo inicial de runtime.
12. Inicializa o `RuntimeStateController`.
13. Atualiza o `HealthStatus`.
14. Publica os eventos iniciais correspondentes.
15. Publica `SYSTEM_START`.
16. Registra a inicialização no banco.
17. Quando `offline_mode=False`, cria e inicia o `ConnectivityMonitor`.

---

## Contrato de inicialização

`initialize()` possui semântica **one-shot**.

Depois de uma inicialização bem-sucedida:

```python
app.initialize()
```

uma segunda chamada:

```python
app.initialize()
```

levanta:

```text
RuntimeError
```

Isso evita:

* repetição de side effects;
* duplicação de eventos;
* reinicialização indevida de componentes;
* criação acidental de múltiplas workers;
* vazamento de threads.

---

## Contrato de shutdown

`shutdown()` é idempotente.

Chamadas repetidas após um shutdown bem-sucedido não repetem:

* `SYSTEM_STOP`;
* fechamento do banco;
* encerramento da worker;
* side effects de finalização.

Quando existe um monitor ativo, a ordem é:

```text
ConnectivityMonitor.stop()
        │
        ▼
SYSTEM_STOP
        │
        ▼
Database.close()
        │
        ▼
shutdown concluído
```

A worker de conectividade é encerrada **antes** de `SYSTEM_STOP`.

Se `ConnectivityMonitor.stop()` não conseguir finalizar a worker dentro do timeout definido, o shutdown não é marcado falsamente como concluído.

---

## Entrypoint principal

O fluxo principal utiliza:

```python
try:
    ...
finally:
    app.shutdown()
```

depois que a inicialização foi concluída com sucesso.

Isso garante liberação dos recursos mesmo quando ocorre uma exceção durante o restante da execução.

---

# Configuração

A configuração principal é representada por uma estrutura tipada.

Entre os parâmetros atuais:

```python
offline_mode: bool = True
connectivity_monitor_interval: float = 30.0
```

---

## `offline_mode = True`

Força o runtime para:

```text
OFFLINE
```

independentemente da disponibilidade real da Internet.

Nesse modo:

* nenhuma verificação periódica é iniciada;
* nenhum `ConnectivityMonitor` é criado;
* `connectivity_monitor` permanece `None`;
* não existe polling externo em background;
* o comportamento é determinístico;
* a operação local permanece soberana.

---

## `offline_mode = False`

Permite que o Nexus:

1. verifique a conectividade externa;
2. determine `ONLINE` ou `OFFLINE`;
3. estabeleça o estado inicial;
4. publique os eventos iniciais;
5. inicie o monitor de conectividade;
6. detecte mudanças posteriores automaticamente.

---

## Intervalo de monitoramento

O intervalo operacional padrão é:

```text
30.0 segundos
```

O `ConnectivityMonitor` rejeita intervalos menores ou iguais a zero.

---

# Connectivity Manager

O `ConnectivityManager` possui uma responsabilidade limitada e explícita:

> realizar uma verificação pontual da conectividade externa.

Fluxo:

```text
ConnectivityManager.check()
        │
        ▼
ConnectivityStatus
        ├── online
        ├── endpoint
        └── latency_ms
```

O componente não possui worker própria.

Ele não decide políticas de runtime e não mantém o estado autoritativo.

---

## ConnectivityStatus

O resultado da verificação possui:

```python
online: bool
latency_ms: float | None
endpoint: str | None
```

Atualmente:

```text
latency_ms
```

faz parte do contrato estrutural, mas não existe medição ativa de latência.

Portanto, sua presença não deve ser interpretada como implementação de benchmarking de rede.

---

## Falhas de conectividade

Falhas de rede ou I/O durante a verificação são interpretadas como indisponibilidade externa.

Uma falha em comunicação não concede qualquer autoridade adicional ao sistema.

---

# Connectivity Monitor

A `v0.2.2` introduz o `ConnectivityMonitor`.

Sua responsabilidade é transformar verificações pontuais em monitoramento periódico controlado.

O componente recebe explicitamente:

```text
ConnectivityManager
RuntimeStateController
EventBus
HealthStatus
poll interval
logger
```

---

## Worker

O monitor utiliza uma thread dedicada:

```text
Name:    Nexus-ConnectivityMonitor
Daemon:  True
```

Implementação baseada na biblioteca padrão do Python:

```python
threading.Thread
threading.Event
threading.RLock
```

Nenhuma dependência externa foi adicionada para essa funcionalidade.

---

## `daemon=True`

`daemon=True` funciona apenas como fallback no encerramento do processo.

Ele **não** é a estratégia normal de shutdown.

A estratégia oficial é:

```text
stop event
    │
    ▼
join
    │
    ▼
worker encerrada
```

---

## Loop de monitoramento

O loop utiliza:

```python
stop_event.wait(interval)
```

em vez de:

```python
time.sleep(interval)
```

Isso permite que o shutdown interrompa a espera imediatamente.

---

## `start()`

`start()` é idempotente enquanto a worker existente estiver viva.

Chamadas repetidas não criam múltiplas threads concorrentes para a mesma instância.

---

## `stop()`

`stop()`:

1. sinaliza o `stop_event`;
2. aguarda a worker através de `join()`;
3. respeita timeout;
4. levanta `TimeoutError` se a worker permanecer viva.

Também é seguro chamar `stop()`:

* antes de `start()`;
* repetidamente após o encerramento.

---

## `is_running`

A propriedade:

```python
monitor.is_running
```

permite observar se a worker associada continua viva.

---

# Detecção de transições

Cada ciclo de monitoramento executa:

```text
ConnectivityManager.check()
        │
        ▼
ConnectivityStatus
```

O modo desejado é derivado diretamente:

```text
online=True  → ONLINE
online=False → OFFLINE
```

A atualização é realizada através de uma transição condicional atômica no `RuntimeStateController`.

---

## Estado inalterado

Se o estado observado for igual ao estado atual:

```text
nenhuma transição
nenhum NETWORK_*
nenhum RUNTIME_MODE_CHANGED
```

Isso evita:

* event flooding;
* timestamps artificiais;
* side effects repetidos;
* atualizações sem mudança real de estado.

---

## Mudança efetiva

Quando existe mudança:

```text
ConnectivityStatus
        │
        ▼
RuntimeStateController
        │
        ▼
HealthStatus
        │
        ▼
NETWORK_ONLINE / NETWORK_OFFLINE
        │
        ▼
RUNTIME_MODE_CHANGED
```

---

# Runtime State Controller

O `RuntimeStateController` é a fonte autoritativa do estado operacional do Nexus Core.

Ele mantém:

```text
mode
reason
changed_at
```

---

## Thread safety

O controlador utiliza:

```python
threading.RLock
```

para proteger seu estado interno.

Leituras individuais de:

```python
mode
reason
changed_at
```

são sincronizadas.

---

## Snapshot

Para leitura consistente do conjunto de estado:

```python
controller.snapshot()
```

retorna um:

```text
RuntimeStateSnapshot
```

imutável.

Campos:

```text
mode
reason
changed_at
```

---

## `transition()`

Preserva o contrato histórico da `v0.2.1`.

Uma transição válida:

```python
controller.transition(
    RuntimeMode.ONLINE,
    "Conectividade externa disponível",
)
```

retorna:

```text
True
```

Transição para o mesmo estado:

```text
ValueError
```

Transição inválida:

```text
ValueError
```

---

## `transition_if_changed()`

A `v0.2.2` adiciona transições condicionais.

Se o estado já for igual ao desejado:

```text
False
```

sem alterar:

```text
mode
reason
changed_at
```

Quando existe mudança:

```text
True
```

---

## `transition_if_changed_result()`

Para consumidores concorrentes, existe:

```python
transition_if_changed_result()
```

que realiza sob o mesmo lock:

```text
comparação
transição
captura do resultado
```

Retorna:

```text
RuntimeTransitionResult
```

com:

```text
changed
mode
reason
changed_at
```

Isso elimina uma janela de corrida entre:

```text
alterar estado
        │
        ▼
liberar lock
        │
        ▼
ler snapshot
```

---

# Runtime Modes

Os modos definidos atualmente são:

```text
ONLINE
OFFLINE
DEGRADED
```

---

## ONLINE

Representa conectividade externa disponível.

Não significa:

* autorização;
* confiança;
* permissão para executar ferramentas;
* permissão para acessar serviços arbitrários;
* elevação de privilégio.

---

## OFFLINE

Representa indisponibilidade externa ou operação offline forçada.

O Nexus Core foi projetado para preservar sua capacidade local mesmo nesse estado.

---

## DEGRADED

Existe atualmente no modelo de domínio.

Entretanto:

```text
DEGRADED
```

ainda **não possui determinação automática**.

A implementação dessa lógica está planejada para:

```text
v0.2.3
```

---

# Health Status

`HealthStatus` representa o estado de saúde e observabilidade dos componentes.

Entre os campos atuais estão:

```text
core
configuration
database
logger
event_bus
security_gate
tool_registry
terminal_sandbox
network_online
runtime_mode
runtime_reason
```

---

## Readiness

A propriedade:

```python
health.ready
```

representa a disponibilidade estrutural dos componentes necessários ao funcionamento local.

Conectividade externa **não determina readiness**.

Portanto:

```text
Network OFFLINE
```

não implica necessariamente:

```text
Nexus unavailable
```

Essa distinção é fundamental para a arquitetura local-first.

---

## Runtime observability

Os campos de runtime do `HealthStatus` são uma projeção do estado operacional.

A fonte autoritativa continua sendo:

```text
RuntimeStateController
```

---

## Atualização atômica

Componentes concorrentes devem utilizar:

```python
health.update_runtime(
    network_online=...,
    runtime_mode=...,
    runtime_reason=...,
)
```

para atualizar os três campos como uma unidade lógica.

---

## Runtime snapshot

Para leitura consistente:

```python
health.runtime_snapshot()
```

retorna:

```text
HealthRuntimeSnapshot
```

imutável.

Campos:

```text
network_online
runtime_mode
runtime_reason
```

O entrypoint principal utiliza esse snapshot para evitar leituras concorrentes incoerentes.

---

# Event Architecture

O Nexus Core utiliza um `EventBus` interno para comunicação desacoplada entre componentes.

Eventos são representados por:

```text
NexusEvent
```

---

## Eventos relevantes de runtime

```text
NETWORK_ONLINE
NETWORK_OFFLINE
RUNTIME_MODE_CHANGED
```

---

# Semântica de inicialização

Durante a inicialização em modo automático:

```text
offline_mode=False
```

o Nexus executa uma verificação inicial.

Exemplo online:

```text
NETWORK_ONLINE
RUNTIME_MODE_CHANGED(ONLINE)
SYSTEM_START
```

Exemplo offline:

```text
NETWORK_OFFLINE
RUNTIME_MODE_CHANGED(OFFLINE)
SYSTEM_START
```

O evento inicial `RUNTIME_MODE_CHANGED` representa o estabelecimento inicial do estado de runtime.

Esse contrato já existia na `v0.2.1` e foi preservado.

---

# Semântica de monitoramento — v0.2.2

Após a inicialização, o monitor somente publica novos eventos quando ocorre uma mudança efetiva.

Exemplo:

```text
Inicialização
OFFLINE
  ├── NETWORK_OFFLINE
  └── RUNTIME_MODE_CHANGED(OFFLINE)

Primeiro polling
OFFLINE
  └── nenhum evento

Polling posterior
ONLINE
  ├── NETWORK_ONLINE
  └── RUNTIME_MODE_CHANGED(ONLINE)

Polling seguinte
ONLINE
  └── nenhum evento
```

Isso preserva:

* determinismo;
* auditabilidade;
* baixo ruído;
* ausência de event flooding.

---

# Falhas em subscribers

O `EventBus` preserva o comportamento de propagação de exceções de subscribers.

Entretanto, a `v0.2.2` endurece o fluxo de eventos de transição.

Se um subscriber de:

```text
NETWORK_ONLINE
```

ou:

```text
NETWORK_OFFLINE
```

falhar, o monitor ainda tenta publicar:

```text
RUNTIME_MODE_CHANGED
```

para a mesma transição.

A falha do primeiro evento continua visível ao chamador de:

```python
check_once()
```

---

## Falha nos dois eventos

Se a publicação do evento de rede e a publicação de `RUNTIME_MODE_CHANGED` falharem:

* o primeiro erro permanece como erro principal;
* a falha adicional é registrada no logger.

---

# Isolamento de falhas da worker

O boundary da worker protege o loop contra exceções inesperadas.

Fluxo:

```text
cycle
  │
  ├── success
  │      └── continue
  │
  └── exception
         │
         ├── log
         └── continue
```

Portanto, uma falha inesperada em um ciclo não encerra permanentemente o monitor.

Isso inclui falhas originadas por subscribers durante publicação de eventos.

---

# Security Gate

O `SecurityGate` é a principal fronteira de autorização operacional do Nexus Core.

Ferramentas não devem executar ações sensíveis apenas porque:

* o LLM pediu;
* um arquivo pediu;
* uma página web pediu;
* uma imagem contém instruções;
* um PDF contém instruções;
* uma mensagem externa contém instruções.

Conteúdo externo é tratado como **não confiável**.

---

# Prompt Injection

Prompt injection não representa autoridade.

Conteúdo proveniente de:

* páginas web;
* PDFs;
* documentos;
* imagens;
* mensagens;
* memória externa;
* arquivos;
* resultados de ferramentas;

deve ser tratado como dado.

Não como autorização.

---

# Tool Architecture

O sistema de ferramentas é estruturado em camadas.

```text
Future Model Layer
        │
        ▼
Planner / Agent
        │
        ▼
ToolRegistry
        │
        ▼
ToolExecutor
        │
        ▼
SecurityGate
        │
        ▼
Tool
```

---

## Tool Registry

Responsável por registrar e localizar ferramentas disponíveis.

O modelo não recebe acesso arbitrário ao sistema apenas por conhecer o nome de uma ferramenta.

---

## Tool Executor

Coordena a execução das ferramentas.

Ele funciona como intermediário entre:

```text
intenção
autorização
execução
resultado
```

---

## Security boundary

O `ToolExecutor` deve respeitar as decisões do `SecurityGate`.

A arquitetura não permite que o modelo simplesmente contorne essa camada.

---

# Filesystem Security

Operações de filesystem são sujeitas a validações explícitas.

Entre os objetivos da arquitetura:

* evitar traversal;
* restringir áreas permitidas;
* validar caminhos;
* impedir acesso acidental a regiões sensíveis;
* preservar least privilege.

---

# Terminal Sandbox

O Nexus Core já possui uma ferramenta de terminal executada em sandbox Docker.

Objetivo:

```text
comando
  │
  ▼
ToolExecutor
  │
  ▼
SecurityGate
  │
  ▼
TerminalSandboxTool
  │
  ▼
Docker
```

A sandbox reduz a exposição direta do host.

---

## Limitação de segurança do Docker

O usuário do sistema atualmente pertence ao grupo:

```text
docker
```

Esse grupo possui poder equivalente a root em diversos cenários.

Isso é uma dívida técnica de segurança conhecida.

Possíveis evoluções futuras:

* Podman rootless;
* Docker rootless;
* helper privilegiado isolado;
* políticas adicionais de sandbox;
* AppArmor;
* polkit;
* namespaces adicionais.

Essa dívida não foi misturada à `v0.2.2`, porque constitui uma mudança independente de infraestrutura e segurança.

---

# Painel de status

O entrypoint principal apresenta um painel textual com o estado operacional.

Exemplo conceitual:

```text
╔══════════════════════════════════════════════╗
║                   N E X U S                  ║
║                    v0.2.2                    ║
╠══════════════════════════════════════════════╣
║ Core                              ✓ ONLINE   ║
║ Configuration                     ✓ READY    ║
║ Database                          ✓ READY    ║
║ Logger                            ✓ READY    ║
║ EventBus                          ✓ READY    ║
║ SecurityGate                      ✓ READY    ║
║ ToolRegistry                      ✓ READY    ║
║ Terminal Sandbox                  ✓ READY    ║
╠══════════════════════════════════════════════╣
║ Health Monitor                    ✓ READY    ║
╠══════════════════════════════════════════════╣
║ Node                         NEXUS-NODE-01    ║
║ Network                           ✗ OFFLINE  ║
║ Mode                               OFFLINE   ║
╚══════════════════════════════════════════════╝
```

A interface atual é textual.

Atualização dinâmica de UI não faz parte do escopo da `v0.2.2`.

---

# Testes

Testes automatizados são parte obrigatória do processo de engenharia do Nexus Core.

A suíte atual utiliza:

```text
pytest
```

Execução:

```bash
PYTHONPATH="$PWD" pytest -q
```

Baseline da `v0.2.2`:

```text
134 passed
```

---

## Cobertura arquitetural atual

A suíte cobre, entre outros:

* inicialização da aplicação;
* shutdown;
* runtime modes;
* transições válidas;
* transições inválidas;
* estado autoritativo;
* snapshots;
* imutabilidade;
* concorrência;
* competing writers;
* health status;
* health snapshots;
* connectivity manager;
* monitoramento contínuo;
* transições offline → online;
* transições online → offline;
* ausência de eventos em estado estável;
* intervalo inválido;
* worker thread;
* nome da worker;
* daemon flag;
* start idempotente;
* stop idempotente;
* stop antes de start;
* timeout de shutdown;
* sobrevivência da worker após exceções;
* falha de subscriber;
* continuidade da worker após falha de subscriber;
* monitor desabilitado em forced offline;
* lifecycle da aplicação;
* `initialize()` one-shot;
* `shutdown()` idempotente;
* ordem monitor stop → system stop;
* shutdown em `finally`;
* uso de runtime snapshot no entrypoint.

---

## Determinismo

Transições podem ser testadas diretamente através de:

```python
monitor.check_once()
```

sem depender de polling real.

Testes que precisam verificar comportamento da worker utilizam primitivas de sincronização como:

```text
threading.Event
threading.Barrier
```

em vez de depender exclusivamente de sleeps arbitrários.

---

# Dependências

O runtime Python da `v0.2.2` não exige pacotes externos obrigatórios.

Arquivo:

```text
requirements/base.txt
```

deve refletir:

```text
# Nexus Core runtime dependencies
# No external Python packages are required at v0.2.2.
```

Para desenvolvimento:

```text
requirements/dev.txt
```

inclui:

```text
-r base.txt
pytest==9.1.1
```

A `v0.2.2` utiliza apenas biblioteca padrão para sua nova funcionalidade de concorrência:

```text
threading
logging
```

---

# Estrutura do projeto

Estrutura conceitual atual:

```text
Nexus Core/
│
├── nexus/
│   │
│   ├── config/
│   │   └── settings.py
│   │
│   ├── core/
│   │   ├── application.py
│   │   ├── connectivity.py
│   │   ├── connectivity_monitor.py
│   │   ├── logger.py
│   │   ├── runtime.py
│   │   └── runtime_state.py
│   │
│   ├── events/
│   │
│   ├── monitoring/
│   │   └── health.py
│   │
│   ├── security/
│   │
│   ├── tools/
│   │
│   └── main.py
│
├── requirements/
│   ├── base.txt
│   └── dev.txt
│
├── tests/
│   ├── test_application_connectivity_monitor.py
│   ├── test_application_runtime.py
│   ├── test_connectivity_monitor.py
│   ├── test_core.py
│   ├── test_health.py
│   ├── test_main.py
│   └── test_runtime_state.py
│
├── README.md
└── ...
```

A árvore acima destaca os componentes relevantes à arquitetura atual e não pretende representar necessariamente todos os arquivos auxiliares existentes.

---

# Histórico recente

## v0.1.0 — Foundation

Fundação inicial do Nexus Core.

Objetivos:

* estrutura do projeto;
* configuração;
* logging;
* banco de dados;
* arquitetura inicial.

---

## v0.1.1 — Infrastructure Core

Expansão da infraestrutura central.

---

## v0.1.2 — Event Architecture

Introdução do modelo de eventos internos.

---

## v0.1.3 — Security Gate

Introdução da fronteira de autorização central.

---

## v0.1.4 — Tool Architecture

Estruturação do sistema de ferramentas.

---

## v0.1.5 — Path Security

Validação de caminhos e proteção de filesystem.

---

## v0.1.6 — Tool Permissions + Audit Log

Permissões explícitas por ferramenta e auditoria.

---

## v0.1.7 — Secure File Tools

Ferramentas de filesystem integradas ao modelo de segurança.

---

## v0.1.8 — Terminal Sandbox

Execução controlada de terminal em sandbox Docker.

---

## v0.1.9 — Health Check & Application Status

Health checks e status operacional da aplicação.

---

## v0.2.0 — Connectivity & Runtime Modes

Introduziu:

* `ConnectivityManager`;
* `ConnectivityStatus`;
* `RuntimeMode`;
* `ONLINE`;
* `OFFLINE`;
* `DEGRADED`;
* política `offline_mode`;
* eventos de conectividade;
* determinação inicial do runtime.

Baseline histórico:

```text
87 tests passing
```

---

## v0.2.1 — Runtime State Controller

Introduziu:

* `RuntimeStateController`;
* estado centralizado;
* `reason`;
* `changed_at`;
* validação formal de transições;
* integração do runtime com a aplicação;
* preservação dos eventos iniciais.

Baseline histórico:

```text
97 tests passing
```

---

# v0.2.2 — Continuous Connectivity Monitoring

A `v0.2.2` introduz monitoramento contínuo e controlado da conectividade externa.

Entregue:

* `ConnectivityMonitor`;
* worker `Nexus-ConnectivityMonitor`;
* polling periódico;
* intervalo configurável;
* intervalo padrão de `30.0` segundos;
* nenhuma worker em forced offline;
* detecção `ONLINE ↔ OFFLINE`;
* ausência de eventos em estado estável;
* transições atômicas;
* `RuntimeTransitionResult`;
* `RuntimeStateSnapshot`;
* `HealthRuntimeSnapshot`;
* sincronização de runtime health;
* `threading.RLock`;
* `threading.Event`;
* shutdown responsivo;
* timeout de stop;
* lifecycle da aplicação endurecido;
* `initialize()` one-shot;
* `shutdown()` idempotente;
* shutdown garantido no entrypoint;
* proteção contra falhas inesperadas da worker;
* tentativa independente de eventos de transição;
* continuidade da worker após falha de subscriber;
* regressão completa.

Baseline:

```text
134 tests passing
```

---

## Princípios de engenharia da v0.2.2

A implementação preserva:

### Local First

O funcionamento local não depende da disponibilidade da Internet.

### Security First

Conectividade não altera as fronteiras de autorização.

### Determinismo

Transições podem ser testadas por `check_once()` sem aguardar polling.

### Observabilidade

O estado de runtime possui representação autoritativa e projeção de health.

### Isolamento de falhas

Exceções inesperadas de ciclos não encerram permanentemente a worker.

### Lifecycle explícito

A worker possui inicialização e shutdown controlados.

### Scope control

Nenhuma funcionalidade de LLM, memória, voz, visão ou automação foi misturada nesta release.

---

# Roadmap

O roadmap é evolutivo.

Cada versão deve adicionar uma responsabilidade pequena, clara e testável.

---

## Infraestrutura de runtime

### v0.2.2 — Continuous Connectivity Monitoring

**Status: concluída**

Entregue:

* polling contínuo de conectividade;
* transições `ONLINE ↔ OFFLINE`;
* worker dedicada;
* lifecycle controlado;
* snapshots consistentes;
* health sincronizado;
* eventos somente em transições;
* isolamento de falhas;
* shutdown determinístico;
* 134 testes passando.

---

### v0.2.3 — Automatic DEGRADED Runtime Detection

**Status: próxima versão planejada**

Objetivo:

* definir formalmente as condições de `DEGRADED`;
* distinguir conectividade de disponibilidade parcial;
* preservar `RuntimeStateController` como fonte autoritativa;
* integrar o novo estado ao EventBus;
* definir razões explícitas para degradação;
* manter comportamento local-first;
* adicionar observabilidade;
* adicionar testes determinísticos;
* evitar heurísticas implícitas.

---

### v0.2.4 — Environment & Runtime Configuration

Planejado:

* configuração por ambiente;
* perfis `development`;
* perfis de produção;
* overrides controlados;
* validação;
* configuração externa;
* governança de parâmetros;
* preparação para providers e modelos.

---

# Inteligência artificial

## v0.3.0 — Local Model Layer

Planejado:

* integração com modelo local;
* provider local;
* execução isolada;
* contratos de entrada e saída;
* observabilidade;
* nenhuma autoridade direta sobre ferramentas.

Candidato atual:

```text
Ollama
```

---

## v0.3.1 — Provider Abstraction & Model Routing

Planejado:

* interface comum para providers;
* modelo local;
* provider online opcional;
* política de roteamento;
* disponibilidade;
* fallback controlado;
* proteção de credenciais.

Modelo conceitual:

```text
Task
 │
 ▼
Model Router
 │
 ├── Local Provider
 │
 └── Online Provider
```

A preferência arquitetural permanece:

```text
LOCAL FIRST
```

---

## v0.3.2 — Controlled Agent & Tool Calling

Planejado:

```text
Model
  │
  ▼
Planner / Agent
  │
  ▼
ToolRegistry
  │
  ▼
ToolExecutor
  │
  ▼
SecurityGate
  │
  ▼
Tool
```

O LLM nunca terá acesso direto ao shell ou ao sistema operacional.

---

# Memória e conhecimento

## v0.4.0 — Persistent Memory Foundation

Planejado:

* modelo formal de memória;
* persistência;
* recuperação;
* proveniência;
* expiração;
* remoção;
* limites de autoridade.

Os eventos:

```text
memory.created
memory.recalled
```

podem existir no catálogo arquitetural antes da implementação do subsistema.

Sua existência **não significa que memória persistente já esteja implementada**.

---

## v0.4.1 — Knowledge Base

Planejado:

* ingestão controlada;
* indexação;
* recuperação;
* metadados;
* proveniência;
* tratamento de documentos como conteúdo não confiável;
* mitigação de prompt injection.

---

# Voz

## v0.5.x — Voice Foundation

Planejado:

* Speech-to-Text;
* Text-to-Speech;
* Wake Word;
* Voice Activity Detection;
* pipeline de interação por voz.

Tecnologias candidatas:

```text
whisper.cpp
openWakeWord
Piper
```

---

# Visão

## v0.6.x — Vision & Screen Understanding

Planejado:

* Computer Vision;
* captura de tela;
* interpretação de tela;
* contexto visual;
* análise multimodal;
* câmera.

---

# Automação

## v0.7.x — Controlled Desktop Automation

Planejado:

* automação controlada do desktop;
* ações governadas;
* autorização baseada em risco;
* observabilidade;
* rollback quando aplicável;
* integração com Agent/Planner.

---

# Hardware e distribuição

## v0.8.x — Devices & Distributed Architecture

Planejado:

* Arduino;
* ESP32;
* sensores;
* comunicação local;
* múltiplos nodes;
* descoberta de dispositivos;
* autenticação entre nodes;
* arquitetura distribuída.

Firmware embarcado seguirá preferencialmente:

```text
C / C++
```

em vez de MicroPython.

---

# Interface multimodal

## v0.9.x — Multimodal Interface

Planejado:

* interface gráfica;
* interação textual;
* voz;
* contexto visual;
* status operacional;
* experiência multimodal;
* UI circular futurista.

Tecnologia candidata para desktop:

```text
PySide6
```

---

# v1.0.0 — Production Baseline

A versão `1.0.0` somente deverá ser considerada quando o Nexus Core possuir um baseline operacional com:

* arquitetura madura;
* segurança revisada;
* testes abrangentes;
* documentação consistente;
* observabilidade;
* gestão de configuração;
* atualização segura;
* modelos locais;
* memória controlada;
* ferramentas governadas;
* lifecycle confiável;
* comportamento offline funcional.

---

# Critérios de qualidade para novas versões

Cada versão deve possuir:

* escopo explícito;
* responsabilidades bem definidas;
* implementação mínima coerente;
* testes unitários;
* testes de integração;
* regressão completa;
* revisão arquitetural;
* documentação atualizada;
* dependências revisadas;
* revisão Git;
* commit versionado;
* tag própria;
* push de commit;
* push de tag;
* verificação final no repositório remoto.

Fluxo:

```text
PLANEJAMENTO
    │
    ▼
IMPLEMENTAÇÃO
    │
    ▼
TESTES UNITÁRIOS
    │
    ▼
TESTES DE INTEGRAÇÃO
    │
    ▼
REGRESSÃO COMPLETA
    │
    ▼
REVISÃO ARQUITETURAL
    │
    ▼
README
    │
    ▼
REQUIREMENTS
    │
    ▼
GIT REVIEW
    │
    ▼
COMMIT
    │
    ▼
TAG
    │
    ▼
PUSH
    │
    ▼
VERIFICAÇÃO FINAL
```

Nenhuma versão deve ser considerada concluída enquanto existirem inconsistências conhecidas entre:

```text
implementação
testes
arquitetura
documentação
requirements
roadmap
Git
```

---

# Convenção de commits

O projeto utiliza:

```text
<type>: Nexus Core v<VERSION> <description>
```

Exemplos históricos:

```text
checkpoint: Nexus Core v0.1.8 terminal sandbox
release: Nexus Core v0.1.9 health check
feat: Nexus Core v0.2.0 Implement Connectivity and Runtime Modes
feat: Nexus Core v0.2.1 Implement Runtime State Controller
```

Commit planejado para a release atual:

```text
feat: Nexus Core v0.2.2 Implement Continuous Connectivity Monitoring
```

Cada release possui sua própria tag.

Exemplos:

```text
v0.2.0
v0.2.1
v0.2.2
```

---

# Segurança e limitações atuais

O projeto permanece em desenvolvimento.

Limitações e regras atuais:

* o LLM ainda não está integrado;
* o LLM não possui acesso direto ao sistema operacional;
* ferramentas passam pelo `SecurityGate`;
* operações perigosas permanecem sujeitas à política de segurança;
* conteúdo externo é não confiável;
* prompt injection não representa autoridade;
* o terminal utiliza sandbox Docker;
* pertencimento ao grupo `docker` representa dívida técnica de segurança;
* `ONLINE` não significa autorização;
* `DEGRADED` ainda não possui determinação automática;
* `latency_ms` ainda não é medido ativamente;
* o monitor atual cobre apenas conectividade `ONLINE ↔ OFFLINE`;
* memória persistente ainda não está implementada;
* Knowledge Base ainda não está implementada;
* modelo local ainda não está integrado;
* interface gráfica ainda não está implementada;
* voz ainda não está implementada;
* visão ainda não está implementada;
* automação do desktop ainda não está implementada.

Essas limitações são explicitadas deliberadamente para distinguir:

```text
IMPLEMENTADO
```

de:

```text
PLANEJADO
```

---

# Tecnologias atuais

Baseline:

```text
Operating System: Ubuntu 24.04 LTS
Runtime:          Python 3.12
Database:         SQLite
Tests:            pytest
Sandbox:          Docker
Version Control:  Git
Remote:           GitHub
```

---

# Tecnologias candidatas futuras

Dependendo da evolução arquitetural:

```text
Ollama
Hermes Agent
whisper.cpp
openWakeWord
Piper
ComfyUI
PySide6
AppArmor
polkit
systemd
Podman rootless
Docker rootless
```

Nenhuma tecnologia futura deve ser considerada compromisso definitivo até passar pela revisão arquitetural da versão correspondente.

---

# Filosofia Local First

O Nexus Core deve continuar útil mesmo quando:

```text
Internet unavailable
```

O sistema local não deve depender estruturalmente de:

* disponibilidade de APIs externas;
* conta em serviço remoto;
* conectividade constante;
* cloud obrigatória.

Serviços online poderão complementar o sistema.

Eles não devem substituir sua fundação local.

---

# Privacidade

O objetivo de longo prazo é manter localmente, sempre que possível:

* processamento;
* memória;
* contexto;
* voz;
* conhecimento;
* documentos;
* automações;
* preferências.

Integrações online deverão ser:

* opcionais;
* explícitas;
* governadas;
* observáveis;
* limitadas ao necessário.

---

# Observabilidade

O Nexus Core deverá evoluir mantendo rastreabilidade de:

* lifecycle;
* runtime;
* conectividade;
* ferramentas;
* autorizações;
* falhas;
* mudanças de estado;
* memória futura;
* providers futuros;
* operações de agentes.

Observabilidade não deve implicar coleta indiscriminada de dados sensíveis.

---

# Governança de ferramentas

Nenhuma ferramenta deve receber autoridade apenas por estar registrada.

O fluxo correto permanece:

```text
Tool requested
      │
      ▼
ToolRegistry
      │
      ▼
ToolExecutor
      │
      ▼
SecurityGate
      │
      ├── ALLOW
      │     │
      │     ▼
      │   EXECUTE
      │
      └── DENY
            │
            ▼
          BLOCK
```

---

# Fronteira entre inteligência e execução

Uma futura camada de modelo deverá operar sob o princípio:

```text
LLM proposes
System decides
Security authorizes
Tool executes
```

Nunca:

```text
LLM directly executes arbitrary host commands
```

---

# Escopo da v0.2.2

A `v0.2.2` é deliberadamente uma release de infraestrutura.

Ela **não** introduz:

* modelo local;
* Agent;
* Planner;
* memória;
* Knowledge Base;
* voz;
* wake word;
* visão;
* câmera;
* screen understanding;
* desktop automation;
* GUI;
* geração de imagens;
* geração de vídeos.

Ela introduz uma capacidade menor e fundamental:

> manter o estado de conectividade atualizado continuamente de forma testável, thread-safe e controlada.

Esse modelo incremental reduz complexidade e facilita auditoria.

---

# Próximo passo

A próxima release planejada é:

```text
v0.2.3 — Automatic DEGRADED Runtime Detection
```

A implementação deverá começar somente após o fechamento completo da `v0.2.2`:

```text
README
requirements
version
tests
Git review
commit
tag
push
remote verification
```

---

# Licença

A licença do projeto será definida posteriormente.

---

# Status

```text
Nexus Core
────────────────────────────────────────────────
Stable Version:       v0.2.2
Next Development:     v0.2.3
Runtime:              Python 3.12
Database:             SQLite
Sandbox:              Docker
Testing:              pytest
Tests:                134 passed
Development Status:   ACTIVE
────────────────────────────────────────────────
```

---

**Nexus Core**

Assistente pessoal de inteligência artificial local-first.
