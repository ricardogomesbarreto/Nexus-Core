# Nexus Core

Assistente pessoal de inteligência artificial **local-first, multimodal, modular, seguro e orientado a agentes**.

> **Versão estável atual:** `v0.2.3 — Automatic DEGRADED Runtime Detection`
> **Próxima versão planejada:** `v0.2.4 — Environment & Runtime Configuration`
> **Status:** Development
> **Test baseline:** `151 passed`

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

A versão `v0.2.3` consolida a infraestrutura de runtime e conectividade introduzindo **detecção automática do estado `DEGRADED`**.

O Nexus Core agora distingue duas dimensões diferentes:

```text
observação bruta da rede
        │
        ▼
network_online

interpretação estabilizada do runtime
        │
        ▼
runtime_mode
```

Uma única mudança observada na conectividade não altera imediatamente o runtime entre `ONLINE` e `OFFLINE`.

Com o threshold padrão:

```text
connectivity_confirmation_threshold = 2
```

uma observação divergente coloca temporariamente o runtime em:

```text
DEGRADED
```

até que a mudança seja confirmada ou cancelada por recuperação.

Exemplo:

```text
ONLINE
  │
  │ primeira observação OFFLINE
  ▼
DEGRADED
  │
  │ segunda observação OFFLINE consecutiva
  ▼
OFFLINE
```

E simetricamente:

```text
OFFLINE
  │
  │ primeira observação ONLINE
  ▼
DEGRADED
  │
  │ segunda observação ONLINE consecutiva
  ▼
ONLINE
```

O estado `DEGRADED` da `v0.2.3` significa especificamente:

> uma mudança ou instabilidade de conectividade externa foi observada, mas ainda não foi confirmada como novo estado estável.

Ele **não** significa:

* indisponibilidade parcial de um provider;
* degradação de um serviço HTTP específico;
* falha parcial de um modelo;
* latência elevada;
* perda parcial de capacidades de IA.

Essas dimensões exigem sinais adicionais que ainda não fazem parte da arquitetura atual.

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
* Connectivity Runtime Evaluator
* Connectivity Monitor
* Runtime Mode
* Runtime State Controller
* Runtime snapshots
* Health runtime snapshots
* Estados `ONLINE`, `OFFLINE` e `DEGRADED`
* Detecção automática de conectividade instável
* Confirmação configurável de mudanças de conectividade
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

---

## Baseline atual

```text
Version:       v0.2.3
Tests:         151 passed
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
    ├── ConnectivityRuntimeEvaluator
    │   ├── Raw connectivity interpretation
    │   ├── Confirmation threshold
    │   ├── DEGRADED detection
    │   ├── Oscillation handling
    │   └── Deterministic state machine
    │
    ├── ConnectivityMonitor
    │   └── Nexus-ConnectivityMonitor
    │       ├── Periodic polling
    │       ├── Serialized monitoring cycles
    │       ├── Runtime evaluation
    │       ├── Raw network change detection
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

O `HealthStatus` não é utilizado pelo monitor como fonte para reconstruir o estado inicial da rede.

O estado bruto inicial é passado explicitamente ao `ConnectivityMonitor` através de:

```text
initial_network_online
```

O construtor valida que esse valor seja consistente com o estado inicial do `RuntimeStateController`.

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

---

# Fluxo de conectividade e runtime

A arquitetura da `v0.2.3` separa aquisição, interpretação, estado autoritativo e observabilidade.

```text
ConnectivityManager
        │
        ▼
ConnectivityStatus
        │
        │ raw online: bool
        ▼
ConnectivityRuntimeEvaluator
        │
        │ target mode
        ▼
RuntimeStateController
        │
        ├──────────────► EventBus
        │
        ▼
HealthStatus
```

Responsabilidades:

```text
ConnectivityManager
    → observa conectividade

ConnectivityRuntimeEvaluator
    → interpreta sequência de observações

RuntimeStateController
    → mantém estado autoritativo

HealthStatus
    → projeta estado para observabilidade

EventBus
    → comunica mudanças
