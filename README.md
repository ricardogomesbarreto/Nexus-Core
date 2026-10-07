<p align="center">
  <img
    src="assets/brand/nexus-core-logo.png"
    alt="Nexus Core"
    width="980"
  >
</p>

<p align="center">
  <img alt="Python 3.12 ou superior" src="https://img.shields.io/badge/Python-3.12%2B-3776AB?logo=python&logoColor=white">
  <img alt="PostgreSQL local" src="https://img.shields.io/badge/PostgreSQL-local-4169E1?logo=postgresql&logoColor=white">
  <img alt="Linux desktop" src="https://img.shields.io/badge/Linux-desktop-FCC624?logo=linux&logoColor=black">
  <img alt="Versão v0.3.3" src="https://img.shields.io/badge/vers%C3%A3o-v0.3.3-722F37">
  <img alt="Licença MIT" src="https://img.shields.io/badge/licen%C3%A7a-MIT-2F855A">
  <a href="https://github.com/ricardogomesbarreto/Nexus-Core/actions/workflows/ci.yml"><img alt="CI do Nexus Core" src="https://github.com/ricardogomesbarreto/Nexus-Core/actions/workflows/ci.yml/badge.svg?branch=main"></a>
</p>

# Nexus Core

Assistente pessoal de inteligência artificial **local-first, modular e seguro**, desenvolvido para execução no desktop Linux sobre fronteiras explícitas entre inteligência, autorização e execução.

> **Versão atual:** `v0.3.3 — Explicit Confirmation & Authorization`<br>
> **Última tag publicada:** `v0.3.3`<br>
> **Próximo marco planejado:** `v0.3.4 — Structured Tool Contracts`<br>
> **Plataforma e distribuição:** aplicativo local executável no Linux; código sob licença MIT<br>
> **Interface atual:** terminal local; interface gráfica nativa planejada<br>
> **Banco único:** PostgreSQL local<br>
> **Validação local:** `549 passed, 8 skipped` (Docker e PostgreSQL reais indisponíveis aqui)<br>
> **Primary Platform:** Linux<br>
> **Local Model Runtime:** Ollama<br>
> **Reference Model:** `qwen3:1.7b`<br>
> **Desktop Application:** Native<br>
> **Web Application:** No<br>
> **Primary Visual Identity:** Wine Red<br>
> **Primary Color:** `#722F37`<br>
>
> [Identidade Nexus Line](docs/ICONOGRAFIA.md) · marca oficial, iconografia Core e fundação visual desktop nativa

---

# Visão geral

O **Nexus Core** é a infraestrutura central de um assistente pessoal de inteligência artificial projetado para operar prioritariamente de forma local.

O programa roda como processo nativo no Linux. A distribuição atual oferece
o comando `nexus-core` no ambiente Python do usuário. A opção
`--sandbox-command` exige confirmação no terminal para cada execução isolada.
Os assets da futura
interface gráfica já existem, mas uma janela gráfica ainda não foi implementada.
Não há aplicação ou servidor web na arquitetura do produto.

O projeto busca preservar:

* privacidade;
* controle operacional;
* segurança;
* auditabilidade;
* independência de serviços externos;
* funcionamento local sempre que tecnicamente possível;
* modularidade;
* portabilidade;
* substituibilidade de componentes;
* testabilidade;
* evolução incremental;
* comportamento previsível;
* compatibilidade controlada.

O Nexus Core não é projetado como um LLM com acesso irrestrito ao computador.

A arquitetura estabelece fronteiras explícitas entre:

```text
INTELIGÊNCIA
     │
     ▼
DECISÃO
     │
     ▼
AUTORIZAÇÃO
     │
     ▼
EXECUÇÃO
```

Um modelo pode interpretar informações e propor uma ação.

Isso não significa que o modelo possua autoridade para executá-la.

---

# Objetivo de longo prazo

O Nexus Core é projetado para evoluir para um assistente capaz de oferecer, de forma integrada:

* conversação por texto;
* conversação por voz;
* operação offline e online;
* modelos de IA locais;
* roteamento entre modelos;
* memória persistente;
* Knowledge Base;
* leitura de arquivos;
* análise de documentos;
* visão computacional;
* interpretação de imagens;
* interpretação de tela;
* pesquisa web;
* desenvolvimento de software assistido;
* automação controlada do desktop;
* geração de documentos;
* geração multimídia;
* integração com dispositivos externos;
* integração com Arduino;
* integração com ESP32;
* arquitetura distribuída entre computadores e dispositivos;
* interface gráfica multimodal.

Essas capacidades não são consideradas implementadas apenas por existirem no roadmap.

Cada release deve adicionar uma responsabilidade pequena, explícita, testável e arquiteturalmente revisável.

---

# Princípios de engenharia

O desenvolvimento do Nexus Core segue princípios que devem continuar válidos durante toda a evolução do projeto.

* **Local First**
* **Security First**
* **Privacy First**
* **Open Source**
* **Free Core**
* **Least Privilege**
* **Defense in Depth**
* **Fail-safe Defaults**
* **Modularidade**
* **Testabilidade**
* **Observabilidade**
* **Auditabilidade**
* **Determinismo quando aplicável**
* **Contratos explícitos**
* **Separação de responsabilidades**
* **Isolamento de falhas**
* **Compatibilidade controlada**
* **Regressão automatizada**
* **Configuração explícita**
* **Scope Control**
* **Evolução incremental**
* **Portabilidade**
* **Substituibilidade de componentes**

Segurança não é tratada como funcionalidade adicionada posteriormente.

Ela faz parte da fundação arquitetural.

---

# Open Source, gratuito e sem quotas comerciais artificiais

O Nexus Core é concebido com a intenção de ser totalmente open source.

O core não deve depender estruturalmente de:

* assinatura obrigatória;
* créditos;
* saldo comercial de tokens;
* billing obrigatório;
* API proprietária obrigatória;
* conta externa obrigatória;
* vendor lock-in;
* quota comercial artificial.

O produto também não deve introduzir limites comerciais como:

```text
N perguntas por dia
N mensagens por mês
N imagens por usuário
saldo de créditos
tokens comerciais
limite por assinatura
```

Limites técnicos continuam existindo.

Exemplos:

* RAM disponível;
* armazenamento;
* capacidade de CPU;
* tamanho da context window;
* tempo de inferência;
* tamanho de arquivo;
* limites de segurança;
* recursos disponíveis no dispositivo.

Esses limites devem ser tratados tecnicamente através de mecanismos como:

* chunking;
* filas;
* paginação;
* indexação;
* compressão de contexto;
* memória persistente;
* cache local;
* gestão de armazenamento;
* processamento incremental.

O objetivo é:

> **nenhuma quota comercial artificial imposta pelo Nexus Core.**

---

# Critérios para tecnologias externas

Uma tecnologia candidata ao Nexus deve ser avaliada considerando:

* disponibilidade do código-fonte;
* licença;
* possibilidade de uso gratuito;
* execução local quando aplicável;
* suporte a Linux;
* ausência de assinatura obrigatória;
* ausência de API obrigatória;
* ausência de lock-in estrutural;
* comunidade ativa;
* manutenção ativa;
* auditabilidade;
* automatização;
* possibilidade de substituição.

Model weights devem ser avaliados separadamente.

Um modelo disponível gratuitamente não é automaticamente open source.

A licença dos pesos e o model card devem ser auditados antes de distribuição pública ou integração definitiva.

---

# Estado atual

A linha `v0.3.1` inclui a abstração de modelos, a identidade visual desktop
(`v0.3.1.1`), a fundação PostgreSQL (`v0.3.1.2`) e correções de configuração
(`v0.3.1.3`). A release `v0.3.2` introduz a mediação explícita de caminhos do
host antes de executar ferramentas. Cada tag preserva o snapshot da sua versão.

O PostgreSQL local é o único provider de banco configurado para produção.
A aplicação exige `NEXUS_DATABASE_PASSWORD` no processo de composição,
conecta no `initialize()`, cria `system_events` e fecha a conexão no
`shutdown()`. O banco não é memória persistente do assistente.

