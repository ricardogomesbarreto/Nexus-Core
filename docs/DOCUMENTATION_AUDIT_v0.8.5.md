# Auditoria integral da documentação — NEXUS CORE v0.8.5

**Escopo auditado em 10/10/2026:** versão de desenvolvimento empilhada na v0.8.4, com código v0.8.2 integrado à `main`. A última tag/release pública verificada é **v0.7.2**. Esta auditoria é revisão documental e de coerência com os módulos e testes; **não é certificação física nem auditoria formal independente de segurança**.

## Arquivos de documentação inspecionados

- `README.md` — histórico extenso, roteiro de arquitetura, linha de releases, instalação, integração de voz/visão, segurança, distribuição e roadmap.
- `docs/ICONOGRAFIA.md` — identidade Wine Red e ícones/SVG locais em interface desktop nativa, sem web ou CDN.
- `docs/X11_PHYSICAL_HOMOLOGATION.md` — sessão X11 local, consentimento para cada ação, teste real de digitação/navegação e critérios de aceite.
- **Todas as 17 notas de versão disponíveis neste snapshot**: `RELEASE_NOTES_v0.3.9.md`, `v0.4.0`, `v0.4.1`, `v0.5.0`, `v0.6.0`, `v0.6.1`, `v0.6.2`, `v0.6.3`, `v0.7.0`, `v0.7.1`, `v0.7.2`, `v0.7.3`, `v0.8.0`, `v0.8.1`, `v0.8.2`, `v0.8.3` e `v0.8.4`.
- `.github/workflows/ci.yml` e os **sete** workflows de release existentes (`release-v0.7.2.yml`, `v0.7.3`, `v0.8.0`, `v0.8.1`, `v0.8.2`, `v0.8.3` e `v0.8.4`), conferidos quanto ao gatilho e bloqueio de releases não homologadas.
- Para verificar se as promessas operacionais tinham contrapartida no código, também foram inspecionados `nexus/platforms/*`, `nexus/updates/*`, `scripts/install_linux.py`, `nexus/main.py`, `nexus/config/settings.py`, `tests/test_linux_bootstrap_updates.py` e as suítes Ubuntu recentes.

## Contratos em vigor — não alterar sem revisão explícita

| Área | Invariante documentada |
| --- | --- |
| Distribuição | Aplicativo desktop Linux, gratuito/open source, sem hospedagem, sem assinatura ou recursos pagos. Ubuntu Desktop 24.04 LTS é o **único instalador automático atualmente direcionado**. Outras distribuições serão homologadas posteriormente |
| IA e dados | PostgreSQL e inferência Ollama **locais**; nenhuma chamada automática a um serviço de modelo em nuvem. Capacidade offline preservada, dependente das ferramentas/modelos instalados |
| Design | Manter marca Nexus Line, cor `#722F37`, ícones locais e experiência Tk; não converter o assistente em sistema web |
| Voz | Vosk/ALSA/eSpeak NG, seleção masculina/feminina e possibilidade de pausar a escuta. Diagnóstico de pacotes não certifica microfone/alto-falantes físicos |
| Visão | Imagem, tela e câmera somente por solicitação e consentimento específicos; não persistir imagens automaticamente; resposta em texto e voz condicionada às opções locais |
| Ferramentas | SecurityGate, ferramentas mediadas e confirmações individuais para digitação/navegação X11; sem autonomia para controle ilimitado de janelas, shell do host ou ações sensíveis |
| Dispositivos | Arduino/ESP32 apenas como manifestos declarativos e read-only na v0.8.0; ainda **sem** telemetria, transporte nem controle físico |
| Instalação | Não rodar como root, obter autorização para `sudo apt`, instalar Python em venv individual, não executar `curl | bash`, preservar dados/credenciais |
| Atualização | Opt-in; pacote de release oficial e SHA-256, aplicação fora de uma conversa e no próximo início; falha preserva a versão anterior; ausência de assinatura independente/lockfile total declarada |
| Publicação | CI Ubuntu 24.04/Python 3.12/PostgreSQL 16/Docker/Xvfb para o SHA exato; **Xvfb não substitui** hardware físico; sem tag estável antes de homologação |