```

Essa separação evita misturar:

```text
observação
interpretação
autoridade
observabilidade
```

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
11. Determina o modo inicial `ONLINE` ou `OFFLINE`.
12. Inicializa o `RuntimeStateController`.
13. Atualiza o `HealthStatus`.
14. Publica os eventos iniciais correspondentes.
15. Publica `SYSTEM_START`.
16. Registra a inicialização no banco.
17. Quando `offline_mode=False`, cria o `ConnectivityMonitor`.
18. Passa explicitamente a observação inicial da rede ao monitor.
19. Configura o threshold de confirmação.
20. Inicia a worker de conectividade.

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
connectivity_confirmation_threshold: int = 2
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
* não existe detecção automática de `DEGRADED`;
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
6. detecte mudanças brutas da rede;
7. coloque o runtime em `DEGRADED` durante confirmação;
8. confirme automaticamente `ONLINE` ou `OFFLINE`.

---

## Intervalo de monitoramento

O intervalo operacional padrão é:

```text
30.0 segundos
```

O `ConnectivityMonitor` rejeita intervalos menores ou iguais a zero.

---

## Threshold de confirmação

O threshold padrão é:

```text
2 observações consecutivas
```

Configuração:

```python
connectivity_confirmation_threshold = 2
```

Valores menores que:

```text
2
```

são rejeitados.

Para um threshold genérico `N`, uma nova condição precisa ser observada `N` vezes consecutivamente antes de substituir o estado estável confirmado.

Enquanto a confirmação não é concluída:

```text
runtime_mode = DEGRADED
```

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

Sua presença não deve ser interpretada como implementação de benchmarking ou como sinal usado para determinar `DEGRADED`.

---

## Falhas de conectividade

Falhas de rede ou I/O tratadas pelo `ConnectivityManager` são interpretadas como indisponibilidade externa.

Uma falha em comunicação não concede qualquer autoridade adicional ao sistema.

---

# Connectivity Runtime Evaluator

A `v0.2.3` introduz:

```text
ConnectivityRuntimeEvaluator
```

Ele implementa a política determinística que transforma observações brutas de conectividade em um modo alvo de runtime.

O evaluator:

* não executa I/O;
* não cria threads;
* não utiliza `EventBus`;
* não utiliza logger;
* não atualiza `HealthStatus`;
* não modifica diretamente o `RuntimeStateController`.

Ele mantém apenas o estado necessário para interpretar sequências de conectividade.

---

## Resultado da avaliação

Cada avaliação retorna um:

```text
ConnectivityRuntimeEvaluation
```

imutável.

Campos:

```text
target_mode
reason
network_online
network_changed
```

Onde:

```text
network_online
```

representa a observação bruta mais recente;

e:

```text
target_mode
```

representa a interpretação estabilizada ou provisória do runtime.

---

## Estado confirmado

O evaluator mantém internamente a última condição de rede confirmada.

Exemplo:

```text
confirmed_network_online = True
```

significa que o estado estável conhecido é online.

Uma observação diferente inicia um processo de confirmação.

---

## ONLINE → DEGRADED → OFFLINE

Com threshold `2`:

```text
Estado confirmado:
ONLINE

Observação 1:
online=False

Resultado:
network_online=False
runtime_mode=DEGRADED
reason="Perda de conectividade aguardando confirmação"

Observação 2:
online=False

Resultado:
network_online=False
runtime_mode=OFFLINE
reason="Conectividade externa indisponível"
```

---

## OFFLINE → DEGRADED → ONLINE

```text
Estado confirmado:
OFFLINE

Observação 1:
online=True

Resultado:
network_online=True
runtime_mode=DEGRADED
reason="Conectividade externa detectada; aguardando confirmação"

Observação 2:
online=True

Resultado:
network_online=True
runtime_mode=ONLINE
reason="Conectividade externa disponível"
```

---

## Recuperação antes da confirmação

Se a rede retornar ao estado confirmado antes que o threshold seja atingido, a mudança pendente é cancelada.

Exemplo:

```text
ONLINE
  │
  ├── OFFLINE observado
  │      ▼
  │   DEGRADED
  │
  └── ONLINE observado novamente
         ▼
      ONLINE