A `v0.3.1` evolui a Local Model Layer introduzida na `v0.3.0`.

A principal mudança é a separação entre:

```text
contrato genérico de modelo

e

implementação concreta Ollama
```

O fluxo principal passa a ser:

```text
NexusApplication
        │
        ▼
ModelRouter
        │
        ▼
ModelProvider
        │
        ▼
OllamaProvider
        │
        ▼
OllamaTransport
        │
        ▼
Ollama
        │
        ▼
Local Model
```

A `v0.3.1` registra apenas:

```text
provider_id = "ollama"
```

na composição de produção.

A abstração permite evolução futura sem introduzir nesta release:

* provider online;
* API paga;
* credenciais;
* fallback;
* balanceamento;
* heurísticas;
* seleção por IA;
* descoberta dinâmica.

---

# Entregas da v0.3.1

A `v0.3.1 — Provider Abstraction & Model Routing` introduz:

* `ModelError`;
* `ModelValidationError`;
* `ModelProtocolError`;
* `ModelProviderError`;
* `ModelProviderUnavailableError`;
* `ModelProviderTimeoutError`;
* `ModelRequest`;
* `ModelResponse`;
* `ModelProvider`;
* `OllamaProvider`;
* `ModelRouter`;
* `ModelRoutingError`;
* erros específicos de routing;
* `build_model_router()`;
* composição provider-agnostic;
* normalização de erros de provider;
* runtime validation no boundary do router;
* provider padrão explícito;
* seleção explícita por `provider_id`;
* `model_layer` como API genérica de health;
* label genérico `Model Layer`;
* compatibilidade controlada com a API `LocalModel*` da `v0.3.0`;
* preservação da composição lazy;
* preservação do comportamento local-first;
* preservação da independência entre Model Layer e conectividade externa;
* preservação da separação entre Model Layer e Tool System;
* 493 testes automatizados passando.

---

# O que a v0.3.1 não implementa

A release deliberadamente **não** implementa:

* providers cloud;
* OpenAI provider;
* Anthropic provider;
* Gemini provider;
* APIs pagas;
* API keys;
* credenciais;
* fallback automático;
* retry inteligente;
* model discovery;
* provider discovery;
* provider availability probes;
* seleção baseada em custo;
* seleção baseada em latência;
* seleção aleatória;
* load balancing;
* model registry dinâmico;
* streaming;
* vision models;
* audio models;
* Agent;
* Planner;
* tool calling pelo modelo;
* memória persistente;
* Knowledge Base;
* self-update;
* dependency repair;
* automatic environment bootstrap.

Essas capacidades devem ser introduzidas por releases próprias.

---

# Baseline atual

```text
Release Target:       v0.3.3
Capability:           Explicit human confirmation
Tests:                veja a seção Testes abaixo
Primary Platform:     Linux
Runtime Baseline:     Python 3.12
Database:             PostgreSQL (loopback)
Sandbox:              Docker
Local Model Runtime:  Ollama
Reference Model:      qwen3:1.7b
Model Provider:       OllamaProvider
Model Router:         ModelRouter
Development Status:   ACTIVE
```

O baseline funcional é:

> **Linux systems with constrained compute resources; no dependency on dedicated GPU.**

GPU pode melhorar desempenho, mas não é requisito estrutural da arquitetura atual.

---

# Arquitetura atual

```text
NEXUS CORE
│
├── Configuration Boundary
│   │
│   ├── Environment
│   ├── load_settings()
│   │   ├── parsing
│   │   ├── normalization
│   │   ├── validation
│   │   └── controlled overrides
│   │
│   ├── Local HTTP Origin Policy
│   │   └── loopback-only validation
│   │
│   └── Settings(frozen=True)
│
├── NexusApplication
│   │
│   ├── Logger
│   ├── Database
│   ├── EventBus
│   ├── ConnectivityManager
│   ├── ConnectivityRuntimeEvaluator
│   ├── ConnectivityMonitor
│   ├── RuntimeStateController
│   ├── HealthStatus
│   ├── ModelRouter
│   ├── SecurityGate
│   ├── ToolRegistry
│   └── ToolExecutor
│
├── Model Layer
│   │
│   ├── ModelRequest
│   ├── ModelResponse
│   ├── ModelProvider
│   ├── ModelRouter
│   ├── OllamaProvider
│   ├── OllamaTransport
│   ├── build_model_router()
│   │
│   └── Compatibility Layer
│       ├── LocalModelRequest
│       ├── LocalModelResponse
│       ├── LocalModelValidationError
│       ├── LocalModelProtocolError
│       ├── LocalModelClient
│       └── build_local_model_client()
│
├── Security Layer
│   │
│   ├── SecurityGate
│   ├── SecurityPolicy
│   ├── PathSecurity
│   ├── ToolPermissionPolicy
│   ├── AuditLogger
│   └── RiskLevel
│
└── Tool System
    │
    ├── NexusTool
    ├── ToolResult
    ├── ToolRegistry
    ├── ToolExecutor
    ├── ListDirectoryTool
    ├── ReadFileTool
    ├── SystemInfoTool
    └── TerminalSandboxTool
        └── Docker
```

---

# Model Layer

A Model Layer representa a fronteira entre o Nexus Core e sistemas de inferência.

Na `v0.3.1`, os contratos principais são provider-agnostic.

---

## `ModelRequest`

`ModelRequest` é um dataclass imutável.

Campos:

```text
prompt
system_prompt
temperature
context_length
think
```

Defaults:

```text
system_prompt = None
temperature = 0.0
context_length = 2048
think = False
```

### `prompt`

Deve ser uma `str` não vazia.

Strings compostas apenas por whitespace são rejeitadas.

### `system_prompt`

Pode ser `None` ou `str` não vazia.

### `temperature`

Deve ser um número finito maior ou igual a zero.

`bool` não é tratado como número válido.

### `context_length`

Deve ser:

```text
int >= 1
```

### `think`

Deve ser:

```text
bool
```

---

# `ModelResponse`

Campos:

```text
content
model
done
prompt_tokens
output_tokens
```

Regras principais:

```text
content        -> str não vazia
model          -> str não vazia
done           -> bool
prompt_tokens  -> int >= 0
output_tokens  -> int >= 0
```

Para a integração não-streaming atual:

```text
done != True
```

representa protocolo incompleto.

---

# `ModelProvider`

`ModelProvider` é um `typing.Protocol` estrutural e `runtime_checkable`.

Contrato conceitual:

```python
@property
def provider_id(self) -> str:
    ...

def generate(
    self,
    request: ModelRequest,
) -> ModelResponse:
    ...
```

A abstração define o que o Nexus espera de um provider.

Ela não determina:

* transporte;
* protocolo externo;
* modelo;
* hardware;
* mecanismo de inferência.

---

# `ModelRouter`

`ModelRouter` é responsável por resolver providers de maneira determinística.

Responsabilidades:

* registrar providers;
* validar contrato estrutural;
* rejeitar provider inválido;
* rejeitar IDs duplicados;
* validar o provider padrão;
* resolver provider explicitamente;
* utilizar provider default;
* validar `ModelRequest`;
* validar `ModelResponse`.

```text
ModelRequest
     │
     ▼
ModelRouter
     │
     ├── provider_id explícito
     │
     └── default_provider_id
             │
             ▼
       ModelProvider
```

---

## Política do router

O router atual não realiza:

```text
fallback
retry policy
provider discovery
model discovery
availability probing
load balancing
cost routing
latency routing
random selection
AI-based selection
```

Essa simplicidade é intencional.

O routing deve permanecer previsível e auditável.

---

# `OllamaProvider`

`OllamaProvider` é a implementação concreta utilizada na `v0.3.1`.

Identificador:

```text
ollama
```

Responsabilidades:

```text
ModelRequest
     │
     ▼
Ollama payload
     │
     ▼
OllamaTransport
     │
     ▼
raw Ollama response
     │
     ▼
protocol validation
     │
     ▼
ModelResponse
```

O provider conhece:

* semântica da API Ollama;
* mensagens;
* `num_ctx`;
* `temperature`;
* `think`;
* estrutura da resposta;
* conclusão não-streaming;
* mapeamento de erros.

