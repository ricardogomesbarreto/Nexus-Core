# Nexus Core

Assistente pessoal de inteligência artificial **local-first, multimodal, modular, seguro e orientado a agentes**.

> **Versão estável atual:** `v0.3.0 — Local Model Layer`
> **Próxima versão planejada:** `v0.3.1 — Provider Abstraction & Model Routing`
> **Status:** Development
> **Test baseline:** `338 passed`

---

## Visão geral

O **Nexus Core** é a infraestrutura central de um assistente pessoal de inteligência artificial projetado para operar prioritariamente de forma local, preservando privacidade, controle operacional, segurança e independência de serviços externos.

O projeto é desenvolvido incrementalmente.

Antes de entregar memória persistente, voz, visão, automação de desktop, agentes ou interfaces multimodais, o Nexus Core estabelece primeiro uma fundação sólida de:

* segurança;
* autorização;
* execução controlada;
* runtime;
* observabilidade;
* conectividade;
* configuração;
* lifecycle;
* testabilidade;
* governança;
* rastreabilidade;
* isolamento entre inteligência e autoridade operacional.

A `v0.3.0` representa a primeira integração formal de um modelo de linguagem local à arquitetura.

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

A presença de um modelo local não altera esse princípio.

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
* **Configuração explícita**
* **Scope control**

Segurança não é tratada como uma funcionalidade adicionada posteriormente.

Ela faz parte da fundação arquitetural do Nexus Core.

---

# Estado atual

A versão `v0.3.0` introduz a primeira **Local Model Layer** formal do Nexus Core.

A release estabelece:

* contrato tipado e imutável para requisições de modelo;
* contrato tipado e imutável para respostas;
* validação explícita de entradas;
* `LocalModelClient`;
* composição separada do transporte;
* integração controlada com Ollama;
* timeout configurável;
* erros explícitos de transporte;
* erros explícitos de protocolo;
* parsing e validação da resposta do backend;
* execução não-streaming;
* endpoint restrito a HTTP loopback;
* composição lazy no `NexusApplication`;
* ausência de inferência durante startup;
* ausência de carregamento de modelo durante os testes unitários;
* health estrutural da Local Model Layer;
* configuração por variáveis de ambiente;
* testes determinísticos independentes de um LLM real.

O modelo técnico de referência da release é:

```text
qwen3:1.7b
```

O backend local de referência é:

```text
Ollama
```

O endpoint padrão é:

```text
http://127.0.0.1:11434
```

A Local Model Layer não possui acesso direto a:

```text
SecurityGate
ToolExecutor
TerminalSandboxTool
filesystem tools
shell
host operating system
```

A `v0.3.0` introduz **inteligência local**, não autoridade operacional para o modelo.

---

## Runtime e conectividade preservados

A semântica de conectividade consolidada nas releases `v0.2.x` permanece preservada.

O Nexus Core distingue:

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

`DEGRADED` significa:

> uma mudança ou instabilidade de conectividade externa foi observada, mas ainda não foi confirmada como novo estado estável.

Ele **não** significa:

* falha do Ollama;
* indisponibilidade do modelo;
* indisponibilidade parcial de provider;
* degradação de serviço HTTP específico;
* latência elevada;
* perda parcial de capacidades de IA.

Health de backend/modelo e runtime connectivity permanecem dimensões distintas.

---

# Capacidades implementadas

Atualmente o projeto possui:

* Núcleo da aplicação
* Configuração tipada e imutável
* Environment configuration loader
* Allowlist de configuração externa
* Parsing e validação de configuração
* Fail-fast para configuração inválida
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
* `LocalModelRequest`
* `LocalModelResponse`
* `LocalModelClient`
* `OllamaTransport`
* Endpoint local restrito a loopback
* Timeout explícito da comunicação com o modelo
* Erros explícitos de transporte
* Erros explícitos de protocolo
* Composição lazy da Local Model Layer
* Health estrutural da Local Model Layer
* Modelo local técnico de referência `qwen3:1.7b`
* Suíte automatizada de testes

---

## Baseline atual

```text
Version:       v0.3.0
Tests:         338 passed
Runtime:       Python 3.12
Database:      SQLite
Sandbox:       Docker
Local Model:   Ollama + qwen3:1.7b
Branch model:  main
Status:        DEVELOPMENT
```

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
└── NexusApplication
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
    │   ├── Runtime observability projection
    │   └── Local Model Layer readiness
    │
    ├── Local Model Layer
    │   │
    │   ├── LocalModelRequest
    │   ├── LocalModelResponse
    │   │
    │   ├── LocalModelClient
    │   │   ├── request validation
    │   │   ├── payload construction
    │   │   ├── non-stream contract
    │   │   └── response validation
    │   │
    │   ├── OllamaTransport
    │   │   ├── HTTP POST /api/chat
    │   │   ├── timeout
    │   │   ├── JSON encode/decode
    │   │   └── explicit transport errors
    │   │
    │   ├── build_local_model_client()
    │   │
    │   └── Lazy application composition
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

A Local Model Layer e o Tool System permanecem separados.

Na `v0.3.0` não existe:

```text
Local Model
    │
    ▼
ToolExecutor
```

nem:

```text
Local Model
    │
    ▼
SecurityGate
```

Tool calling será introduzido somente em uma release posterior, depois da abstração formal de providers e routing.

---

# Local Model Layer

A `v0.3.0` estabelece uma fronteira explícita entre o Nexus Core e um modelo de linguagem executado localmente.

Fluxo:

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
Local model
        │
        ▼
Ollama response
        │
        ▼
validation
        │
        ▼