```

Nesse caso o sistema não confirma `OFFLINE`.

---

## Oscilação

Mudanças alternadas reiniciam o processo de confirmação quando necessário.

Isso impede que observações antigas sejam acumuladas incorretamente através de uma oscilação.

---

# Connectivity Monitor

A `v0.2.2` introduziu o `ConnectivityMonitor`.

A `v0.2.3` estende sua responsabilidade integrando o `ConnectivityRuntimeEvaluator`.

O componente recebe explicitamente:

```text
ConnectivityManager
RuntimeStateController
EventBus
HealthStatus
initial_network_online
poll interval
confirmation threshold
logger
```

---

## Invariant de inicialização

O monitor só pode ser criado quando:

```text
initial_network_online=True
```

for consistente com:

```text
runtime inicial ONLINE
```

e:

```text
initial_network_online=False
```

for consistente com:

```text
runtime inicial OFFLINE
```

Combinações inconsistentes são rejeitadas com:

```text
ValueError
```

O monitor também não aceita `DEGRADED` como seu estado confirmado inicial.

`DEGRADED` é alcançado posteriormente pelo evaluator a partir de uma observação divergente.

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

## Serialização de ciclos

A `v0.2.3` adiciona um lock dedicado ao ciclo de monitoramento:

```text
_cycle_lock
```

Todo `check_once()` é serializado.

Isso impede que:

```text
worker thread
```

e:

```text
chamada manual de check_once()
```

executem simultaneamente sobre o evaluator stateful.

O ciclo protegido inclui:

```text
ConnectivityManager.check()
        │
        ▼
ConnectivityRuntimeEvaluator.evaluate()
        │
        ▼
RuntimeStateController transition
        │
        ▼
HealthStatus update
        │
        ▼
Event publication
```

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

# Semântica das transições de conectividade

A `v0.2.3` separa:

```text
mudança na observação bruta da rede
```

de:

```text
mudança no modo de runtime
```

Essas duas dimensões possuem eventos independentes.

---

## Eventos `NETWORK_*`

Os eventos:

```text
NETWORK_ONLINE
NETWORK_OFFLINE
```

representam **mudanças na observação bruta da conectividade**.

Eles não representam confirmação de runtime.

---

## Evento `RUNTIME_MODE_CHANGED`

O evento:

```text
RUNTIME_MODE_CHANGED
```

representa uma mudança efetiva no estado autoritativo de runtime.

Ele pode representar:

```text
ONLINE → DEGRADED
DEGRADED → OFFLINE
OFFLINE → DEGRADED
DEGRADED → ONLINE
```

---

## Exemplo ONLINE → OFFLINE

Estado inicial:

```text
ONLINE
```

Primeira observação `False`:

```text
NETWORK_OFFLINE
RUNTIME_MODE_CHANGED(DEGRADED)
```

Segunda observação `False`:

```text
RUNTIME_MODE_CHANGED(OFFLINE)
```

Não existe um segundo:

```text
NETWORK_OFFLINE
```

porque a observação bruta não mudou novamente.

---

## Exemplo OFFLINE → ONLINE

Primeira observação `True`:

```text
NETWORK_ONLINE
RUNTIME_MODE_CHANGED(DEGRADED)
```

Segunda observação `True`:

```text
RUNTIME_MODE_CHANGED(ONLINE)
```

Novamente, não existe um segundo:

```text
NETWORK_ONLINE
```

na confirmação.

---

## Estado bruto estável

Se nenhuma dimensão mudar:

```text
nenhum NETWORK_*
nenhum RUNTIME_MODE_CHANGED
```

Isso evita:

* event flooding;
* timestamps artificiais;
* side effects repetidos;
* atualizações sem mudança real.

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

```text
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

## Matriz de transições

A matriz atual permite:

```text
OFFLINE
  ├── ONLINE
  └── DEGRADED

ONLINE
  ├── OFFLINE
  └── DEGRADED

DEGRADED
  ├── ONLINE
  └── OFFLINE
```

As transições diretas:

```text
ONLINE ↔ OFFLINE
```

continuam legais no `RuntimeStateController` para preservar compatibilidade e permitir outros consumidores.