O provider não implementa HTTP diretamente.

---

# `OllamaTransport`

`OllamaTransport` é responsável pela comunicação HTTP concreta.

Endpoint:

```text
POST /api/chat
```

Responsabilidades:

* requisição HTTP;
* JSON encode;
* JSON decode;
* timeout;
* erros de conexão;
* erros HTTP;
* JSON inválido.

A fronteira permanece:

```text
HTTP / urllib
     │
     ▼
OllamaTransport
```

e não:

```text
ModelRouter → HTTP

ModelProvider → HTTP

NexusApplication → HTTP Ollama
```

---

# Taxonomia de erros da Model Layer

```text
ModelError
│
├── ModelValidationError
│
├── ModelProtocolError
│
├── ModelProviderError
│   ├── ModelProviderUnavailableError
│   └── ModelProviderTimeoutError
│
└── ModelRoutingError
    ├── InvalidModelProviderError
    ├── InvalidModelProviderIdError
    ├── UnknownModelProviderError
    └── DuplicateModelProviderError
```

`ModelValidationError` preserva compatibilidade com `ValueError`.

Erros de protocolo, provider e routing preservam semântica compatível com `RuntimeError` quando definida pelo contrato.

---

# Normalização de erros Ollama

```text
OllamaUnavailableError
        │
        ▼
ModelProviderUnavailableError
```

```text
OllamaTimeoutError
        │
        ▼
ModelProviderTimeoutError
```

```text
OllamaHTTPError
        │
        ▼
ModelProviderError
```

```text
OllamaInvalidJSONError
        │
        ▼
ModelProtocolError
```

A causa original é preservada por exception chaining.

---

# Compatibilidade com v0.3.0

A `v0.3.1` preserva:

```text
LocalModelRequest
LocalModelResponse
LocalModelValidationError
LocalModelProtocolError
LocalModelClient
build_local_model_client()
```

Aliases:

```text
LocalModelRequest is ModelRequest

LocalModelResponse is ModelResponse

LocalModelValidationError is ModelValidationError

LocalModelProtocolError is ModelProtocolError
```

---

## `LocalModelClient`

`LocalModelClient` permanece como facade de compatibilidade.

Novo código deve preferir:

```text
ModelRouter
ModelProvider
ModelRequest
ModelResponse
```

O facade delega a semântica Ollama ao:

```text
OllamaProvider
```

e preserva os atributos históricos:

```text
model
transport
timeout
```

---

## Compatibilidade de erros do client legado

Na `v0.3.0`, erros originados no transporte podiam escapar diretamente pelo `LocalModelClient`.

A `v0.3.1` preserva esse comportamento no facade legado.

```text
NOVO CAMINHO

ModelRouter
   → OllamaProvider
   → erros Model*
```

```text
CAMINHO LEGADO

LocalModelClient
   → OllamaProvider
   → recupera OllamaTransportError original
   → preserva superfície v0.3.0
```

---

# Factory da Model Layer

Factory principal:

```python
build_model_router(settings)
```

Composição:

```text
OllamaTransport
      │
      ▼
OllamaProvider
      │
      ▼
ModelRouter
```

Produção:

```text
providers = [OllamaProvider]
default_provider_id = "ollama"
```

A criação da composição não realiza inferência.

---

# Composição lazy

```text
NexusApplication()
       │
       ├── _model_router = None
       │
       └── nenhum contato com Ollama
```

No primeiro acesso:

```text
app.model_router
       │
       ▼
build_model_router(settings)
       │
       ▼
ModelRouter
```

O backend só é utilizado quando uma geração é solicitada.

---

# Compatibilidade `local_model_client` no Application

`NexusApplication` mantém:

```python
app.local_model_client
```

como propriedade de compatibilidade.

Na `v0.3.1`, ela resolve o provider Ollama através do router.

Não existe uma segunda composição paralela de Model Layer.

---

# Modelo técnico de referência

```text
qwen3:1.7b
```

É o baseline técnico da camada local atual.

A licença dos pesos deve ser auditada separadamente da futura licença do Nexus Core.

---

# Backend local

```text
Ollama
```

O Nexus Core atualmente:

* não instala Ollama;
* não inicia o daemon;
* não encerra o daemon;
* não instala modelos automaticamente;
* não executa model discovery;
* não carrega modelo no startup;
* não executa inferência no startup;
* não executa probe automático de provider;
* não assume ownership do lifecycle do serviço.

---

# Endpoint local

Default:

```text
http://127.0.0.1:11434
```

A configuração permite somente origem HTTP loopback.

São rejeitados:

* HTTPS;
* hosts externos;
* hosts LAN;
* credenciais;
* custom paths;
* query;
* fragment;
* porta inválida.

---

# Health da Model Layer

API principal:

```python
health.model_layer
```

O campo histórico:

```python
health.local_model_layer
```

é preservado para compatibilidade sobre o mesmo estado.

---

## Semântica

```text
Model Layer ✓ READY
```

significa readiness estrutural da camada de software.

Não significa:

* Ollama liveness;
* modelo instalado;
* modelo carregado;
* inferência bem-sucedida;
* provider saudável.

---

# Painel de status

O label atual é:

```text
Model Layer
```

Exemplo conceitual:

```text
╔══════════════════════════════════════════════╗
║                  N E X U S                   ║
║                    v0.3.1                    ║
╠══════════════════════════════════════════════╣
║ Core              ✓ ONLINE                  ║
║ Configuration     ✓ READY                   ║
║ Database          ✓ READY                   ║
║ Logger            ✓ READY                   ║
║ EventBus          ✓ READY                   ║
║ SecurityGate      ✓ READY                   ║
║ ToolRegistry      ✓ READY                   ║
║ Terminal Sandbox  ✓ READY                   ║
║ Model Layer       ✓ READY                   ║
╠══════════════════════════════════════════════╣
║ Health Monitor    ✓ READY                   ║
╠══════════════════════════════════════════════╣
║ Node              ...                       ║
║ Network           ...                       ║
║ Mode              ...                       ║
╚══════════════════════════════════════════════╝
```

---

# Configuração

Configuração principal:

```python
Settings(frozen=True)
```

Defaults relevantes:

```text
node_name                              NEXUS-NODE-01
offline_mode                           True
connectivity_monitor_interval          30.0
connectivity_confirmation_threshold    2
local_model_name                       qwen3:1.7b
local_model_base_url                   http://127.0.0.1:11434
local_model_timeout                    120.0
```

---

# Variáveis de ambiente

```text
NEXUS_NODE_NAME
NEXUS_OFFLINE_MODE
NEXUS_CONNECTIVITY_MONITOR_INTERVAL
NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD
NEXUS_LOCAL_MODEL_NAME
NEXUS_LOCAL_MODEL_BASE_URL
NEXUS_LOCAL_MODEL_TIMEOUT
```

---

# Configurações deliberadamente ausentes na v0.3.1

Não existe:

```text
NEXUS_MODEL_PROVIDER
NEXUS_PROVIDER_FALLBACK
NEXUS_OPENAI_API_KEY
NEXUS_ANTHROPIC_API_KEY
NEXUS_GEMINI_API_KEY
```

Existe apenas um provider de produção:

```text
ollama
```

---

# Runtime e conectividade

Fluxo:

```text
ConnectivityManager
       │
       ▼
network_online
       │
       ▼
ConnectivityRuntimeEvaluator
       │
       ▼
ONLINE / OFFLINE / DEGRADED
       │
       ▼
RuntimeStateController
```

Estados:

```text
ONLINE
OFFLINE
DEGRADED
```

---

# Semântica de DEGRADED

Com threshold default `2`:

```text
ONLINE
   │
   │ primeira observação OFFLINE
   ▼
DEGRADED
   │
   │ segunda observação OFFLINE
   ▼
OFFLINE
```

e:

```text
OFFLINE
   │
   │ primeira observação ONLINE
   ▼
DEGRADED
   │
   │ segunda observação ONLINE
   ▼
ONLINE
```

`DEGRADED` não representa automaticamente falha da Model Layer.

