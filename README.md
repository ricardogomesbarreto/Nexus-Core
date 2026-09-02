# Nexus Core

Assistente pessoal de inteligência artificial local-first, multimodal, modular e orientado a agentes.

**Versão atual:** `v0.2.0`

## Objetivos

* Conversação por texto e voz
* Operação offline e online
* Memória persistente
* Knowledge Base
* Visão computacional
* Interpretação de tela
* Automação do desktop
* Desenvolvimento de software assistido
* Geração multimídia
* Integração futura com Arduino e ESP32
* Arquitetura distribuída para múltiplos dispositivos
* Arquitetura com modelos locais e provedores online
* Sistema de segurança centralizado

## Princípios

* Open Source
* Local First
* Security First
* Privacy First
* Modularidade
* Testabilidade
* Observabilidade
* Princípio do menor privilégio

## Estado atual

A versão `v0.2.0` amplia a infraestrutura do Nexus Core com a introdução do gerenciamento de conectividade e dos modos de operação do sistema.

O Nexus agora consegue determinar, durante sua inicialização, se existe conectividade externa e definir automaticamente seu modo de execução como `ONLINE` ou `OFFLINE`.

Também é possível forçar o funcionamento em modo offline por meio da configuração da aplicação.

Atualmente o projeto possui:

* Núcleo da aplicação
* Configuração tipada
* Sistema de logs
* Banco SQLite
* Sistema de eventos
* Health Status
* Health Check integrado
* Gerenciamento de conectividade
* Detecção de estado da rede
* Runtime Mode
* Modos `ONLINE`, `OFFLINE` e `DEGRADED`
* Arquitetura de ferramentas
* Registro de ferramentas
* Executor central de ferramentas
* Security Gate
* Política de riscos
* Política de permissões por ferramenta
* Segurança de caminhos
* Auditoria de operações
* Ferramentas de filesystem
* Terminal isolado em Docker
* Status detalhado da aplicação
* Monitoramento dos componentes essenciais
* Eventos de conectividade
* Eventos de mudança de runtime
* Suíte automatizada de testes

> O modo `DEGRADED` já faz parte do modelo de runtime, mas sua determinação automática ainda não está implementada. Atualmente o `ConnectivityManager` diferencia conectividade disponível e indisponível.

## Gerenciamento de conectividade

O Nexus Core possui um `ConnectivityManager` responsável por verificar a disponibilidade de conectividade externa.

A verificação utiliza um endpoint configurável e possui timeout para evitar bloqueios prolongados durante a inicialização.

O resultado da verificação fornece:

```text
online
latency_ms
endpoint
```

Atualmente, `latency_ms` está reservado na estrutura de status, mas a implementação ainda não realiza a medição efetiva da latência.

A conectividade externa não é requisito para o funcionamento do núcleo local do Nexus.

## Modos de operação

O Nexus Core possui uma camada de runtime representada por `RuntimeMode`.

Os modos disponíveis são:

```text
ONLINE
OFFLINE
DEGRADED
```

### ONLINE

Indica que o Nexus possui conectividade externa disponível.

### OFFLINE

Indica que a conectividade externa está indisponível ou que o modo offline foi explicitamente forçado pela configuração.

### DEGRADED

Representa um estado futuro em que o Nexus possui conectividade, porém algum serviço externo necessário está parcialmente indisponível.

A detecção automática de `DEGRADED` será implementada posteriormente.

## Configuração de modo offline

O Nexus possui uma configuração:

```python
offline_mode: bool = True
```

Quando:

```text
offline_mode = True
```

o Nexus força sua operação em `OFFLINE`, independentemente da disponibilidade da Internet.

Quando:

```text
offline_mode = False
```

o Nexus realiza a verificação automática de conectividade.

Essa abordagem permite que o sistema tenha comportamento determinístico em ambientes que exigem operação exclusivamente local.

## Eventos de conectividade e runtime

A arquitetura de eventos foi ampliada para representar mudanças relacionadas à conectividade e ao modo de operação.

Eventos disponíveis:

```text
network.online
network.offline
runtime.mode_changed
```

### NETWORK_ONLINE

Publicado quando o Nexus detecta conectividade externa disponível.

Os dados do evento incluem:

```text
endpoint
latency_ms
```

### NETWORK_OFFLINE

Publicado quando o Nexus realiza a verificação automática e detecta ausência de conectividade externa.

Os dados do evento incluem:

```text
endpoint
latency_ms
```

### RUNTIME_MODE_CHANGED

Publicado quando o modo de execução é determinado ou alterado.

Os dados incluem:

```text
mode
reason
```

Exemplo:

```text
mode: ONLINE
reason: Conectividade externa disponível
```

ou:

```text
mode: OFFLINE
reason: Conectividade externa indisponível
```

## Health Check

O Nexus Core possui um mecanismo centralizado de verificação do estado dos componentes essenciais.

Os componentes monitorados são:

```text
Core
Configuration
Database
Logger
EventBus
SecurityGate
ToolRegistry
Terminal Sandbox
```

Além desses componentes, o Health Status também acompanha:

```text
Network Online
Runtime Mode
Runtime Reason
```

O sistema fornece um estado geral:

```text
Health Monitor
```

A conectividade externa **não é requisito para o Nexus ser considerado `READY`**.

Portanto, um Nexus funcionando completamente em modo offline pode apresentar:

```text
Network: OFFLINE
Mode: OFFLINE
Health Monitor: READY
```

## Arquitetura atual

```text
NEXUS CORE

│
└── NexusApplication
    │
    ├── EventBus
    │
    ├── Database
    │
    ├── ConnectivityManager
    │
    ├── HealthStatus
    │
    ├── SecurityGate
    │
    ├── ToolRegistry
    │
    └── ToolExecutor
        │
        └── SecurityGate
            │
            ├── Risk Policy
            ├── Tool Permissions
            ├── Path Security
            └── Audit Log
                │
                └── Tools
                    ├── Filesystem
                    ├── System Info
                    └── Terminal Sandbox
                        │
                        └── Docker
```

## Sistema de segurança

Toda ferramenta executada pelo Nexus deve passar pelo `SecurityGate`.

O sistema utiliza:

* Níveis de risco
* Política central de segurança
* Permissões individuais por ferramenta
* Proteção de caminhos
* Auditoria
* Bloqueio de ferramentas não registradas
* Princípio do menor privilégio

Os níveis de risco são:

```text
SAFE
LOW
MEDIUM
HIGH
CRITICAL
```

A política atual permite automaticamente operações de baixo risco, exige confirmação para operações de risco médio e bloqueia operações de alto risco ou críticas.

## Terminal Sandbox

O terminal do Nexus não executa comandos diretamente no sistema operacional do usuário.

A execução ocorre dentro de um container Docker isolado.

Características atuais:

* Sem acesso à rede
* Filesystem somente leitura
* `/tmp` temporário
* Limite de memória
* Limite de CPU
* Limite de processos
* `no-new-privileges`
* Remoção automática do container
* Execução como usuário não-root
* Limite de tempo
* Limite de saída

Essa camada constitui a infraestrutura atual de execução controlada de comandos do Nexus Core.

## Painel de status

A aplicação possui uma interface de status executável pelo terminal.

Execução:

```bash
python -m nexus.main
```

O painel apresenta:

* Versão do Nexus
* Estado do Core
* Configuration
* Database
* Logger
* EventBus
* SecurityGate
* ToolRegistry
* Terminal Sandbox
* Health Monitor
* Node
* Estado da rede
* Modo de operação

Exemplo em modo offline:

```text
╔══════════════════════════════════════════════╗
║                  N E X U S                   ║
║                    v0.2.0                    ║
╠══════════════════════════════════════════════╣
║ Core              ✓ ONLINE                  ║
║ Configuration     ✓ READY                   ║
║ Database          ✓ READY                   ║
║ Logger            ✓ READY                   ║
║ EventBus          ✓ READY                   ║
║ SecurityGate      ✓ READY                   ║
║ ToolRegistry      ✓ READY                   ║
║ Terminal Sandbox  ✓ READY                   ║
╠══════════════════════════════════════════════╣
║ Health Monitor    ✓ READY                   ║
╠══════════════════════════════════════════════╣
║ Node              NEXUS-NODE-01             ║
║ Network           ✗ OFFLINE                 ║
║ Mode              OFFLINE                   ║
╚══════════════════════════════════════════════╝
```

O painel utiliza os valores reais do `HealthStatus`, não um modo de operação fixo.

## Testes

O projeto possui uma suíte automatizada utilizando `pytest`.

Estado atual:

```text
87 passed
```

Os testes devem ser executados a partir da raiz do projeto:

```bash
python -m pytest -q
```

A suíte atual valida, entre outros componentes:

* Configuração
* Banco de dados
* Logging
* EventBus
* Security Gate
* Tool Registry
* Ferramentas
* Path Security
* Terminal Sandbox
* Health Check
* Connectivity Manager
* Runtime Mode
* Eventos de conectividade
* Eventos de mudança de runtime
* Integração entre runtime e Health Status
* Painel e inicialização da aplicação

## Ambiente

Ambiente de desenvolvimento atual:

* Ubuntu 24.04 LTS
* Python 3.12
* Git
* Docker
* SQLite
* pytest

## Dependências

O Nexus Core mantém o runtime Python sem dependências externas obrigatórias neste estágio.

Dependências de desenvolvimento:

```text
pytest
```

Arquivos:

```text
requirements/

├── base.txt
└── dev.txt
```

O arquivo `base.txt` permanece sem dependências externas obrigatórias.

O arquivo `dev.txt` contém as dependências necessárias para desenvolvimento e testes.

## Estrutura do projeto

```text
Nexus Core/

│
├── nexus/
│   ├── config/
│   ├── core/
│   │   ├── application.py
│   │   ├── connectivity.py
│   │   ├── logger.py
│   │   └── runtime.py
│   ├── database/
│   ├── events/
│   ├── monitoring/
│   ├── security/
│   ├── tools/
│   └── main.py
│
├── requirements/
│   ├── base.txt
│   └── dev.txt
│
├── scripts/
├── tests/
├── data/
├── logs/
├── .gitignore
└── README.md
```