Entretanto, a política implementada pelo `ConnectivityRuntimeEvaluator` e pelo `ConnectivityMonitor` utiliza `DEGRADED` como estado intermediário durante mudanças automáticas de conectividade.

---

## `transition()`

Preserva o contrato histórico da `v0.2.1`.

Uma transição válida retorna:

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

Representa conectividade externa confirmada como disponível.

Não significa:

* autorização;
* confiança;
* permissão para executar ferramentas;
* permissão para acessar serviços arbitrários;
* elevação de privilégio.

---

## OFFLINE

Representa conectividade externa confirmada como indisponível ou operação offline forçada.

O Nexus Core foi projetado para preservar sua capacidade local mesmo nesse estado.

---

## DEGRADED

Na `v0.2.3`, `DEGRADED` possui uma semântica operacional específica:

> existe uma mudança de conectividade observada que ainda aguarda confirmação suficiente para substituir o estado estável anterior.

Exemplos:

```text
network_online=False
runtime_mode=DEGRADED
```

pode representar uma perda de conectividade ainda não confirmada.

Enquanto:

```text
network_online=True
runtime_mode=DEGRADED
```

pode representar uma recuperação ainda não confirmada.

`DEGRADED` não implica disponibilidade parcial de serviços.

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

O monitor não utiliza o `HealthStatus` como fonte para decidir sua política de conectividade.

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

Esse contrato histórico foi preservado.

O estado inicial automático é sempre:

```text
ONLINE
```

ou:

```text
OFFLINE
```

`DEGRADED` é produzido posteriormente pelo monitor quando uma nova observação diverge do estado confirmado.

---

# Semântica de monitoramento — v0.2.3

Exemplo completo:

```text
Inicialização
ONLINE
  ├── NETWORK_ONLINE
  └── RUNTIME_MODE_CHANGED(ONLINE)

Polling estável
ONLINE
  └── nenhum evento

Primeira perda observada
network_online=False
runtime=DEGRADED
  ├── NETWORK_OFFLINE
  └── RUNTIME_MODE_CHANGED(DEGRADED)

Segunda perda consecutiva
network_online=False
runtime=OFFLINE
  └── RUNTIME_MODE_CHANGED(OFFLINE)

Polling estável
OFFLINE
  └── nenhum evento

Primeira recuperação observada
network_online=True
runtime=DEGRADED
  ├── NETWORK_ONLINE
  └── RUNTIME_MODE_CHANGED(DEGRADED)

Segunda recuperação consecutiva
network_online=True
runtime=ONLINE
  └── RUNTIME_MODE_CHANGED(ONLINE)
```

Isso preserva:

* determinismo;
* auditabilidade;
* baixo ruído;
* ausência de event flooding;
* separação entre observação e interpretação;
* resistência a flapping simples.

---

# Falhas em subscribers

O `EventBus` preserva o comportamento de propagação de exceções de subscribers.

Se um evento de rede e um evento de runtime precisarem ser publicados no mesmo ciclo e um subscriber de:

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

A falha original continua visível ao chamador de:

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

Essa dívida não foi misturada à `v0.2.3`, porque constitui uma mudança independente de infraestrutura e segurança.

---

# Painel de status

O entrypoint principal apresenta um painel textual com o estado operacional.

Exemplo conceitual:

```text
╔══════════════════════════════════════════════╗
║                   N E X U S                  ║
║                    v0.2.3                    ║
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

Atualização dinâmica de UI não faz parte do escopo da `v0.2.3`.

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

Baseline da `v0.2.3`:

```text
151 passed
```

---

## Cobertura arquitetural atual

A suíte cobre, entre outros:

* inicialização da aplicação;
* shutdown;
* runtime modes;
* transições válidas;
* transições inválidas;
* transições envolvendo `DEGRADED`;
* estado autoritativo;
* snapshots;
* imutabilidade;
* concorrência;
* competing writers;
* health status;
* health snapshots;
* connectivity manager;
* connectivity runtime evaluator;
* threshold inválido;
* threshold configurável;
* threshold maior que dois;
* perda de conectividade;
* recuperação de conectividade;
* cancelamento de mudança pendente;
* oscilação;
* distinção entre `network_changed` e confirmação de runtime;
* monitoramento contínuo;
* `ONLINE → DEGRADED → OFFLINE`;
* `OFFLINE → DEGRADED → ONLINE`;
* separação entre eventos de rede e runtime;
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
* serialização de chamadas concorrentes de `check_once()`;
* consistência entre runtime inicial e rede inicial;
* independência entre HealthStatus e inicialização do evaluator;
* monitor desabilitado em forced offline;
* lifecycle da aplicação;
* `initialize()` one-shot;
* `shutdown()` idempotente;
* ordem monitor stop → system stop;
* shutdown em `finally`;
* uso de runtime snapshot no entrypoint;
* regressão completa.

---

## Determinismo

Transições podem ser testadas diretamente através de:

```python
monitor.check_once()
```

sem depender de polling real.

O `ConnectivityRuntimeEvaluator` também pode ser exercitado isoladamente através de sequências determinísticas de valores booleanos.

Testes que precisam verificar comportamento concorrente utilizam primitivas de sincronização explícitas.

---

# Dependências

O runtime Python da `v0.2.3` não exige pacotes externos obrigatórios.

Arquivo:

```text
requirements/base.txt
```

deve refletir:

```text
# Nexus Core runtime dependencies
# No external Python packages are required at v0.2.3.
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

A `v0.2.3` utiliza apenas biblioteca padrão para a nova funcionalidade:

```text
dataclasses
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
│   │   ├── connectivity_runtime_evaluator.py
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
│   ├── test_connectivity_runtime_evaluator.py
│   ├── test_core.py
│   ├── test_health.py
│   ├── test_main.py
│   ├── test_runtime.py
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

## v0.2.2 — Continuous Connectivity Monitoring

Introduziu:

* `ConnectivityMonitor`;
* worker `Nexus-ConnectivityMonitor`;
* polling periódico;
* intervalo configurável;
* intervalo padrão de `30.0` segundos;
* nenhuma worker em forced offline;
* detecção contínua de conectividade;
* transições condicionais atômicas;
* `RuntimeTransitionResult`;
* `RuntimeStateSnapshot`;
* `HealthRuntimeSnapshot`;
* sincronização de runtime health;
* `threading.RLock`;
* `threading.Event`;
* shutdown responsivo;
* timeout de stop;
* lifecycle endurecido;
* `initialize()` one-shot;
* `shutdown()` idempotente;
* shutdown garantido no entrypoint;
* isolamento de falhas da worker;
* continuidade após falha de subscriber.

Baseline histórico:

```text
134 tests passing
```

---

# v0.2.3 — Automatic DEGRADED Runtime Detection

A `v0.2.3` introduz uma política determinística de confirmação de mudanças de conectividade e ativa automaticamente o estado `DEGRADED`.

Entregue:

* `ConnectivityRuntimeEvaluator`;
* `ConnectivityRuntimeEvaluation`;
* `DEGRADED` automático;
* confirmação simétrica de perda e recuperação;
* threshold configurável;
* threshold padrão `2`;
* rejeição de threshold menor que `2`;
* suporte determinístico a thresholds maiores;
* cancelamento de mudança pendente;
* reset após oscilação;
* separação entre rede bruta e runtime estabilizado;
* `network_changed`;
* `ONLINE → DEGRADED → OFFLINE`;
* `OFFLINE → DEGRADED → ONLINE`;
* eventos `NETWORK_*` ligados a mudanças da observação bruta;
* `RUNTIME_MODE_CHANGED` ligado a mudanças do runtime;
* nenhuma duplicação de `NETWORK_*` na confirmação;
* integração explícita do evaluator ao monitor;
* estado bruto inicial passado explicitamente;
* invariant entre rede inicial e runtime inicial;
* rejeição de `DEGRADED` como estado confirmado inicial do monitor;
* `HealthStatus` preservado como projeção;
* serialização integral de `check_once()`;
* proteção contra chamadas concorrentes;
* matriz de transições do `RuntimeStateController` expandida;
* propagação de `connectivity_confirmation_threshold` por `Settings`;
* forced offline preservado;
* sem dependências externas adicionais;
* regressão completa.

Baseline:

```text
151 tests passing
```

---

## Princípios de engenharia da v0.2.3

### Local First

A conectividade externa continua não sendo requisito para a operação estrutural local.

### Security First

Mudanças de conectividade não concedem autoridade adicional a ferramentas ou modelos futuros.

### Separação de responsabilidades

Aquisição, avaliação, estado autoritativo, observabilidade e publicação de eventos permanecem separados.

### Determinismo

O evaluator pode ser testado sem rede real, sleeps ou threads.

### Observabilidade

O Nexus diferencia explicitamente:

```text
network_online
```

de:

```text
runtime_mode
```

### Resistência a flapping

Uma única observação divergente não substitui imediatamente o estado estável confirmado.

### Concorrência controlada

`check_once()` é serializado para impedir corrupção do estado interno do evaluator.

### Scope control

A release não inventa sinais que o sistema ainda não possui.

`DEGRADED` não foi associado artificialmente a:

* latência;
* providers;
* APIs;
* LLMs;
* serviços HTTP.

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
* worker dedicada;
* lifecycle controlado;
* snapshots consistentes;
* health sincronizado;
* isolamento de falhas;
* shutdown determinístico;
* 134 testes passando.

---

### v0.2.3 — Automatic DEGRADED Runtime Detection

**Status: concluída**

Entregue:

* definição operacional de `DEGRADED`;
* `ConnectivityRuntimeEvaluator`;
* confirmação configurável de conectividade;
* threshold padrão `2`;
* transições com estado intermediário;
* separação entre observação bruta e runtime;
* eventos independentes de rede e runtime;
* tratamento determinístico de recuperação e oscilação;
* serialização de ciclos;
* invariants de inicialização;
* 151 testes passando.

---

### v0.2.4 — Environment & Runtime Configuration

**Status: próxima versão planejada**

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
VERSION
    │
    ▼
SMOKE TEST
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
feat: Nexus Core v0.2.2 Implement Continuous Connectivity Monitoring
```