LocalModelResponse
```

---

## Modelo técnico de referência

O baseline técnico da release é:

```text
qwen3:1.7b
```

O modelo é utilizado como referência de desenvolvimento da primeira camada local.

Essa escolha **não** representa ainda:

* roteamento de modelos;
* seleção dinâmica;
* fallback;
* provider abstraction;
* política automática baseada em hardware;
* model registry.

Essas responsabilidades pertencem a releases posteriores.

---

## Backend local

A implementação inicial utiliza:

```text
Ollama
```

Ollama é tratado como um serviço local externo ao processo Python do Nexus Core.

O Nexus:

* não inicia o daemon Ollama;
* não encerra o daemon Ollama;
* não instala modelos automaticamente;
* não carrega modelos durante `NexusApplication.initialize()`;
* não executa probe de inferência durante startup;
* não assume ownership do lifecycle do serviço Ollama.

---

## Instalação do modelo de referência

Com Ollama instalado:

```bash
ollama pull qwen3:1.7b
```

Para verificar modelos disponíveis:

```bash
ollama list
```

Para verificar modelos atualmente carregados:

```bash
ollama ps
```

O Nexus utiliza por padrão a API local do Ollama em:

```text
http://127.0.0.1:11434
```

---

# `LocalModelRequest`

`LocalModelRequest` representa o contrato tipado de entrada.

A estrutura é imutável.

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

---

## `prompt`

Deve ser:

```text
str não vazia
```

Valores compostos apenas por whitespace são rejeitados.

Tipos diferentes de `str` também são rejeitados.

---

## `system_prompt`

Pode ser:

```text
None
```

ou:

```text
str não vazia
```

Quando presente, é enviada antes da mensagem do usuário.

---

## `temperature`

Deve ser:

```text
número
finito
>= 0
```

`bool` não é aceito como número válido neste contrato.

São rejeitados, entre outros:

```text
True
False
None
"0.5"
NaN
Infinity
valor negativo
```

---

## `context_length`

Deve ser:

```text
int >= 1
```

`bool`, `float`, `str` e `None` são rejeitados.

---

## `think`

Deve ser:

```text
bool
```

O default técnico da `v0.3.0` é:

```text
False
```

---

# `LocalModelResponse`

O contrato de saída normalizado contém:

```text
content
model
done
prompt_tokens
output_tokens
```

A estrutura também é imutável.

---

## `content`

Deve ser uma string não vazia.

---

## `model`

Deve identificar o modelo retornado pelo backend através de uma string não vazia.

---

## `done`

Deve ser um booleano.

A `v0.3.0` envia obrigatoriamente:

```text
stream = False
```

Portanto:

```text
done = False
```

é considerado incompatível com o contrato esperado de uma resposta final não-streaming.

Nesse cenário o Nexus gera:

```text
LocalModelProtocolError
```

---

## Token counts

Os campos:

```text
prompt_tokens
output_tokens
```

devem ser:

```text
int >= 0
```

Tipos incorretos são rejeitados.

---

# `LocalModelClient`

`LocalModelClient` coordena o contrato de alto nível da Local Model Layer.

Responsabilidades:

* validar o tipo da requisição;
* construir mensagens;
* incluir system prompt quando existente;
* adicionar mensagem do usuário;
* aplicar o nome do modelo configurado;
* aplicar `temperature`;
* aplicar `context_length`;
* aplicar `think`;
* desabilitar streaming;
* aplicar timeout;
* delegar I/O ao transporte;
* validar a estrutura da resposta;
* produzir `LocalModelResponse`.

O client não executa HTTP diretamente.

Essa responsabilidade pertence ao transporte.

---

## Validação da requisição no boundary

`generate()` aceita:

```text
LocalModelRequest
```

Valores arbitrários não atravessam a fronteira.

Exemplos rejeitados:

```text
None
str
dict
object arbitrário
```

Esses casos geram:

```text
LocalModelValidationError
```

em vez de vazar erros internos como:

```text
AttributeError
```

---

## Payload para Ollama

Conceitualmente:

```json
{
  "model": "qwen3:1.7b",
  "messages": [
    {
      "role": "user",
      "content": "..."
    }
  ],
  "stream": false,
  "think": false,
  "options": {
    "num_ctx": 2048,
    "temperature": 0.0
  }
}
```

Quando existe `system_prompt`:

```text
system
  │
  ▼
user
```

A ordem é preservada.

---

# Ollama Transport

`OllamaTransport` implementa a comunicação HTTP concreta da `v0.3.0`.

Endpoint:

```text
POST /api/chat
```

A implementação utiliza biblioteca padrão do Python.

Componentes utilizados incluem:

```text
urllib.request
urllib.error
json
```

A release não adiciona SDK Python do Ollama como dependência.

---

## Erros de transporte

A hierarquia atual inclui:

```text
OllamaTransportError
├── OllamaUnavailableError
├── OllamaTimeoutError
├── OllamaHTTPError
└── OllamaInvalidJSONError
```

---

## `OllamaUnavailableError`

Representa indisponibilidade de conexão com o backend local.

---

## `OllamaTimeoutError`

Representa timeout na comunicação.

O timeout default da Local Model Layer é:

```text
120.0 segundos
```

---

## `OllamaHTTPError`

Representa uma resposta HTTP de erro.

O status HTTP é preservado para diagnóstico.

---

## `OllamaInvalidJSONError`

Representa uma resposta que não pode ser interpretada como JSON válido.

A validação semântica do objeto JSON pertence ao `LocalModelClient`.

---

# Erros do contrato de modelo

Além dos erros de transporte, a Local Model Layer possui erros próprios.

```text
LocalModelValidationError
LocalModelProtocolError
```

---

## `LocalModelValidationError`

Representa dados inválidos fornecidos ao contrato local.

Exemplos:

* prompt vazio;
* tipo inválido;
* temperature inválida;
* context length inválido;
* token count inválido;
* resposta tipada inválida.

---

## `LocalModelProtocolError`

Representa uma resposta do backend incompatível com o protocolo esperado pelo client.

Exemplos:

* root da resposta não é mapping;
* campo obrigatório ausente;
* `message` inválido;
* conteúdo estruturalmente inválido;
* `done=False` em uma requisição não-streaming.

---

# Endpoint local e segurança de origem

A Local Model Layer da `v0.3.0` é deliberadamente restrita a um backend HTTP local.

Default:

```text
http://127.0.0.1:11434
```

A validação pertence a:

```text
nexus.config.local_endpoint
```

e não ao pacote `security`.

Essa decisão evita introduzir uma dependência arquitetural:

```text
config
  │
  ▼
