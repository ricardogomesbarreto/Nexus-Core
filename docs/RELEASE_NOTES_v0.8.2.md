# NEXUS CORE v0.8.2 — Ubuntu Desktop Baseline & Distribution Portability

## Diretriz oficial de plataforma

**Ubuntu Desktop 24.04 LTS é a plataforma de desenvolvimento, instalação inicial e homologação da aplicação.** O NEXUS CORE continua sendo um aplicativo **local Linux**, gratuito e open source, que não precisa de hospedagem nem de banco em nuvem. **Debian, Fedora, Arch, SteamOS e Ubuntu de outras versões não são, nesta versão, destinos homologados do instalador automático.** O projeto será preparado para outras distribuições em incrementos posteriores, conforme testes reais e política de suporte.

### Implementação desta versão

- Novo módulo de compatibilidade isolado `nexus.platforms`: leitura segura de `/etc/os-release` (`ID` e `VERSION_ID`), sessão X11/Wayland e versão Python, com perfil tipado e contrato de capacidades.
- `nexus-core --platform-check` e `python3 scripts/install_linux.py --check` geram um **diagnóstico somente leitura** para qualquer Linux. Relatam perfil, recursos visíveis, dependências ausentes e distinção entre GUI nativa Tk e automação de teclado X11. Os diagnósticos não acessam câmera/microfone, iniciam PostgreSQL/Ollama/Docker nem executam comandos de instalação.
- Instalador guiado restringe alterações de pacotes de sistema, provisionamento de PostgreSQL e criação do venv gerenciado ao Ubuntu 24.04 LTS (Python 3.12+). O instalador verifica o perfil **antes** de qualquer alteração, não toma a variável `ID_LIKE=debian` como autorização para usar apt em Debian ou SteamOS.
- Dependências essenciais do Ubuntu têm uma matriz única versionada. Se faltarem pacotes, `sudo apt-get update/install` exige consentimento no terminal; recusa, falha ou ausência persistente de requisitos **interrompem a instalação**, sem relatar sucesso falso.
- `.github/workflows/ci.yml` passa a usar `ubuntu-24.04` explicitamente para estabilizar o ambiente testado, com Python 3.12, PostgreSQL 16, Docker e Xvfb.
- Testes de parsing hostil de os-release, Ubuntu/Wayland vs X11, distros não homologadas e ausência de sudo sem consentimento.
- Identidade visual, conversa por voz, visão autorizada, arquitetura PostgreSQL/Ollama local, atualização verificada v0.8.1 e dispositivos declarativos v0.8.0 permanecem sem ampliação descontrolada.

## Comandos da versão, em ambiente de desenvolvimento

```bash
nexus-core --platform-check
python3 scripts/install_linux.py --check
# Instalação guiada (apenas Ubuntu Desktop 24.04 LTS):
python3 scripts/install_linux.py
```

A leitura do diagnóstico não comprova suporte real ao microfone, webcam, placa de som, modelo Ollama ou servidor PostgreSQL. Sessões Ubuntu Wayland podem executar a interface Tk, mas `xdotool`/interação controlada com outra janela exige sessão X11 local. Não forçar troca de sessão nem desabilitar proteções do Linux automaticamente.

## Preparação para Linux desktop multiplataforma

A camada `nexus.platforms` estabelece a fronteira para adaptadores de pacote, sessão gráfica, áudio, serviços e recursos. O roadmap evoluirá em fases:

1. **Ubuntu 24.04 LTS** — instalação, atualização, banco, GUI, voz, visão, confirmação, recuperação e testes reais como baseline.
2. **Outras versões Ubuntu LTS** — adaptação e homologação individual, conforme suporte de dependências e Python.
3. **Debian/Fedora/Arch/SteamOS** — adaptadores de pacote separados (apt/dnf/pacman), políticas específicas de serviços e permissões, validação de sessões, empacotamento e testes próprios. Nenhum instalador multi-distro foi ativado nesta etapa.
4. **Compatibilidade desktop ampla** — matriz de distribuição/versão/sessão gráfica/hardware e ciclos completos de upgrade e rollback antes de qualquer alegação de suporte universal.

As prioridades e versões futuras são de planejamento, **não funcionalidades já entregues**.

## Critérios para merge/release

- CI Ubuntu 24.04 verde no commit exato do PR e em `main`.
- PRs anteriores **#11 v0.7.3**, **#12 v0.8.0** e **#13 v0.8.1** integrados na ordem correta; o PR #11 ainda exige homologação física X11.
- Instalação, PostgreSQL, Ollama, voz, visão, áudio, webcam e atualização/rollback avaliados em Ubuntu Desktop 24.04 real para marcar a v0.8.2 estável.
- **Sem tag/release antecipada** e sem declarar suporte de outras distribuições antes de homologação.

Data do planejamento: 10 de outubro de 2026.