---

# Event Architecture

O Nexus possui:

```text
NexusEvent
EventBus
EventType
```

O EventBus suporta:

* subscribe;
* unsubscribe;
* publish;
* clear;
* contagem de handlers;
* sincronização interna.

O catálogo contém tipos para capacidades atuais e futuras.

A existência de um tipo de evento não implica implementação da funcionalidade correspondente.

---

# Database

Runtime atual:

```text
PostgreSQL local (Psycopg 3)
```

Tabela estrutural:

```text
system_events
```

Campos:

```text
id
event_type
message
created_at
```

O database atual não representa a futura Persistent Memory.

O provider é construído sem I/O; a conexão e a criação da tabela ocorrem
durante `initialize()`. Um PostgreSQL acessível no loopback, um usuário e
um banco já criados são pré-requisitos para executar `nexus.main`.

Configuração por ambiente:

| Variável | Padrão | Regra |
| --- | --- | --- |
| `NEXUS_DATABASE_PROVIDER` | `postgresql` | Único provider suportado |
| `NEXUS_DATABASE_HOST` | `127.0.0.1` | Somente `127.0.0.1`, `localhost` ou `::1` |
| `NEXUS_DATABASE_PORT` | `5432` | Porta de 1 a 65535 |
| `NEXUS_DATABASE_NAME` | `nexus` | Nome não vazio |
| `NEXUS_DATABASE_USER` | `nexus` | Usuário não vazio |
| `NEXUS_DATABASE_PASSWORD` | sem valor | Obrigatória ao compor a aplicação; não é registrada em logs |
| `NEXUS_DATABASE_CONNECT_TIMEOUT` | `5.0` | Segundos, número finito maior que zero |

Guarde a senha fora do repositório e forneça-a ao processo antes da execução.

---

# Logging

Logging principal:

* console;
* arquivo;
* biblioteca padrão;
* formato estruturado.

O security audit log é separado.

---

# Security Architecture

Princípio:

```text
Modelo propõe.

SecurityGate autoriza.

ToolExecutor executa.
```

Arquitetura planejada:

```text
Model Layer
     │
     ▼
Agent / Planner
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

# SecurityGate

Uma `SecurityRequest` possui:

```text
action
description
risk_level
data
tool_name
resources
path (compatibilidade para chamadas diretas antigas)
```

Avaliação:

1. tool registration;
2. tool permission;
3. validação de cada recurso declarado pela ferramenta;
4. risk policy;
5. audit.

Decisões:

```text
ALLOW
CONFIRM
DENY
```

Cada ferramenta interna declara `sensitive_resources(**kwargs)`: caminhos
de arquivo, diretório e workspace são avaliados antes de `execute()`.
Declarações ausentes ou inválidas são negadas e auditadas. A decisão
`CONFIRM` exige uma resposta humana explícita antes de executar. Uma recusa,
ausência de terminal ou falha na confirmação bloqueia a chamada; a política
e os recursos são revalidados após a resposta. A decisão e o resultado da
execução ficam no log de auditoria. O código de ferramentas internas é confiável;
uma ferramenta externa que declare falsamente seus recursos exige revisão
antes de ser registrada.

---

# Path Security

A política protege diretórios críticos como:

```text
/boot
/etc
/bin
/sbin
/usr
/var
/root
/sys
/proc
/dev
/run
/lib
/lib64
/opt
/srv
/snap
```

e áreas sensíveis do usuário:

```text
~/.ssh
~/.gnupg
~/.aws
~/.docker
~/.kube
~/.config
~/.local/share/keyrings
```

---

# Audit Log

Registra:

```text
timestamp
tool_name
action
risk_level
decision
reason
path
outcome
```

Outcomes de execução:

```text
SUCCESS
ERROR
EXCEPTION
```

---

# Tool Architecture

```text
NexusTool
    │
    ├── name
    ├── description
    ├── risk_level
    └── execute()
```

Ferramentas implementadas:

```text
ListDirectoryTool
ReadFileTool
SystemInfoTool
TerminalSandboxTool
```

---

# Terminal Sandbox

O `TerminalSandboxTool` executa comandos em Docker.

Configuração atual inclui:

```text
image: ubuntu:24.04
network: none
root filesystem: read-only
/tmp: tmpfs
memory: 256 MiB
CPU: 0.5
PIDs: 64
no-new-privileges
capabilities: dropped
user: 1000:1000
timeout: 30 seconds
output limit: 64 KiB
```

Workspace opcional é montado:

```text
/workspace
```

como read-only.

---

# Mediação de recursos da v0.3.2

Fluxo implementado para as ferramentas internas:

```text
Tool
   │
   ├── declara caminhos do host usados nesta chamada
   ▼
ToolExecutor
   │
   ▼
SecurityGate
   │
   ▼
PathSecurity / policies
```

`ListDirectoryTool` declara inclusive o default `.`;
`ReadFileTool` declara o arquivo; `TerminalSandboxTool` declara o
`workspace` quando fornecido; `SystemInfoTool` declara explicitamente
nenhum caminho. Um symlink que resolve para fora da área permitida é negado.
As chamadas devem entrar por `ToolExecutor`; invocar diretamente
`tool.execute()` é uso interno fora da fronteira de autorização.

---

# Prompt Injection

Conteúdo de:

* web;
* PDFs;
* documentos;
* imagens;
* arquivos;
* páginas;
* mensagens externas;

deve ser considerado:

```text
UNTRUSTED DATA
```

Ação proposta por conteúdo externo não equivale a autorização.

---

# Dependências

## Runtime Python

A `v0.3.1` não adiciona dependência Python externa obrigatória ao runtime principal.

`requirements/base.txt` permanece sem pacotes externos.

---

## Desenvolvimento

```text
pytest==9.1.1
```

Instalação:

```bash
python -m pip install -r requirements/dev.txt
```

---

## Dependências externas por capacidade

Inferência:

```text
Ollama
```

Terminal sandbox:

```text
Docker
```

---

# Instalação

Baseline:

```text
Linux
Python 3.12
Git
PostgreSQL local
```

Desenvolvimento:

```text
pytest
```

Inferência:

```text
Ollama
```

Sandbox:

```text
Docker
```

GPU dedicada não é requisito arquitetural.

---

# Ambiente virtual

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
```

---

# Ollama

Modelo baseline:

```bash
ollama pull qwen3:1.7b
```

Comandos úteis:

```bash
ollama list
ollama ps
ollama run qwen3:1.7b
```

---

# Executando o Nexus

`NEXUS_DATABASE_PASSWORD` deve estar definido e o PostgreSQL local deve
aceitar a conexão com o banco e o usuário configurados.

```bash
nexus-core
```

O entrypoint `python -m nexus.main` também está disponível a partir da
raiz do projeto. O comando usa o PostgreSQL local configurado e termina
com erro explícito quando ele não está disponível. Esta versão oferece
uma interface de terminal, não uma janela gráfica.

Para executar um comando no sandbox Docker, com aprovação presencial no
terminal e workspace opcional montado somente para leitura:

```bash
nexus-core --sandbox-command 'pwd' --workspace "$PWD"
```

O prompt mostra o comando e os recursos. Somente a resposta literal `sim`
autoriza aquela chamada; sem terminal interativo a operação é negada. O
PostgreSQL local deve estar disponível antes de iniciar a aplicação. Dados
e logs ficam no diretório do usuário conforme `XDG_DATA_HOME` e
`XDG_STATE_HOME` (padrões `~/.local/share/nexus-core` e
`~/.local/state/nexus-core/logs`).

---

# Exemplo de ModelRouter

```python
from nexus.config.settings import settings
from nexus.models.contracts import ModelRequest
from nexus.models.model_factory import build_model_router


router = build_model_router(settings)

response = router.generate(
    ModelRequest(
        prompt="Olá, Nexus.",
    )
)

print(response.content)
```

---

# Testes

Comando oficial:

```bash
PYTHONPATH="$PWD" pytest -q
```

Verificação nesta revisão (ambiente sem Docker e PostgreSQL de teste):

```text
549 passed; 8 skipped (7 integrações Docker e 1 PostgreSQL)
```