security
```

apenas para validar uma origem de configuração.

---

## Origens permitidas

São aceitas origens HTTP em loopback.

Exemplos:

```text
http://127.0.0.1:11434
http://127.0.0.1:11434/
http://localhost:11434
http://[::1]:11434
```

Whitespace externo é normalizado.

A barra final simples também é normalizada.

---

## Origens rejeitadas

São rejeitados:

```text
https://127.0.0.1:11434
http://example.com:11434
http://192.168.1.10:11434
http://10.0.0.25:11434
ftp://127.0.0.1:11434
```

Também são rejeitados endpoints contendo:

* username;
* password;
* custom path;
* query string;
* fragment;
* hostname externo;
* endereço LAN não-loopback;
* porta inválida.

---

## Por que somente loopback?

A Local Model Layer da `v0.3.0` deve permanecer local.

Uma variável de ambiente não pode transformar silenciosamente:

```text
Local Model Layer
```

em:

```text
Remote Provider Layer
```

Provider abstraction e providers online pertencem à `v0.3.1`.

---

# Factory da Local Model Layer

A composição concreta é centralizada em:

```python
build_local_model_client(settings)
```

Fluxo:

```text
Settings
   │
   ▼
build_local_model_client()
   │
   ├── OllamaTransport(
   │       base_url=settings.local_model_base_url
   │   )
   │
   └── LocalModelClient(
           model=settings.local_model_name
           timeout=settings.local_model_timeout
       )
```

Isso evita espalhar detalhes de composição pela aplicação.

---

# Composição lazy

`NexusApplication` não instancia o client de modelo no construtor.

Também não instancia o client durante:

```python
app.initialize()
```

O campo interno começa como:

```text
_local_model_client = None
```

O client é criado somente quando:

```python
app.local_model_client
```

é acessado pela primeira vez.

Depois disso, a instância é reutilizada.

Fluxo:

```text
NexusApplication
        │
        │ first property access
        ▼
local_model_client
        │
        ▼
build_local_model_client(settings)
        │
        ├── OllamaTransport
        └── LocalModelClient
```

---

## Razão para composição lazy

O modelo de referência utiliza memória significativa quando carregado.

A aplicação não deve consumir esse recurso apenas por iniciar o Nexus.

Portanto:

```text
NexusApplication()
```

não carrega modelo.

```text
app.initialize()
```

não carrega modelo.

```text
app.local_model_client
```

constrói apenas client e transporte.

Somente:

```python
client.generate(...)
```

executa comunicação com Ollama e pode causar o carregamento real do modelo.

---

# Health da Local Model Layer

`HealthStatus` possui:

```text
local_model_layer
```

O valor começa em:

```text
False
```

Durante a inicialização bem-sucedida da aplicação, a camada é marcada como estruturalmente pronta:

```text
local_model_layer = True
```

Isso não causa:

* conexão com Ollama;
* carregamento do modelo;
* inferência;
* probe HTTP.

---

## Semântica de readiness

O painel utiliza:

```text
Local Model Layer    ✓ READY
```

Isso significa:

> a camada de software do Nexus necessária para utilizar um modelo local foi integrada e configurada corretamente.

Não significa:

```text
Ollama está ativo
```

Não significa:

```text
qwen3:1.7b está instalado
```

Não significa:

```text
modelo está carregado
```

Não significa:

```text
inferência foi validada agora
```

Não significa:

```text
backend está saudável
```

Essa distinção é deliberada.

---

# Local Model Layer e offline mode

`offline_mode` controla o relacionamento do runtime com **conectividade externa**.

Ollama utiliza loopback.

Portanto:

```text
offline_mode = True
```

não desabilita a Local Model Layer.

Isso preserva o princípio:

```text
LOCAL FIRST
```

O assistente deve poder utilizar inteligência local mesmo quando a Internet está indisponível ou quando o runtime está explicitamente em forced offline.

---

# Configuração

A `v0.2.4` estabeleceu o boundary formal entre o ambiente do processo e a configuração utilizada pelo Nexus Core.

A `v0.3.0` preserva esse contrato e adiciona somente os parâmetros necessários à Local Model Layer.

Fluxo:

```text
Environment
    │
    ▼
load_settings()
    │
    ├── parsing tipado
    ├── normalização
    ├── validação
    ├── defaults seguros
    └── overrides permitidos
    │
    ▼
Settings(frozen=True)
    │
    ▼
settings = load_settings()
    │
    ▼
Nexus Core
```

A estrutura permanece:

```python
@dataclass(frozen=True)
class Settings:
    ...
```

`Settings` representa um snapshot tipado e imutável de configuração.

---

# Defaults de configuração

Parâmetros operacionais principais:

```python
node_name: str = "NEXUS-NODE-01"

offline_mode: bool = True

connectivity_monitor_interval: float = 30.0

connectivity_confirmation_threshold: int = 2

local_model_name: str = "qwen3:1.7b"

local_model_base_url: str = "http://127.0.0.1:11434"

local_model_timeout: float = 120.0
```

Os defaults permanecem centralizados em `Settings`.

`load_settings()` deriva seus defaults de:

```python
Settings()
```

em vez de manter uma segunda tabela independente.

---

# Variáveis de ambiente suportadas

A allowlist atual é:

```text
NEXUS_NODE_NAME
NEXUS_OFFLINE_MODE
NEXUS_CONNECTIVITY_MONITOR_INTERVAL
NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD
NEXUS_LOCAL_MODEL_NAME
NEXUS_LOCAL_MODEL_BASE_URL
NEXUS_LOCAL_MODEL_TIMEOUT
```

Variáveis `NEXUS_*` desconhecidas não são automaticamente convertidas em configuração.

---

# `NEXUS_NODE_NAME`

Default:

```text
NEXUS-NODE-01
```

Exemplo:

```bash
export NEXUS_NODE_NAME="NEXUS-DESKTOP-01"
```

Whitespace externo é removido.

Valores vazios são rejeitados com:

```text
ConfigurationError
```

---

# `NEXUS_OFFLINE_MODE`

Default:

```text
true
```

Valores aceitos:

```text
true
false
```

O parsing é:

* case-insensitive;
* normalizado por whitespace;
* estrito.

São rejeitados:

```text
yes
1
enabled
on
```

---

# `NEXUS_CONNECTIVITY_MONITOR_INTERVAL`

Default:

```text
30.0
```

Deve ser:

```text
float
finito
> 0
```

São rejeitados:

```text
0
-1
nan
inf
-inf
valor não numérico
```

---

# `NEXUS_CONNECTIVITY_CONFIRMATION_THRESHOLD`

Default:

```text
2
```

Deve ser:

```text
integer >= 2
```

São rejeitados:

```text
0
1
-1
2.5
abc
```

---

# `NEXUS_LOCAL_MODEL_NAME`

Default:

```text
qwen3:1.7b
```

Exemplo:

```bash
export NEXUS_LOCAL_MODEL_NAME="qwen3:1.7b"
```

O valor é normalizado por whitespace.

Strings vazias são rejeitadas.

A `v0.3.0` não valida a existência do modelo durante carregamento de configuração.

A existência real do modelo é responsabilidade do backend Ollama.

---

# `NEXUS_LOCAL_MODEL_BASE_URL`

Default:

```text
http://127.0.0.1:11434
```

Exemplo:

```bash
export NEXUS_LOCAL_MODEL_BASE_URL="http://127.0.0.1:11434"
```

A URL passa pela política local de origem.

Endpoints remotos são rejeitados com:

```text
ConfigurationError
```

---

# `NEXUS_LOCAL_MODEL_TIMEOUT`

Default:

```text
120.0
```

Representa o timeout em segundos utilizado pelo `LocalModelClient`.

Deve ser:

```text
float
finito
> 0
```

São rejeitados:

```text
0
-1
nan
inf
-inf
valor não numérico
```

---

# Campos não configuráveis por ambiente

Os seguintes campos estruturais continuam protegidos:

```text
app_name
version
project_root
data_dir
logs_dir
database_dir
database_file
```

Portanto variáveis como:

```text
NEXUS_APP_NAME
NEXUS_VERSION
NEXUS_PROJECT_ROOT
NEXUS_DATA_DIR
NEXUS_LOGS_DIR
NEXUS_DATABASE_DIR
NEXUS_DATABASE_FILE
```

não alteram esses valores.

---

# `ConfigurationError`

Configurações ambientais inválidas produzem:

```python
ConfigurationError
```

A exceção deriva de:

```python
ValueError
```

Objetivos:

* distinguir falhas de configuração externa;
* evitar fallback silencioso;
* facilitar diagnóstico;
* preservar fail-fast;
* impedir valores inválidos no runtime.

---

# Fail-fast

Configuração inválida não é substituída silenciosamente por defaults.

```text
Environment
    │
    ▼