Commit planejado para a release atual:

```text
feat: Nexus Core v0.2.3 Implement Automatic DEGRADED Runtime Detection
```

Cada release possui sua própria tag.

Exemplos:

```text
v0.2.0
v0.2.1
v0.2.2
v0.2.3
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
* `DEGRADED` representa somente conectividade em confirmação;
* `DEGRADED` não representa saúde de providers;
* `latency_ms` ainda não é medido ativamente;
* latência não participa da política de `DEGRADED`;
* o monitor atual observa conectividade externa booleana;
* não existem probes de serviços individuais;
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

# Escopo da v0.2.3

A `v0.2.3` é deliberadamente uma release de infraestrutura de runtime.

Ela **não** introduz:

* modelo local;
* provider abstraction;
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
* geração de vídeos;
* probes de providers;
* service health;
* degradação baseada em latência;
* avaliação HTTP de serviços;
* política de disponibilidade de modelos.

Ela introduz uma capacidade menor e fundamental:

> interpretar mudanças de conectividade de forma estabilizada, utilizando `DEGRADED` durante o período de confirmação antes de assumir um novo estado `ONLINE` ou `OFFLINE`.

Esse modelo incremental reduz complexidade e facilita auditoria.

---

# Próximo passo

A próxima release planejada é:

```text
v0.2.4 — Environment & Runtime Configuration
```

Objetivo:

* externalizar configuração de runtime de forma controlada;
* introduzir perfis de ambiente;
* validar parâmetros;
* permitir overrides explícitos;
* preparar a infraestrutura para providers e modelos futuros.

---

# Licença

A licença do projeto será definida posteriormente.

---

# Status

```text
Nexus Core
────────────────────────────────────────────────
Stable Version:       v0.2.3
Next Development:     v0.2.4
Runtime:              Python 3.12
Database:             SQLite
Sandbox:              Docker
Testing:              pytest
Tests:                151 passed
Development Status:   ACTIVE
────────────────────────────────────────────────
```

---

**Nexus Core**

Assistente pessoal de inteligência artificial local-first.