Coleta:

```text
557 tests collected
```

Os sete testes que executam containers são ignorados automaticamente
quando o daemon Docker não está disponível. Em um Linux com Docker
operacional, o mesmo comando também verifica o isolamento real. O teste
PostgreSQL real é executado quando `NEXUS_TEST_POSTGRES_PASSWORD` está
definido para o banco descartável `nexus_test` no loopback. A CI configura
esse serviço e executa a suíte em Linux com Docker.

---

# Estratégia de testes

A suíte prioriza:

* determinismo;
* isolamento;
* fake transports;
* fake providers;
* ausência de inferência real;
* validação de contratos;
* regressão;
* compatibilidade;
* lifecycle;
* concurrency;
* segurança;
* boundaries arquiteturais.

---

# Estrutura do projeto

```text
Nexus-Core/
│
├── README.md
│
├── requirements/
│   ├── base.txt
│   └── dev.txt
│
├── scripts/
│
├── nexus/
│   │
│   ├── brains/
│   ├── config/
│   ├── context/
│   ├── core/
│   ├── database/
│   ├── events/
│   ├── knowledge/
│   ├── memory/
│   │
│   ├── models/
│   │   ├── contracts.py
│   │   ├── local_model.py
│   │   ├── local_model_factory.py
│   │   ├── model_factory.py
│   │   ├── ollama_provider.py
│   │   ├── ollama_transport.py
│   │   ├── provider.py
│   │   └── router.py
│   │
│   ├── monitoring/
│   ├── security/
│   ├── tools/
│   └── main.py
│
└── tests/
```

Diretórios de scaffolding não representam capacidades concluídas.

---

# Histórico de releases

O histórico abaixo documenta a evolução incremental da arquitetura.

Cada release adiciona uma nova responsabilidade sem antecipar artificialmente capacidades das etapas seguintes.

---

## v0.1.0 — Foundation

### Objetivo

Criar a primeira fundação executável do Nexus Core.

### Entregue

* estrutura inicial do projeto;
* package `nexus`;
* organização modular inicial;
* configuração central;
* logging;
* database local;
* persistência local de eventos;
* arquitetura inicial da aplicação;
* diretórios de dados e logs;
* primeira separação entre infraestrutura e futuras capacidades de IA.

### Impacto arquitetural

A release estabeleceu a base sobre a qual os demais subsistemas passaram a ser adicionados.

Antes de agentes, modelos, memória ou automação, o projeto recebeu uma infraestrutura mínima capaz de:

```text
configurar
inicializar
registrar
persistir
encerrar
```

### Limites

Ainda não existiam:

* EventBus formal;
* SecurityGate;
* Tool System;
* runtime connectivity;
* modelos;
* Agent;
* memória.

---

## v0.1.1 — Infrastructure Core

### Objetivo

Consolidar a infraestrutura central criada na fundação.

### Entregue

* evolução do núcleo da aplicação;
* composição mais clara dos componentes de infraestrutura;
* lifecycle centralizado;
* endurecimento de logging e database;
* preparação para módulos desacoplados;
* separação progressiva de responsabilidades.

### Impacto arquitetural

A aplicação passou a ter uma base mais adequada para receber componentes independentes sem transformar o entrypoint em um monólito.

A direção passou a ser:

```text
NexusApplication
      │
      ├── Infrastructure Component A
      ├── Infrastructure Component B
      └── Future Components
```

### Limites

A release continuava focada em infraestrutura.

Ainda não introduzia autorização, tools ou inteligência.

---

## v0.1.2 — Event Architecture

### Objetivo

Criar uma arquitetura interna de comunicação desacoplada por eventos.

### Entregue

* `NexusEvent`;
* `EventBus`;
* catálogo de tipos de evento;
* subscribe;
* unsubscribe;
* publish;
* múltiplos handlers;
* desacoplamento entre produtores e consumidores;
* timestamps de evento;
* preparação para eventos de sistema, segurança, rede, tarefas e futuras capacidades.

### Impacto arquitetural

Componentes passaram a poder se comunicar sem referência direta entre si.

```text
Producer
   │
   ▼
EventBus
   │
   ├── Handler A
   ├── Handler B
   └── Handler C
```

Isso criou uma base importante para lifecycle, conectividade e observabilidade.

### Limites

A presença de eventos como voice, vision ou memory no catálogo não significava implementação dessas capacidades.

---

## v0.1.3 — Security Gate

### Objetivo

Criar a primeira fronteira central de autorização do Nexus Core.

### Entregue

* `SecurityGate`;
* `SecurityRequest`;
* `SecurityResult`;
* decisões explícitas de segurança;
* risk-based evaluation;
* separação entre solicitação e autorização;
* base para políticas de acesso;
* princípio de fail-safe authorization.

### Impacto arquitetural

Foi estabelecida a regra:

```text
operação potencialmente sensível
        │
        ▼
SecurityGate
        │
        ├── ALLOW
        ├── CONFIRM
        └── DENY
```

A partir dessa versão, autoridade operacional deixou de ser tratada como consequência implícita de uma chamada de função.

### Limites

Ainda faltavam:

* arquitetura formal de tools;
* path security;
* permissões específicas por ferramenta;
* audit log completo.

---

## v0.1.4 — Tool Architecture

### Objetivo

Criar uma camada formal para capacidades executáveis.

### Entregue

* `NexusTool`;
* `ToolResult`;
* `ToolRegistry`;
* `ToolExecutor`;
* nomes e descrições de tools;
* níveis de risco;
* registro explícito;
* lookup de ferramentas;
* execução controlada;
* integração inicial com o `SecurityGate`;
* rejeição de tool desconhecida.

### Impacto arquitetural

Foi criada a separação:

```text
Tool Definition
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
Execution
```

Essa arquitetura se tornaria posteriormente a base para tool calling controlado.

### Limites

Modelos ainda não participavam da cadeia.

---

## v0.1.5 — Path Security

### Objetivo

Evitar que operações de filesystem fossem autorizadas apenas pelo nome da tool.

### Entregue

* `PathSecurity`;
* resolução explícita de paths;
* delimitação de área autorizada;
* proteção de diretórios críticos do sistema;
* proteção de áreas sensíveis do usuário;
* rejeição de paths fora da região permitida;
* prevenção de acesso direto a caminhos protegidos.

### Impacto arquitetural

A autorização passou a considerar:

```text
ação
tool
risco
path
```

em vez de apenas:

```text
ação
```

Isso reduziu a superfície de acesso acidental ou indevido ao host.

### Limites

A mediação ainda depende do recurso ser corretamente representado no `SecurityRequest`.

Na `v0.3.2`, as ferramentas internas passaram a declarar os recursos
usados em cada chamada, e o executor nega declarações ausentes.

---

## v0.1.6 — Tool Permissions + Audit Log

### Objetivo

Adicionar governança explícita por ferramenta e rastreabilidade.

### Entregue

* `ToolPermissionPolicy`;
* registro individual de tools;
* maximum risk por ferramenta;
* rejeição de tools não registradas;
* `AuditLogger`;
* registros de decisão;
* timestamps UTC;
* razão da decisão;
* tool name;
* action;
* risk level;
* path quando aplicável;
* base para rastreamento de execução.

### Impacto arquitetural

O SecurityGate passou a combinar:

```text
Tool Permission
       +
Path Security
       +
Risk Policy
       +
Audit
```

Essa versão estabeleceu auditabilidade como requisito de arquitetura, e não apenas debugging.

---

## v0.1.7 — Secure File Tools

### Objetivo

Introduzir as primeiras ferramentas reais de filesystem sob a arquitetura de segurança.

### Entregue

* `ListDirectoryTool`;
* `ReadFileTool`;
* integração das file tools ao Tool System;
* leitura de arquivos de texto;
* validação de existência;
* validação de tipo;
* tratamento de permission errors;
* tratamento de filesystem errors;
* limite de tamanho para leitura;
* rejeição de conteúdo não UTF-8;
* mediação de path pelo fluxo de segurança.

### Impacto arquitetural

Pela primeira vez, a cadeia:

```text
ToolRegistry
      │
      ▼
ToolExecutor
      │
      ▼
SecurityGate
      │
      ▼
PathSecurity
      │
      ▼
Filesystem Tool
```

passou a operar sobre recursos reais.

### Limites

As ferramentas eram deliberadamente restritas.

Não existia shell livre ou automação de desktop.

---

## v0.1.8 — Terminal Sandbox

### Objetivo

Adicionar execução de comandos sem conceder shell irrestrito no host.

### Entregue

* `TerminalSandboxTool`;
* execução dentro de Docker;
* isolamento do host;
* ausência de rede no container;
* root filesystem read-only;
* `/tmp` temporário;
* limites de recursos;
* limite de processos;
* timeout;
* captura controlada de stdout/stderr;
* limite de output;
* remoção do container após execução;
* risk level superior às file tools;
* integração com o modelo de autorização.

### Impacto arquitetural

O projeto passou a separar:

```text
comando solicitado

de

execução direta no host
```

A direção passou a ser:

```text
Command
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

### Limites

O sandbox não representa autorização automática.

A política default continua tratando operações `MEDIUM` como dependentes de confirmação.

---

## v0.1.9 — Health Check & Application Status

### Objetivo

Tornar o estado estrutural da aplicação observável.

### Entregue

* `HealthStatus`;
* readiness estrutural;
* status dos principais componentes;
* painel textual;
* lifecycle de status;
* integração de health com `NexusApplication`;
* shutdown garantido pelo entrypoint;
* visualização operacional do estado do core.

### Impacto arquitetural

O projeto ganhou uma projeção explícita de estado:

```text
Core
Configuration
Database
Logger
EventBus
SecurityGate
ToolRegistry
Terminal Sandbox
Health Monitor
```

Essa camada posteriormente passou a incorporar runtime connectivity e Model Layer.

---

# Série v0.2.x — Runtime e conectividade

A série `v0.2.x` transformou conectividade em um subsistema formal de runtime.

---

## v0.2.0 — Connectivity & Runtime Modes

### Objetivo

Introduzir observação de conectividade externa e modos formais de execução.

### Entregue

* `ConnectivityManager`;
* `ConnectivityStatus`;
* `RuntimeMode`;
* `ONLINE`;
* `OFFLINE`;
* `DEGRADED`;
* `offline_mode`;
* eventos de conectividade;
* determinação inicial do runtime;
* separação inicial entre execução local e disponibilidade externa.

### Impacto arquitetural

Foi criada a distinção:

```text
Nexus running
```

não implica:

```text
Internet available
```

A aplicação passou a possuir semântica explícita de operação online e offline.

### Baseline histórico

```text
87 tests passing
```

---

## v0.2.1 — Runtime State Controller

### Objetivo

Substituir estado de runtime disperso por uma fonte autoritativa.

### Entregue

* `RuntimeStateController`;
* estado centralizado;
* `mode`;
* `reason`;
* `changed_at`;
* transições formais;
* validação de transições;
* integração com a aplicação;
* preservação dos eventos iniciais;
* base para snapshots e concorrência futura.

### Impacto arquitetural

O runtime passou a seguir:

```text
Observation
     │
     ▼
RuntimeStateController
     │
     ▼
Authoritative Runtime State
```

Em vez de múltiplos componentes manterem interpretações independentes do estado.

### Baseline histórico

```text
97 tests passing
```

---

## v0.2.2 — Continuous Connectivity Monitoring

### Objetivo

Transformar conectividade de uma verificação pontual em monitoramento contínuo.

### Entregue

* `ConnectivityMonitor`;
* worker `Nexus-ConnectivityMonitor`;
* polling periódico;
* intervalo configurável;
* snapshots;
* sincronização de health;
* locks;
* stop event;
* shutdown responsivo;
* lifecycle endurecido;
* isolamento de falhas;
* monitor independente do fluxo principal da aplicação.

### Impacto arquitetural

A conectividade passou de:

```text
startup check
```

para:

```text
startup check
      +
continuous observation
```

O monitor passou a alimentar o runtime sem bloquear a aplicação principal.

### Baseline histórico

```text
134 tests passing
```

---

## v0.2.3 — Automatic DEGRADED Runtime Detection

### Objetivo

Evitar mudanças de estado instáveis causadas por uma única observação divergente.

### Entregue

* `ConnectivityRuntimeEvaluator`;
* `ConnectivityRuntimeEvaluation`;
* `DEGRADED` automático;
* confirmação simétrica;
* confirmation threshold;
* threshold default `2`;
* cancelamento de mudança pendente;
* tratamento de oscilação;
* separação de rede e runtime;
* eventos independentes;
* serialização de ciclos;
* invariants de inicialização;
* interpretação determinística da conectividade.

### Impacto arquitetural

Foi estabelecido o modelo:

```text
raw observation
      │
      ▼
runtime interpretation
      │
      ▼
stable state
```

Uma única divergência passa temporariamente por:

```text
DEGRADED
```

antes de alterar o estado estável.

### Exemplo

```text
ONLINE
   │
   │ 1ª observação OFFLINE
   ▼
DEGRADED
   │
   │ 2ª observação OFFLINE
   ▼
OFFLINE
```

### Baseline histórico

```text
151 tests passing
```

---

## v0.2.4 — Environment & Runtime Configuration

### Objetivo

Transformar configuração em um boundary formal, validado e determinístico.

### Entregue

* `ConfigurationError`;
* `load_settings()`;
* leitura controlada de `os.environ`;
* mappings explícitos para testes;
* `Settings(frozen=True)`;
* defaults centralizados;
* allowlist de environment variables;
* parsing booleano estrito;
* parsing numérico;
* normalização;
* validação;
* fail-fast;
* proteção de paths;
* proteção de version;
* proteção de app name;
* testes determinísticos;
* nenhuma dependência Python adicional;
* nenhum `.env` automático;
* nenhum `python-dotenv`;
* nenhum perfil artificial;
* nenhum reload dinâmico.

### Impacto arquitetural

Configuração deixou de ser estado global mutável informal e passou a seguir:

```text
Environment
     │
     ▼
parse
     │
     ▼
normalize
     │
     ▼
validate
     │
     ▼
Settings(frozen=True)
```

### Baseline histórico

```text
184 tests passing
```

---

# Série v0.3.x — Inteligência e Model Layer

A série `v0.3.x` introduz inteligência local sem romper a fronteira entre inteligência e autoridade operacional.

---

## v0.3.0 — Local Model Layer

### Objetivo

Introduzir a primeira integração formal de um modelo de linguagem local ao Nexus Core.

### Entregue

* `LocalModelRequest`;
* `LocalModelResponse`;
* contratos imutáveis;
* validação tipada;
* `LocalModelValidationError`;
* `LocalModelProtocolError`;
* `LocalModelClient`;
* request boundary explícito;
* payload não-streaming;
* system prompt;
* temperature;
* context length;
* `think`;
* model name;
* timeout;
* parsing de resposta;
* validação de resposta final;
* rejeição de `done=False`;
* `OllamaTransport`;
* `OllamaTransportError`;
* `OllamaUnavailableError`;
* `OllamaTimeoutError`;
* `OllamaHTTPError`;
* `OllamaInvalidJSONError`;
* integração com `/api/chat`;
* JSON pela biblioteca padrão;
* endpoint HTTP local;
* política loopback-only;
* bloqueio de hosts externos;
* bloqueio de LAN;
* bloqueio de credentials;
* bloqueio de custom paths;
* bloqueio de query;
* bloqueio de fragments;
* `NEXUS_LOCAL_MODEL_NAME`;
* `NEXUS_LOCAL_MODEL_BASE_URL`;
* `NEXUS_LOCAL_MODEL_TIMEOUT`;
* `build_local_model_client()`;
* composição lazy;
* integração com `NexusApplication`;
* health estrutural;
* label `Local Model Layer`;
* operação compatível com forced offline;
* nenhuma inferência durante startup;
* nenhuma inferência na suíte unitária;
* smoke tests reais separados;
* modelo técnico de referência `qwen3:1.7b`;
* backend técnico de referência Ollama;
* nenhuma autoridade direta sobre tools;
* nenhuma dependência Python externa adicional;
* regressão arquitetural completa.

### Arquitetura da release

```text
LocalModelRequest
        │
        ▼
