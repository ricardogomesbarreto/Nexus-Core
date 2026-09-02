# Nexus Core

Assistente pessoal de inteligência artificial local-first, multimodal, modular e orientado a agentes.

**Versão atual:** `v0.1.8`

## Objetivos

- Conversação por texto e voz
- Operação offline e online
- Memória persistente
- Knowledge Base
- Visão computacional
- Interpretação de tela
- Automação do desktop
- Desenvolvimento de software assistido
- Geração multimídia
- Integração futura com Arduino e ESP32
- Arquitetura distribuída para múltiplos dispositivos
- Arquitetura com modelos locais e provedores online
- Sistema de segurança centralizado

## Princípios

- Open Source
- Local First
- Security First
- Privacy First
- Modularidade
- Testabilidade
- Observabilidade
- Princípio do menor privilégio

## Estado atual

A versão `v0.1.8` estabelece a primeira camada funcional de execução segura de comandos.

Atualmente o projeto possui:

- Núcleo da aplicação
- Configuração tipada
- Sistema de logs
- Banco SQLite
- Sistema de eventos
- Health Status
- Arquitetura de ferramentas
- Registro de ferramentas
- Executor central de ferramentas
- Security Gate
- Política de riscos
- Política de permissões por ferramenta
- Segurança de caminhos
- Auditoria de operações
- Ferramentas de filesystem
- Ferramenta de informações do sistema
- Terminal isolado em Docker
- Suíte automatizada de testes

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