load_settings()
    │
    ├── válido
    │     │
    │     ▼
    │   Settings
    │
    └── inválido
          │
          ▼
   ConfigurationError
          │
          ▼
    startup interrompido
```

---

# Configuração determinística para testes

Para obter exclusivamente defaults:

```python
load_settings({})
```

Isso evita dependência acidental de:

```text
shell
CI
systemd environment
container environment
user session
```

---

# Singleton global

O módulo mantém:

```python
settings = load_settings()
```

O ambiente é avaliado na importação do módulo.

Mudanças posteriores em `os.environ` não causam reload automático.

A arquitetura atual não possui configuração dinâmica.

---

# Perfis de ambiente

Não existem perfis formais como:

```text
development
production
staging
testing
```

Perfis somente deverão ser introduzidos quando houver comportamento operacional real que justifique a abstração.

---

# `.env`

O Nexus Core não carrega automaticamente:

```text
.env
```

e não depende de:

```text
python-dotenv
```

A configuração permanece baseada diretamente no ambiente do processo.

---

# Segurança da configuração

Configuração externa não representa autoridade operacional.

Ela não pode:

* contornar `SecurityGate`;
* registrar ferramentas arbitrárias;
* conceder permissões;
* alterar paths estruturais;
* alterar a versão;
* executar comandos;
* conceder acesso direto ao host;
* transformar a Local Model Layer em provider remoto.

---

# `offline_mode = True`

Força o runtime para:

```text
OFFLINE
```

independentemente da disponibilidade real da Internet.

Nesse modo:

* nenhuma verificação externa periódica é iniciada;
* nenhum `ConnectivityMonitor` é criado;
* `connectivity_monitor` permanece `None`;
* não existe polling externo em background;
* não existe detecção automática de `DEGRADED`;
* o comportamento de conectividade é determinístico;
* recursos locais continuam disponíveis;
* a Local Model Layer continua utilizável.

Esse permanece sendo o default seguro.

---

# `offline_mode = False`

Permite que o Nexus:

1. verifique conectividade externa;
2. determine `ONLINE` ou `OFFLINE`;
3. estabeleça o estado inicial;
4. publique os eventos iniciais;
5. inicie o monitor de conectividade;
6. detecte mudanças brutas da rede;
7. coloque o runtime em `DEGRADED` durante confirmação;
8. confirme automaticamente `ONLINE` ou `OFFLINE`.

Exemplo:

```bash
NEXUS_OFFLINE_MODE=false \
PYTHONPATH="$PWD" \
python -m nexus.main
```

---

# Fluxo de conectividade e runtime

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

---

# Runtime State Controller

`RuntimeStateController` é a fonte autoritativa do estado operacional.

Mantém:

```text
mode
reason
changed_at
```

O componente utiliza:

```python
threading.RLock
```

para proteger o estado interno.

---

## Snapshot

```python
controller.snapshot()
```

retorna um:

```text
RuntimeStateSnapshot
```

imutável.

---

## Matriz de transições

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

Transições diretas entre:

```text
ONLINE ↔ OFFLINE
```

continuam permitidas pelo controlador.

A política automática de conectividade utiliza `DEGRADED` como estado intermediário.

---

# Connectivity Runtime Evaluator

`ConnectivityRuntimeEvaluator` transforma observações brutas em modo alvo.

O evaluator:

* não executa I/O;
* não cria threads;
* não utiliza `EventBus`;
* não atualiza diretamente `HealthStatus`;
* não modifica diretamente o `RuntimeStateController`.

Cada avaliação retorna:

```text
ConnectivityRuntimeEvaluation
```

com:

```text
target_mode
reason
network_online
network_changed
```

---

# Connectivity Monitor

O monitor utiliza uma worker dedicada:

```text
Name:    Nexus-ConnectivityMonitor
Daemon:  True
```

Primitivas:

```text
threading.Thread
threading.Event
threading.RLock
```

`check_once()` é serializado.

O ciclo protegido envolve:

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

## Shutdown da worker

O loop utiliza:

```python
stop_event.wait(interval)
```

permitindo interrupção responsiva.

`stop()`:

1. sinaliza o stop event;
2. aguarda a thread com `join()`;
3. respeita timeout;
4. gera `TimeoutError` se a worker não terminar.

---

# Semântica dos eventos de conectividade

Os eventos:

```text
NETWORK_ONLINE
NETWORK_OFFLINE
```

representam mudança na **observação bruta**.

O evento:

```text
RUNTIME_MODE_CHANGED
```

representa alteração do estado autoritativo.

Exemplo:

```text
ONLINE
  │
  │ observação OFFLINE
  ▼