LocalModelClient
        │
        ▼
OllamaTransport
        │
        ▼
HTTP loopback
        │
        ▼
Ollama
        │
        ▼
Local Model
```

### Princípios consolidados

#### Local First

Inferência através de backend local.

#### Contract First

Entrada e saída possuem contratos formais.

#### Runtime Validation

Type hints não são a única defesa.

#### Fail Explicitly

Falhas são diferenciadas entre:

```text
validation
protocol
transport
```

#### Resource Discipline

Startup não carrega o modelo.

#### Test Determinism

A suíte unitária não depende de LLM real.

#### Separation of Concerns

`LocalModelClient` não implementa HTTP.

`OllamaTransport` não define semântica do contrato de alto nível.

#### Security First

O modelo não recebe acesso às tools.

### Limites deliberados

A `v0.3.0` não introduziu:

* streaming;
* provider abstraction;
* model routing;
* online providers;
* Agent;
* Planner;
* tool calling;
* memory;
* Knowledge Base;
* voice;
* vision;
* desktop automation.

### Baseline histórico

```text
338 tests passing
```

---

## v0.3.1 — Provider Abstraction & Model Routing

### Status

```text
IMPLEMENTATION COMPLETE
RELEASED
```

### Objetivo

Remover o acoplamento conceitual entre a Model Layer e uma implementação concreta de provider sem adicionar cloud providers ou routing heurístico.

### Entregue

#### Contratos genéricos

* `ModelRequest`;
* `ModelResponse`;
* `ModelError`;
* `ModelValidationError`;
* `ModelProtocolError`;
* `ModelProviderError`;
* `ModelProviderUnavailableError`;
* `ModelProviderTimeoutError`.

#### Provider abstraction

* `ModelProvider`;
* `typing.Protocol`;
* `runtime_checkable`;
* `provider_id`;
* contrato estrutural `generate()`.

#### Ollama provider

* `OllamaProvider`;
* conversão `ModelRequest → Ollama payload`;
* conversão `Ollama response → ModelResponse`;
* protocolo não-streaming;
* validação de resposta;
* normalização de transport errors.

#### Model routing

* `ModelRouter`;
* provider registry;
* default provider;
* provider selection explícita;
* validação do provider;
* duplicate provider rejection;
* unknown provider rejection;
* request boundary validation;
* response boundary validation.

#### Routing errors

* `ModelRoutingError`;
* `InvalidModelProviderError`;
* `InvalidModelProviderIdError`;
* `UnknownModelProviderError`;
* `DuplicateModelProviderError`.

Toda a família de routing passa a pertencer à hierarquia:

```text
ModelError
```

#### Factory

* `build_model_router()`;
* composição `OllamaTransport → OllamaProvider → ModelRouter`;
* nenhuma conexão com backend durante construção.

#### NexusApplication

* `_model_router`;
* propriedade lazy `model_router`;
* única composição de provider;
* nenhum backend contact durante construção;
* nenhum backend contact obrigatório durante `initialize()`.

#### Health

API principal:

```text
model_layer
```

Compatibilidade:

```text
local_model_layer
```

ambas representando o mesmo backing state.

#### UI

Label atualizado:

```text
Model Layer
```

#### Compatibilidade v0.3.0

Preservados:

* `LocalModelRequest`;
* `LocalModelResponse`;
* `LocalModelValidationError`;
* `LocalModelProtocolError`;
* `LocalModelClient`;
* `build_local_model_client()`.

#### Compatibilidade de erros

O caminho genérico utiliza erros `Model*`.

O facade legado preserva os transport errors da `v0.3.0`.

```text
NEW

ModelRouter
   → OllamaProvider
   → Model* errors
```

```text
LEGACY

LocalModelClient
   → OllamaProvider
   → original OllamaTransportError
```

#### Arquitetura

```text
NexusApplication
        │
        ▼
ModelRouter
        │
        ▼
ModelProvider
        │
        ▼
OllamaProvider
        │
        ▼
OllamaTransport
        │
        ▼
Ollama
```

### Provider de produção

Somente:

```text
ollama
```

### Não implementado

A release deliberadamente não adiciona:

* online provider;
* cloud API;
* credenciais;
* fallback;
* availability probes;
* provider discovery;
* model discovery;
* load balancing;
* cost routing;
* latency routing;
* AI routing;
* streaming;
* Agent;
* Planner;
* tool calling.

### Segurança

A Model Layer continua sem dependência de:

```text
SecurityGate
ToolRegistry
ToolExecutor
TerminalSandboxTool
filesystem tools
```

Isso preserva:

```text
intelligence != authority
```

### Baseline validado

```text
493 tests passing
493 tests collected
```

---

## v0.3.1.1 — Desktop Visual Identity Foundation

Marca e iconografia desktop nativa Nexus Line em Wine Red (`#722F37`),
manifesto de 18 ícones e testes de integridade dos SVGs e do logotipo.
A identidade é um conjunto de assets; ainda não há interface gráfica.

## v0.3.1.2 — PostgreSQL Database Provider Foundation

Introduz `DatabaseProvider`, `PostgreSQLProvider`, a factory de composição,
configuração validada via ambiente e Psycopg 3. O serviço conecta durante a
inicialização, mantém `system_events` e fecha no encerramento. Testes
usam providers falsos quando não requerem o servidor PostgreSQL.

## v0.3.1.3 — Release Configuration Corrections

O commit etiquetado como `v0.3.1.3` corrigiu regressões dos testes de
configuração, mas ainda exibia `0.3.1.2` em `Settings.version` e mantinha
o README em `v0.3.1.1`. Esta revisão posterior no `main` alinha a versão
exibida, os testes e a documentação à implementação efetiva. A tag
existente não foi reescrita.

---

## v0.3.2 — Security Resource Mediation

Release concluída: declaração explícita dos caminhos sensíveis
por ferramenta, avaliação de todos pelo `SecurityGate`, mediação de
`TerminalSandboxTool.workspace` e do default de `ListDirectoryTool`,
negação de declarações ausentes ou inválidas, auditoria de todos os
caminhos e testes de escape por symlink. A Model Layer ainda não chama
ferramentas.

---

## v0.3.3 — Explicit Confirmation & Authorization

O `ToolExecutor` trata `CONFIRM` como uma autorização individual: solicita
decisão por um handler separado da Model Layer, registra aprovação ou recusa
e reavalia recursos e política após a resposta. Sem handler, sem terminal
visível, diante de erro ou de qualquer resposta diferente de `sim`, a
execução é negada. `DENY` nunca apresenta pedido de confirmação.

O comando Linux `nexus-core --sandbox-command` expõe o fluxo para o sandbox
Docker. Os logs e dados locais seguem os diretórios XDG do usuário. A CI
verifica Python 3.12, PostgreSQL real e a suíte Docker no Linux.

---

# Roadmap

O roadmap é evolutivo. Cada release adiciona uma responsabilidade
pequena, clara e verificável.

---

## v0.3.4 — Structured Tool Contracts

Objetivo:

formalizar contratos estruturados para ferramentas antes da integração com agentes.

Escopo planejado:

* definir entradas declaradas e validáveis;
* declarar recursos sensíveis explicitamente;
* declarar requisitos de permissão;
* estruturar resultados e erros;
* manter contratos auditáveis e independentes do modelo.

---

## v0.3.5 — Controlled Agent & Tool Calling

Objetivo:

introduzir o primeiro Agent/Planner controlado sobre as fronteiras de segurança já estabelecidas.

Arquitetura alvo:

```text
Model Layer
     │
     ▼
Agent / Planner
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

Pré-requisitos obrigatórios:

* `v0.3.2 — Security Resource Mediation`;
* `v0.3.3 — Explicit Confirmation & Authorization`;
* `v0.3.4 — Structured Tool Contracts`;
* nenhuma execução direta `ModelProvider → Tool`.

---

# Confiabilidade, bootstrap e updates

Sequência planejada:

```text
Environment Detection
        │
        ▼