## Achados e tratamento

| Achado | Classificação | Providência v0.8.5 |
| --- | --- | --- |
| O roteiro X11 dizia que PRs #11/#12 ainda estavam abertos, após integração na main | Documentação operacional desatualizada | **Corrigido** o estado atual, mantendo teste físico pendente |
| Notas da v0.8.1 citavam Debian como alvo do instalador; v0.8.2 restringiu ao Ubuntu 24.04 | Diretriz superada por versão posterior | **Nota retrospectiva adicionada** à v0.8.1; histórico mantido |
| v0.7.3 e v0.8.0 eram descritas como PRs empilhados | Estado temporal superado | Atualizações de status acrescentadas sem apagar limites históricos |
| `previous` era preservado pelo atualizador, mas não existia recuperação executável quando `current/bin/python` estivesse danificado | Lacuna funcional contra objetivo de recovery da v1.0 | **Novo utilitário `nexus-core-recover` independente do ambiente do app**, com consulta offline e reversão interativa |
| Atualizador poderia reaplicar a versão problemática após rollback | Risco operacional | Recuperação **desativa** auto-update antes de selecionar a versão anterior |
| CI não testa microfone/câmera/software alvo X11/modelo real | Homologação incompleta | **Permanece bloqueio físico**; não declarar release estável |
| PyPI transitivo sem lockfile completo e wheel sem atestação independente | Limitação de cadeia de suprimentos | Não alegar segurança total; endurecimento/assinatura devem ter versões próprias |
| Modelos Vosk/Ollama e suporte Arch/Fedora/SteamOS ainda exigem preparação separada | Escopo futuro | Não acionar instaladores externos nem alegar suporte |
| Conteúdo de memória/knowledge base pode ficar em texto claro no PostgreSQL local | Privacidade documentada | Preservar advertências e limites de retenção; rollback **não** migra nem restaura dados |

## Recuperação autorizada — v0.8.5

A instalação Ubuntu gerenciada entrega o auxiliar **`~/.local/bin/nexus-core-recover`**, composto somente de módulos da biblioteca padrão do Python e ancorado no diretório gerenciado definido pela instalação. Ele não importa o pacote NEXUS CORE do venv ativo. O operador deve fechar a aplicação antes de executar:

```bash
~/.local/bin/nexus-core-recover --status
~/.local/bin/nexus-core-recover --rollback
```

A primeira operação é somente leitura e não exige rede. A segunda exige terminal interativo, **confirmação textual exata `REVERTER`**, uma versão `previous` válida localizada dentro da pasta de versões do mesmo usuário, e troca de apontador sem copiar arquivos de modelo/banco. Nenhum comando é executado pelo assistente sem a solicitação explícita do usuário. O utilitário desabilita a preferência de atualização automática durante a reversão.

**Limites:** restaura somente **a seleção do código Python de uma versão anterior**, não reinstala dependências, não reverte migrações de schema, não restaura o PostgreSQL, não desconecta processos em andamento e não atesta integridade de todos os bytes do venv. Precisa de uma instalação gerenciada previamente criada e de pelo menos uma atualização anterior bem-sucedida. Se a versão anterior estiver ausente/inválida, deve recusar. Recuperação física/offline real no Ubuntu segue pendente de aceite.

## Regras de release e continuidade

A v0.8.5 fica empilhada sobre o PR #16 (v0.8.4), que depende do PR #15 (v0.8.3). A release workflow permanece **desabilitada por `if: ${{ false }}`**, e o código desta versão não será integrado como tag pública sem a sequência aprovada e a homologação real de instalação/recuperação.

O próximo foco técnico após esta versão deve ser executar o roteiro físico Ubuntu 24.04 com microfone, câmera e Ollama reais, rever os riscos de processo/venv/lockfile e planejar a portabilidade para outras distribuições somente após estabilizar Ubuntu.