NETWORK_OFFLINE
RUNTIME_MODE_CHANGED(DEGRADED)
  │
  │ confirmação OFFLINE
  ▼
RUNTIME_MODE_CHANGED(OFFLINE)
```

O segundo ciclo não publica outro `NETWORK_OFFLINE` porque a observação bruta não mudou novamente.

---

# Health Status

`HealthStatus` representa saúde estrutural e observabilidade.

Campos relevantes incluem:

```text
core
configuration
database
logger
event_bus
security_gate
tool_registry
terminal_sandbox
local_model_layer
network_online
runtime_mode
runtime_reason
```

---

## Readiness

```python
health.ready
```

representa disponibilidade estrutural dos componentes locais necessários.

Conectividade externa não determina readiness.

A Local Model Layer participa da readiness estrutural.

Isso não deve ser confundido com liveness do Ollama.

---

## Runtime snapshot

```python
health.runtime_snapshot()
```

retorna:

```text
HealthRuntimeSnapshot
```

com:

```text
network_online
runtime_mode
runtime_reason
```

---

# NexusApplication

`NexusApplication` coordena o ciclo de vida dos principais componentes.

A configuração global é carregada através de:

```text
Environment
    │
    ▼
load_settings()
    │
    ▼
settings
```

Durante a inicialização a aplicação estabelece, entre outros:

1. logging;
2. banco SQLite;
3. `EventBus`;
4. `SecurityGate`;
5. `ToolRegistry`;
6. ferramentas;
7. `ToolExecutor`;
8. `ConnectivityManager`;
9. runtime state;
10. health;
11. eventos de inicialização;
12. monitor de conectividade quando aplicável;
13. readiness estrutural da Local Model Layer.

A inicialização **não** instancia o model client e não executa inferência.

---

## Contrato de inicialização

`initialize()` possui semântica:

```text
one-shot
```

Uma segunda chamada após sucesso gera:

```text
RuntimeError
```

Isso evita duplicação de:

* side effects;
* eventos;
* workers;
* componentes;
* recursos.

---

## Contrato de shutdown

`shutdown()` é idempotente.

Quando existe monitor ativo:

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

Ollama não é encerrado porque é um serviço externo ao lifecycle da aplicação.

---

# Fluxo de autoridade

Uma regra fundamental é que inteligência não equivale a autoridade.

Arquitetura futura:

```text
MODEL
  │
  ▼
PLANNER / AGENT
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
  │
  │      ▼
  │  EXECUÇÃO CONTROLADA
  │
  └── negado
         │
         ▼
       BLOQUEIO
```

A `v0.3.0` termina antes do Planner/Agent.

Atualmente:

```text
Local Model
    │
    ▼
Text Response
```

---

# Security Gate

`SecurityGate` é a principal fronteira de autorização operacional.

Ferramentas não devem executar ações sensíveis apenas porque:

* o LLM pediu;
* um arquivo pediu;
* uma página web pediu;
* um PDF pediu;
* uma imagem contém instruções;
* uma mensagem externa contém instruções.

Conteúdo externo é **não confiável**.

---

# Prompt Injection

Prompt injection não representa autoridade.

Conteúdo proveniente de:

* web;
* PDFs;
* documentos;
* imagens;
* mensagens;
* memória futura;
* arquivos;
* resultados de ferramentas;

é tratado como dado.

Não como autorização.

---

# Tool Architecture

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

Na `v0.3.0`, a Local Model Layer ainda não está conectada a essa cadeia.

---

# Tool Registry

Responsável por registrar e localizar ferramentas.

Conhecer o nome de uma ferramenta não concede permissão para utilizá-la.

---

# Tool Executor

Coordena:

```text
intenção
autorização
execução
resultado
```

Ele deve respeitar decisões do `SecurityGate`.

---

# Filesystem Security

Operações de filesystem passam por validações explícitas.

Objetivos:

* impedir traversal;
* restringir áreas permitidas;
* validar caminhos;
* impedir acesso acidental a regiões sensíveis;
* preservar least privilege.

---

# Terminal Sandbox

O terminal controlado utiliza Docker.

```text
command
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

A sandbox reduz exposição direta do host.

---

## Dívida de segurança do Docker

Pertencimento ao grupo:

```text
docker
```

pode equivaler a autoridade root em diversos cenários.

Essa é uma dívida técnica conhecida.

Possíveis evoluções:

```text
Podman rootless
Docker rootless
helper privilegiado isolado
AppArmor
polkit
namespaces adicionais
```

A questão permanece separada da Local Model Layer.

---

# Painel de status

O entrypoint apresenta status textual.

Exemplo conceitual da `v0.3.0`:

```text
╔══════════════════════════════════════════════╗
║                   N E X U S                  ║
║                    v0.3.0                    ║
╠══════════════════════════════════════════════╣
║ Core                              ✓ ONLINE   ║
║ Configuration                     ✓ READY    ║
║ Database                          ✓ READY    ║
║ Logger                            ✓ READY    ║
║ EventBus                          ✓ READY    ║
║ SecurityGate                      ✓ READY    ║
║ ToolRegistry                      ✓ READY    ║
║ Terminal Sandbox                  ✓ READY    ║
║ Local Model Layer                 ✓ READY    ║
╠══════════════════════════════════════════════╣
║ Health Monitor                    ✓ READY    ║
╠══════════════════════════════════════════════╣
║ Node                         NEXUS-NODE-01    ║
║ Network                           ✗ OFFLINE  ║
║ Mode                               OFFLINE   ║
╚══════════════════════════════════════════════╝
```

`Local Model Layer ✓ READY` representa readiness estrutural da camada.

Não representa liveness do backend.

---

# Testes

Testes automatizados são parte obrigatória do processo de engenharia.

Framework:

```text
pytest
```

Execução padrão:

```bash
PYTHONPATH="$PWD" pytest -q
```

Baseline validado da `v0.3.0`:

```text
338 passed
```

---

## Determinismo da suíte

A suíte completa foi executada verificando também:

```bash
ollama ps
```

antes e depois dos testes.

Resultado esperado e observado:

```text
nenhum modelo carregado
```

antes e depois.

Portanto os testes automatizados da arquitetura não dependem de:

* inferência real;
* modelo carregado;
* resposta de Ollama;
* rede externa;
* disponibilidade de GPU.

Isso mantém a suíte rápida e determinística.

---

## Cobertura da Local Model Layer

A suíte cobre, entre outros:

* contrato de `LocalModelRequest`;
* contrato de `LocalModelResponse`;
* imutabilidade;
* prompt inválido;
* system prompt inválido;
* temperature inválida;
* rejeição de `bool` como temperature;
* context length inválido;
* rejeição de tipos incorretos;
* token counts inválidos;
* `LocalModelClient`;
* validação runtime do tipo da requisição;
* payload;
* mensagens;
* system prompt;
* timeout;
* model name;
* parsing de resposta;
* resposta malformada;
* resposta incompleta;
* rejeição de `done=False`;
* protocolo não-streaming;
* `OllamaTransport`;
* HTTP POST;
* timeout;
* backend indisponível;
* HTTP error;
* JSON inválido;
* settings do modelo;
* environment overrides;
* endpoint local;
* loopback IPv4;
* localhost;
* loopback IPv6;
* rejeição de hosts externos;
* rejeição de LAN;
* rejeição de credentials;
* rejeição de paths;
* rejeição de query;
* rejeição de fragment;
* factory;
* lazy composition;
* cache do local model client;
* ausência de model client no startup;
* health estrutural;
* painel de status.

---

## Cobertura geral

A suíte também cobre:

* inicialização;
* shutdown;
* runtime modes;
* transições válidas;
* transições inválidas;
* `DEGRADED`;
* snapshots;
* concorrência;
* competing writers;
* health;
* connectivity manager;
* connectivity runtime evaluator;
* thresholds;
* perda de conectividade;
* recuperação;
* oscilação;
* monitoramento contínuo;
* eventos de rede;
* eventos de runtime;
* ausência de event flooding;
* lifecycle de worker;
* stop timeout;
* subscriber failures;
* filesystem security;
* tool architecture;
* terminal sandbox;
* environment configuration;
* defaults;
* fail-fast;
* regressão completa.

---

# Smoke tests reais

Os testes unitários não dependem de Ollama real.

Separadamente, a Local Model Layer foi validada com smoke tests reais.

Caminho básico:

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
Ollama
        │
        ▼
qwen3:1.7b
        │
        ▼
LocalModelResponse
```

Também foi validada a composição:

```text
load_settings()
        │
        ▼
Settings
        │
        ▼
build_local_model_client()
        │
        ▼
LocalModelClient
        │
        ▼
OllamaTransport
        │
        ▼
qwen3:1.7b
```

Esses smokes são separados da suíte determinística.

---

# Baseline de hardware do modelo

O ambiente principal de desenvolvimento utiliza hardware de baixo consumo com memória limitada.

O modelo:

```text
qwen3:1.7b
```

foi selecionado como baseline técnico inicial por oferecer operação local viável nesse ambiente.

A execução de referência atual ocorre em:

```text
CPU
```

A aceleração GPU não é requisito da `v0.3.0`.

Suporte e otimização de hardware permanecem assuntos independentes da arquitetura do contrato de modelo.

---

# Uso de memória

Carregar um LLM local pode aumentar significativamente o consumo de RAM e swap.

Por esse motivo:

* startup não carrega modelo;
* health não executa inferência;
* testes unitários não carregam modelo;
* composição do client é lazy.

A aplicação deve preservar a capacidade de iniciar e operar sua infraestrutura sem exigir que um LLM permaneça residente em memória.

---

# Dependências

## Runtime Python

A `v0.3.0` continua sem exigir pacotes Python externos obrigatórios no runtime.

`requirements/base.txt` deve refletir:

```text
# Nexus Core runtime dependencies
# No external Python packages are required at v0.3.0.
```

A Local Model Layer utiliza componentes da biblioteca padrão, incluindo:

```text
dataclasses
collections.abc
json
math
urllib
ipaddress
pathlib
```

---

## Desenvolvimento

`requirements/dev.txt` inclui o tooling de desenvolvimento, incluindo:

```text
pytest
```

---

## Dependência externa para inferência local

Embora não exista SDK Python obrigatório, inferência real exige:

```text
Ollama
```

e um modelo instalado, por padrão:

```text
qwen3:1.7b
```

Portanto existe uma distinção importante:

```text
Python package dependency
        ≠