Dependency Doctor
        │
        ▼
Bootstrap / Preflight
        │
        ▼
Update Manager
        │
        ▼
Self-Recovery
```

Estados desejados de diagnóstico:

```text
OK
MISSING
OUTDATED
INCOMPATIBLE
DEGRADED
ERROR
```

Updates não devem executar cegamente:

```text
sudo apt upgrade
root escalation
arbitrary package mutation
```

Fluxo desejado:

```text
Detect
  │
  ▼
Compare Compatibility
  │
  ▼
Plan
  │
  ▼
Update Authorized Component
  │
  ▼
Integrity Check
  │
  ▼
Smoke
  │
  ├── Accept
  └── Rollback / Degraded
```

---

# Memória e conhecimento

## v0.4.0 — Persistent Memory Foundation

Planejado:

* storage;
* schemas;
* persistência;
* recuperação;
* lifecycle;
* observabilidade.

---

## v0.4.1 — Knowledge Base

Planejado:

* ingestão;
* indexação;
* retrieval;
* documentos;
* integração com memória.

---

# Voz

## v0.5.x — Voice Foundation

Planejado:

```text
speech-to-text
wake word
text-to-speech
```

---

# Visão

## v0.6.x — Vision & Screen Understanding

Planejado:

* imagens;
* câmera;
* screen capture;
* screen understanding;
* visão multimodal.

---

# Automação

## v0.7.x — Controlled Desktop Automation

Planejado:

* interação com desktop;
* ações controladas;
* autorização;
* sandboxing;
* observabilidade.

---

# Hardware e distribuição

## v0.8.x — Devices & Distributed Architecture

Planejado:

* nodes;
* Arduino;
* ESP32;
* dispositivos;
* comunicação entre máquinas;
* arquitetura distribuída.

Para microcontroladores:

```text
C / C++
```

é a direção preferencial.

---

# Interface multimodal

## v0.9.x — Multimodal Interface

Planejado:

* desktop UI;
* chat;
* voz;
* visão;
* status;
* integração de dispositivos.

---

# v1.0 — Production Baseline

Objetivo:

* instalação reproduzível;
* segurança validada;
* recovery;
* documentação;
* observabilidade;
* interfaces estáveis;
* portabilidade;
* capacidades locais úteis.

---

# Tecnologias atuais

```text
Primary Platform:     Linux
Runtime:              Python 3.12
Database:             PostgreSQL (local, Psycopg 3)
Tests:                pytest
Sandbox:              Docker
Local Model Runtime:  Ollama
Reference Model:      qwen3:1.7b
Version Control:      Git
Remote:               GitHub
```

---

# Tecnologias candidatas futuras

```text
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

A presença na lista não representa decisão definitiva.

---

# Filosofia Local First

O Nexus Core deve continuar útil quando:

```text
Internet unavailable
```

Capacidades locais devem continuar locais quando isso for tecnicamente razoável.

---

# Privacidade

Princípios:

* processamento local quando viável;
* dados locais por default;
* nenhuma telemetria obrigatória;
* nenhuma API cloud obrigatória;
* nenhum envio silencioso de conteúdo;
* credenciais fora do código;
* integrações externas futuras explícitas e substituíveis.

---

# Observabilidade

O Nexus utiliza:

* logging;
* health;
* runtime state;
* snapshots;
* EventBus;
* security audit;
* erros explícitos.

---

# Fronteira entre inteligência e execução

Na `v0.3.1`:

```text
ModelRouter
     │
     ▼
ModelProvider
```

não está conectado a:

```text
ToolExecutor
SecurityGate
TerminalSandboxTool
Filesystem Tools
```

Essa separação é deliberada.

---

# Limitações atuais

Ainda não existem:

* Agent;
* Planner;
* tool calling por LLM;
* memória persistente;
* Knowledge Base;
* voz;
* visão;
* GUI;
* desktop automation;
* provider discovery;
* model discovery;
* provider health probes;
* fallback;
* streaming;
* cloud providers;
* dependency doctor;
* bootstrap automático;
* update manager;
* self-recovery;
* distributed nodes;
* device integration.

---

# Requirements e portabilidade

O projeto não deve ser documentado para uma máquina específica.

Baseline:

> **Linux systems with constrained compute resources; no dependency on dedicated GPU.**

Diagnósticos futuros devem detectar genericamente:

* sistema operacional;
* distribuição;
* CPU architecture;
* recursos;
* Python;
* dependências;
* Ollama;
* modelos;
* Docker;
* database;
* paths;
* permissions;
* configuração;
* serviços.

---

# Critérios de qualidade para releases

Uma release só deve ser fechada quando houver consistência entre:

```text
implementation
tests
architecture
documentation
requirements
roadmap
version
Git
tag
remote
```

Fluxo:

```text
planning
   │
   ▼
implementation
   │
   ▼
tests
   │
   ▼
architecture review
   │
   ▼
README
   │
   ▼
requirements
   │
   ▼
version
   │
   ▼
smoke
   │
   ▼
Git verification
   │
   ▼
versioned commit
   │
   ▼
annotated tag
   │
   ▼
push
   │
   ▼
remote verification
```

---

# Convenção de commits

Formato:

```text
<type>: Nexus Core v<VERSION> <description>
```

Exemplos:

```text
feat: Nexus Core v0.2.0 Implement Connectivity and Runtime Modes

feat: Nexus Core v0.2.1 Implement Runtime State Controller

feat: Nexus Core v0.2.2 Implement Continuous Connectivity Monitoring

feat: Nexus Core v0.2.3 Implement Automatic DEGRADED Runtime Detection

feat: Nexus Core v0.2.4 Implement Environment and Runtime Configuration

feat: Nexus Core v0.3.0 Implement Local Model Layer
```

---

# Tags

Releases versionadas utilizam tags Git.

Exemplos:

```text
v0.2.0
v0.2.1
v0.2.2
v0.2.3
v0.2.4
v0.3.0
v0.3.1
```

A `v0.3.1` foi fechada com tag anotada.

As tags `v0.3.1.1`, `v0.3.1.2`, `v0.3.1.3`, `v0.3.2` e `v0.3.3` já existem.

---

# Política de desenvolvimento

Mudanças devem respeitar:

* uma capacidade pequena por release;
* testes antes do fechamento;
* nenhuma mudança silenciosa de arquitetura;
* nenhuma ampliação acidental de escopo;
* nenhuma dependência proprietária obrigatória;
* nenhuma alteração retroativa de release já publicada sem patch deliberado;
* compatibilidade quando contratos públicos são preservados.

---

# Licença

O código-fonte e a documentação do Nexus Core são licenciados sob
[MIT](LICENSE). A licença permite uso, modificação e redistribuição,
mantendo o aviso de copyright. A disponibilização pública do repositório
depende da visibilidade configurada no GitHub; uma licença, por si só,
não altera a visibilidade.

Licenças de:

* Ollama;
* Docker;
* bibliotecas;
* ferramentas;
* model weights;

devem ser consideradas separadamente.

---

# Status

```text
────────────────────────────────────────────────────────
Project:               Nexus Core
Release Target:        v0.3.3
Release Name:          Explicit Confirmation & Authorization
Latest Git Tag:        v0.3.3
Implementation:        RELEASED
Release Validation:    LOCAL PASS; CI CHECKS REAL POSTGRESQL AND DOCKER
Tests:                 549 passed, 8 skipped locally
Primary Platform:      Linux
Runtime Baseline:      Python 3.12
Database:              PostgreSQL (loopback, Psycopg 3)
License:               MIT
Linux Entry Point:     nexus-core
Sandbox:               Docker
Model Runtime:         Ollama
Reference Model:       qwen3:1.7b
Production Provider:   ollama
Agent / Tool Calling:  NOT IMPLEMENTED
Development Status:    ACTIVE
────────────────────────────────────────────────────────
```

---

**Nexus Core**

Assistente pessoal de inteligência artificial **local-first**, construído sobre segurança, modularidade, controle operacional e evolução incremental.