## Histórico de versões

### v0.1.0 — Foundation

* Estrutura inicial do projeto
* Ambiente virtual
* Configuração inicial
* Logging
* SQLite
* CLI/status
* Estrutura inicial de testes

### v0.1.1 — Infrastructure Core

* Settings tipado
* Logging estruturado
* Eventos do sistema
* Banco SQLite
* Health Status
* Ciclo de vida da aplicação

### v0.1.2 — Event Architecture

* EventBus
* NexusEvent
* Catálogo de eventos
* Publicação e assinatura
* Múltiplos handlers
* Testes de eventos

### v0.1.3 — Security Gate

* RiskLevel
* PermissionDecision
* SecurityPolicy
* SecurityRequest
* SecurityResult
* SecurityGate

### v0.1.4 — Tool Architecture

* NexusTool
* ToolResult
* ToolRegistry
* ToolExecutor
* Integração entre ferramentas e Security Gate

### v0.1.5 — Path Security

* Proteção de caminhos
* Prevenção de traversal
* Tratamento de symlinks
* Áreas protegidas
* Área autorizada dentro do HOME

### v0.1.6 — Tool Permissions + Audit Log

* ToolPermissionPolicy
* Permissões individuais
* AuditLogger
* Auditoria de decisões de segurança
* Auditoria dos resultados de execução

### v0.1.7 — Secure File Tools

* ListDirectoryTool
* ReadFileTool
* Proteção de caminhos
* Limite de leitura de 1 MB
* Leitura UTF-8
* Auditoria
* Testes

### v0.1.8 — Terminal Sandbox

* TerminalSandboxTool
* Execução através do Docker
* Isolamento de rede
* Filesystem somente leitura
* Limites de CPU e memória
* Limite de processos
* `no-new-privileges`
* Remoção automática dos containers
* Execução sem privilégios de root
* Timeout
* Limite de saída

### v0.1.9 — Health Check & Application Status

* HealthStatus ampliado
* Monitoramento de oito componentes
* Integração do Health Check ao NexusApplication
* Integração do ToolRegistry
* Integração do ToolExecutor
* Integração do SecurityGate
* Registro do Terminal Sandbox
* Painel de status detalhado
* Identificação da versão da aplicação
* Verificação do estado geral `READY`
* 58 testes automatizados passando

### v0.2.0 — Connectivity & Runtime Mode

* ConnectivityManager
* Detecção automática de conectividade externa
* Configuração de modo offline
* RuntimeMode
* Estados `ONLINE`, `OFFLINE` e `DEGRADED`
* RuntimeStatus como estrutura reservada para evolução do estado de runtime
* Integração de RuntimeMode e runtime_reason ao HealthStatus
* Eventos `NETWORK_ONLINE`
* Eventos `NETWORK_OFFLINE`
* Evento `RUNTIME_MODE_CHANGED`
* Dados associados aos eventos de runtime
* Detecção de modo ONLINE
* Detecção de modo OFFLINE
* Suporte a OFFLINE forçado
* Painel de status com modo dinâmico
* Painel de status com estado da rede
* Testes automatizados de conectividade e runtime
* 87 testes automatizados passando

## Próximas etapas

O desenvolvimento seguirá de forma incremental, mantendo a segurança como requisito estrutural.

Próximas áreas previstas:

* Configuração de ambientes `development` e `production`
* Detecção e implementação do estado `DEGRADED`
* Monitoramento contínuo de conectividade
* Detecção de mudanças de conectividade durante a execução
* Interface gráfica
* Interface de voz
* Speech-to-Text
* Text-to-Speech
* Wake Word
* Integração com modelos locais
* Memória persistente
* Knowledge Base
* Visão computacional
* Interpretação de tela
* Agentes
* Automação controlada do desktop
* Integração com Arduino e ESP32
* Arquitetura distribuída
* Integração opcional com provedores online

## Segurança e limitações atuais

O Nexus Core ainda está em desenvolvimento.

A arquitetura atual prioriza impedir que o núcleo de inteligência tenha autoridade irrestrita sobre o sistema operacional.

Em especial:

* O LLM não deve possuir acesso direto ao sistema operacional.
* Ferramentas devem passar pelo `SecurityGate`.
* Conteúdo obtido da web, PDFs, imagens ou outros documentos deve ser tratado como dado não confiável.
* Prompt injection deve ser tratado como conteúdo não confiável e nunca como uma instrução privilegiada.
* Operações de alto risco permanecem bloqueadas.
* A execução de comandos utiliza sandbox Docker.
* O uso do grupo `docker` pelo usuário possui implicações de segurança e deverá ser posteriormente substituído ou restringido por uma camada privilegiada específica.
* A conectividade externa não deve conceder autoridade adicional ao núcleo de inteligência.
* O modo `ONLINE` representa disponibilidade de rede, não autorização automática para executar ações externas.

## Licença

A licença do projeto será definida posteriormente.

---

**Nexus Core**

Assistente pessoal de inteligência artificial local-first.
