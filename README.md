# Nexus Core

Assistente pessoal de inteligência artificial local-first, multimodal, modular e orientado a agentes.

**Versão atual:** `v0.1.9`

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

A versão `v0.1.9` amplia a camada de infraestrutura do Nexus Core, integrando o sistema de Health Check aos principais componentes da aplicação e disponibilizando um painel de status detalhado no terminal.

Atualmente o projeto possui:

* Núcleo da aplicação
* Configuração tipada
* Sistema de logs
* Banco SQLite
* Sistema de eventos
* Health Status
* Health Check integrado
* Arquitetura de ferramentas
* Registro de ferramentas
* Executor central de ferramentas
* Security Gate
* Política de riscos
* Política de permissões por ferramenta
* Segurança de caminhos
* Auditoria de operações
* Ferramentas de filesystem
* Ferramenta de informações do sistema
* Terminal isolado em Docker
* Status detalhado da aplicação
* Monitoramento de oito componentes principais
* Suíte automatizada de testes

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

O sistema também fornece um estado geral:

```text
Health Monitor
```

O Nexus é considerado `READY` somente quando todos os componentes essenciais estão operacionais.

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

Essa camada constitui a primeira infraestrutura de execução controlada de comandos do Nexus Core.

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
* Modo de operação

Exemplo:

```text
╔══════════════════════════════════════════════╗
║                 N E X U S                    ║
║                 v0.1.9                       ║
╠══════════════════════════════════════════════╣
║ Core             ✓ ONLINE                    ║
║ Configuration    ✓ READY                     ║
║ Database         ✓ READY                     ║
║ Logger           ✓ READY                     ║
║ EventBus         ✓ READY                     ║
║ SecurityGate     ✓ READY                     ║
║ ToolRegistry     ✓ READY                     ║
║ Terminal Sandbox ✓ READY                     ║
╠══════════════════════════════════════════════╣
║ Health Monitor   ✓ READY                     ║
╠══════════════════════════════════════════════╣
║ Node: NEXUS-NODE-01                          ║
║ Mode: OFFLINE                                ║
╚══════════════════════════════════════════════╝
```

## Testes

O projeto possui uma suíte automatizada utilizando `pytest`.

Estado atual:

```text
58 passed
```

Os testes devem ser executados a partir da raiz do projeto:

```bash
pytest -q
```

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

## Estrutura do projeto

```text
Nexus Core/
│
├── nexus/
│   ├── config/
│   ├── core/
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

## Próximas etapas

O desenvolvimento seguirá de forma incremental, mantendo a segurança como requisito estrutural.

Próximas áreas previstas:

* Configuração de ambiente `development` e `production`
* Detecção real do modo online/offline
* Sistema de conectividade
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

## Licença

A licença do projeto será definida posteriormente.

---

**Nexus Core**
Assistente pessoal de inteligência artificial local-first.