external local runtime dependency
```

Ollama é uma dependência do ambiente de inferência, não uma dependência Python do Nexus Core.

---

# Estrutura do projeto

Estrutura conceitual da `v0.3.0`:

```text
Nexus Core/
│
├── nexus/
│   │
│   ├── config/
│   │   ├── __init__.py
│   │   ├── local_endpoint.py
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
│   ├── database/
│   │
│   ├── events/
│   │
│   ├── models/
│   │   ├── local_model.py
│   │   ├── local_model_factory.py
│   │   └── ollama_transport.py
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
│   ├── test_application_local_model.py
│   ├── test_application_local_model_health.py
│   ├── test_application_runtime.py
│   ├── test_connectivity.py
│   ├── test_connectivity_monitor.py
│   ├── test_connectivity_runtime_evaluator.py
│   ├── test_core.py
│   ├── test_health.py
│   ├── test_local_endpoint.py
│   ├── test_local_model_client.py
│   ├── test_local_model_contract.py
│   ├── test_local_model_factory.py
│   ├── test_local_model_settings.py
│   ├── test_main.py
│   ├── test_ollama_transport.py
│   ├── test_runtime.py
│   ├── test_runtime_state.py
│   └── test_settings_environment.py
│
├── README.md
└── ...
```

A árvore destaca componentes arquiteturais relevantes e não necessariamente todos os arquivos auxiliares.

---

# Histórico de releases

## v0.1.0 — Foundation

Fundação inicial.

Entregou:

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

Introdução da fronteira central de autorização.

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

Ferramentas seguras de filesystem integradas ao modelo de segurança.

---

## v0.1.8 — Terminal Sandbox

Execução controlada de terminal em Docker.

---

## v0.1.9 — Health Check & Application Status

Health checks e status operacional.

---

## v0.2.0 — Connectivity & Runtime Modes

Introduziu:

* `ConnectivityManager`;
* `ConnectivityStatus`;
* `RuntimeMode`;
* `ONLINE`;
* `OFFLINE`;
* `DEGRADED`;
* `offline_mode`;
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
* transições formais;
* integração com a aplicação;
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
* polling;
* intervalo configurável;
* snapshots;
* sincronização de health;
* locks;
* stop event;
* shutdown responsivo;
* lifecycle endurecido;
* isolamento de falhas.

Baseline histórico:

```text
134 tests passing
```

---

## v0.2.3 — Automatic DEGRADED Runtime Detection

Introduziu:

* `ConnectivityRuntimeEvaluator`;
* `ConnectivityRuntimeEvaluation`;
* `DEGRADED` automático;
* confirmação simétrica;
* threshold configurável;
* threshold default `2`;
* cancelamento de mudança pendente;
* tratamento de oscilação;
* separação de rede e runtime;
* eventos independentes;
* serialização de ciclos;
* invariants de inicialização.

Baseline histórico:

```text
151 tests passing
```

---

## v0.2.4 — Environment & Runtime Configuration

Introduziu:

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
* proteção de versão;
* proteção de app name;
* testes determinísticos;
* nenhuma dependência Python adicional;
* nenhum `.env`;
* nenhum `python-dotenv`;
* nenhum perfil artificial;
* nenhum reload dinâmico.

Baseline histórico:

```text
184 tests passing
```

---

# v0.3.0 — Local Model Layer

A `v0.3.0` introduz a primeira camada formal de inteligência artificial local.

Entregue:

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
* `/api/chat`;
* JSON pela biblioteca padrão;
* endpoint HTTP local;
* política loopback-only;
* bloqueio de hosts externos;
* bloqueio de LAN;
* bloqueio de credentials;
* bloqueio de custom paths;
* bloqueio de query e fragments;
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
* smokes reais separados;
* modelo técnico de referência `qwen3:1.7b`;
* backend técnico de referência Ollama;
* nenhuma autoridade direta sobre ferramentas;
* nenhuma dependência Python externa adicional;
* regressão arquitetural completa.

Baseline:

```text
338 tests passing
```

---

## Princípios de engenharia da v0.3.0

### Local First

A inteligência introduzida pela release opera através de um backend local em loopback.

---

### Contract First

Entrada e saída do modelo possuem contratos explícitos.

---

### Runtime validation

Type hints não são tratados como única defesa.

Boundaries públicos validam dados em runtime.

---

### Fail explicitly

Falhas são classificadas entre:

```text
validation
protocol
transport
```

---

### Resource discipline

Startup não carrega o modelo.

---

### Test determinism

A suíte não depende de inferência real.

---

### Separation of concerns

```text
LocalModelClient
```

não implementa transporte HTTP diretamente.

```text
OllamaTransport
```

não decide semântica do contrato de modelo.

---

### Local endpoint policy

A configuração da Local Model Layer não pode ser usada para apontar silenciosamente para um provider remoto.

---

### Security First

O modelo não recebe acesso a ferramentas.

---

### Scope control

A release não introduz:

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

---

# Roadmap

O roadmap é evolutivo.

Cada versão deve adicionar uma responsabilidade pequena, clara e testável.

---

# Inteligência artificial

## v0.3.0 — Local Model Layer

**Status: concluída**

Entregue:

* contrato local;
* client;
* Ollama transport;
* endpoint local seguro;
* timeout;
* errors;
* lazy composition;
* health estrutural;
* settings;
* modelo baseline;
* testes determinísticos;
* smokes reais;
* 338 testes passando.

---

## v0.3.1 — Provider Abstraction & Model Routing

**Status: próxima versão planejada**

Objetivos planejados:

* interface comum de providers;
* abstração do provider local;
* provider online opcional;
* model routing;
* política de seleção;
* disponibilidade;
* fallback controlado;
* proteção de credenciais;
* separação entre provider capability e runtime connectivity;
* manutenção da preferência local-first.

Arquitetura conceitual:

```text
Task / Model Request
        │
        ▼
Model Router
        │
        ├── Local Provider
        │
        └── Online Provider
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

O LLM nunca deverá receber acesso direto ao shell ou ao sistema operacional.

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

* automação controlada;
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
* descoberta;
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

* GUI;
* chat;
* voz;
* contexto visual;
* status operacional;
* experiência multimodal;
* UI circular futurista.

Tecnologia candidata:

```text
PySide6
```

---

# v1.0.0 — Production Baseline

A versão `1.0.0` somente deverá ser considerada quando existir um baseline operacional com:

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

# Critérios de qualidade para releases

Cada release deve possuir:

* escopo explícito;
* responsabilidades definidas;
* implementação mínima coerente;
* testes unitários;
* testes de integração;
* regressão completa;
* revisão arquitetural;
* documentação atualizada;
* dependências revisadas;
* versão atualizada;
* smoke test;
* revisão Git;
* commit versionado;
* tag;
* push do commit;
* push da tag;
* verificação remota.

Fluxo oficial:

```text
PLANEJAMENTO
    │
    ▼
IMPLEMENTAÇÃO
    │
    ▼
TESTES
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
VERIFICAÇÃO REMOTA
```

Nenhuma release deve ser considerada concluída enquanto existirem inconsistências conhecidas entre:

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

Formato:

```text
<type>: Nexus Core v<VERSION> <description>
```

Exemplos:

```text
checkpoint: Nexus Core v0.1.8 terminal sandbox
release: Nexus Core v0.1.9 health check
feat: Nexus Core v0.2.0 Implement Connectivity and Runtime Modes
feat: Nexus Core v0.2.1 Implement Runtime State Controller
feat: Nexus Core v0.2.2 Implement Continuous Connectivity Monitoring
feat: Nexus Core v0.2.3 Implement Automatic DEGRADED Runtime Detection
feat: Nexus Core v0.2.4 Implement Environment and Runtime Configuration
```

Commit de release da `v0.3.0`:

```text
feat: Nexus Core v0.3.0 Implement Local Model Layer
```

---

# Tags

Cada release possui uma tag própria.

```text
v0.2.0
v0.2.1
v0.2.2
v0.2.3
v0.2.4
v0.3.0
```

Mensagem da tag da `v0.3.0`:

```text
release: Nexus Core v0.3.0 Local Model Layer
```

---

# Segurança e limitações atuais

A `v0.3.0` possui uma Local Model Layer funcional, mas o projeto permanece em desenvolvimento.

Limitações atuais:

* não existe provider abstraction;
* não existe model router;
* não existem providers online integrados;
* não existe streaming da Local Model Layer;
* não existe Agent;
* não existe Planner;
* não existe tool calling pelo LLM;
* o modelo não possui acesso direto ao sistema operacional;
* o modelo não possui acesso ao `SecurityGate`;
* o modelo não possui acesso ao `ToolExecutor`;
* o modelo não possui acesso ao terminal;
* o modelo não possui acesso direto ao filesystem;
* health da Local Model Layer não representa Ollama liveness;
* não existe probe automático de Ollama no startup;
* não existe model discovery automático;
* não existe fallback de modelo;
* não existe seleção automática de modelo;
* Ollama é um serviço externo;
* o Nexus não administra o lifecycle do daemon Ollama;
* ferramentas continuam passando pelo `SecurityGate`;
* conteúdo externo permanece não confiável;
* prompt injection não representa autoridade;
* terminal continua em sandbox Docker;
* grupo `docker` permanece dívida de segurança;
* `ONLINE` não representa autorização;
* `DEGRADED` continua restrito à semântica de conectividade;
* `DEGRADED` não representa saúde de modelos;
* `latency_ms` de connectivity ainda não determina degradação;
* não existem probes de providers;
* não existe reload dinâmico de configuração;
* não existem profiles formais;
* `.env` não é carregado automaticamente;
* memória persistente ainda não está implementada;
* Knowledge Base ainda não está implementada;
* voz ainda não está implementada;
* visão ainda não está implementada;
* automação de desktop ainda não está implementada;
* interface gráfica ainda não está implementada.

A documentação distingue deliberadamente:

```text
IMPLEMENTADO
```

de:

```text
PLANEJADO
```

---

# Escopo da v0.3.0

A release introduz:

```text
Local Model Layer
```

Ela não introduz:

```text
Provider Abstraction
Model Router
Online Providers
Agent
Planner
Tool Calling
Persistent Memory
Knowledge Base
Voice
Vision
Desktop Automation
GUI
```

Seu boundary termina em:

```text
LocalModelResponse
```

A próxima responsabilidade arquitetural começa somente na `v0.3.1`.

---

# Tecnologias atuais

Baseline:

```text
Operating System:    Ubuntu 24.04 LTS
Runtime:             Python 3.12
Database:            SQLite
Tests:               pytest
Sandbox:             Docker
Local Model Runtime: Ollama
Reference Model:     qwen3:1.7b
Version Control:     Git
Remote:              GitHub
```

---

# Tecnologias candidatas futuras

Dependendo da evolução:

```text
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

Ollama deixa de ser apenas uma tecnologia candidata na `v0.3.0` e passa a ser o backend local de referência da Local Model Layer.

Tecnologias futuras não representam compromisso definitivo antes da revisão arquitetural correspondente.

---

# Filosofia Local First

O Nexus Core deve continuar útil quando:

```text
Internet unavailable
```

O sistema não deve depender estruturalmente de:

* APIs externas;
* contas cloud;
* conectividade constante;
* serviços remotos obrigatórios.

A `v0.3.0` reforça esse objetivo ao introduzir inteligência local real.

Fluxo local:

```text
Application
    │
    ▼
Local Model Layer
    │
    ▼
127.0.0.1
    │
    ▼
Ollama
    │
    ▼
Local Model
```

Serviços online poderão complementar o Nexus.

Eles não devem substituir sua fundação local.

---

# Privacidade

O objetivo de longo prazo é manter localmente, sempre que possível:

* processamento;
* contexto;
* memória;
* voz;
* conhecimento;
* documentos;
* automações;
* preferências.

A `v0.3.0` mantém a primeira comunicação de modelo restrita a loopback.

Integrações online futuras deverão ser:

* opcionais;
* explícitas;
* governadas;
* observáveis;
* limitadas ao necessário.

Credenciais futuras exigirão tratamento específico.

---

# Observabilidade

O Nexus Core deverá manter rastreabilidade de:

* lifecycle;
* runtime;
* conectividade;
* configuração;
* ferramentas;
* autorizações;
* falhas;
* mudanças de estado;
* modelos;
* providers futuros;
* memória futura;
* operações futuras de agentes.

Observabilidade não deve implicar coleta indiscriminada de conteúdo sensível.

---

# Governança de ferramentas

Nenhuma ferramenta recebe autoridade apenas por estar registrada.

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

A Local Model Layer não altera essa cadeia.

---

# Fronteira entre inteligência e execução

O princípio arquitetural é:

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

Na `v0.3.0` o boundary é ainda mais restrito:

```text
LLM responds
```

Não existe tool calling.

---

# Exemplo de arquitetura futura

```text
User
 │
 ▼
Model Layer
 │
 ▼
Planner
 │
 ▼
Tool Request
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
 ├── DENY ─────► blocked
 │
 └── ALLOW
       │
       ▼
      Tool
       │
       ▼
 Controlled Execution
```

Essa arquitetura é futura e não deve ser confundida com a funcionalidade entregue na `v0.3.0`.

---

# Próximo passo

A próxima release planejada é:

```text
v0.3.1 — Provider Abstraction & Model Routing
```

Objetivo:

* separar a Local Model Layer da implementação concreta do provider;
* criar contratos formais de provider;
* preparar providers adicionais;
* introduzir model routing controlado;
* preservar local-first;
* tratar disponibilidade;
* definir fallback;
* manter credenciais fora das abstrações atuais de configuração operacional;
* não introduzir ainda autoridade direta do modelo sobre ferramentas.

Arquitetura conceitual:

```text
Model Request
     │
     ▼
Model Router
     │
     ├── Local Provider
     │
     └── Online Provider
```

Tool calling permanece reservado para:

```text
v0.3.2 — Controlled Agent & Tool Calling
```

---

# Licença

A licença do projeto será definida posteriormente.

---

# Status

```text
Nexus Core
──────────────────────────────────────────────────────
Stable Version:       v0.3.0
Current Capability:   Local Model Layer
Next Development:     v0.3.1
Runtime:              Python 3.12
Database:             SQLite
Sandbox:              Docker
Local Model Runtime:  Ollama
Reference Model:      qwen3:1.7b
Testing:              pytest
Tests:                338 passed
Development Status:   ACTIVE
──────────────────────────────────────────────────────
```

---

**Nexus Core**

Assistente pessoal de inteligência artificial **local-first**.