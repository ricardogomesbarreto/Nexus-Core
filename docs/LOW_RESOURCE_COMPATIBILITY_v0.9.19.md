# NEXUS CORE v0.9.19 — Compatibilidade e consumo de recursos (em desenvolvimento)

**Escopo real:** desktops Linux compatíveis, especialmente Ubuntu 26.04.
Não é possível prometer desempenho idêntico em todo computador nem suporte
a Windows/macOS, arquiteturas sem modelos compatíveis ou ambientes
que não disponham de PostgreSQL, Ollama e dependências opcionais.

## Otimizações adicionadas à branch

O perfil automático `NEXUS_RESOURCE_PROFILE=auto` agora consulta a
memória realmente disponível no Linux, inclusive quotas da hierarquia
cgroup v2 (systemd/user.slice, containers) ou cgroup v1. Respeita a
afinidade de CPU e a quota `cpu.max`/CFS ao dimensionar threads. O
cálculo é *somente leitura*, sem sudo, sem alterações nas frequências,
sem downloads e sem novos serviços. Se o kernel não oferecer os
dados, a informação é marcada como indisponível — não se inventa
RAM livre.

### Orçamentos automáticos de referência

| Memória efetiva do processo | Perfil | Threads de inferência | Contexto de texto | Lado máximo de imagem | Residência de modelo |
|---|---|---:|---:|---:|---|
| Até 4 GiB | eco ultraleve | 1 | 768 tokens | 512 px | 0 s |
| Acima de 4 até 8 GiB | eco | até 2 | 1.024 tokens | 768 px | 0 s |
| Mais de 8 GiB e RAM disponível acima de 2 GiB | equilibrado | até 4 | 2.048 tokens | 1.536 px | 45 s |
| RAM disponível baixa, independentemente do total | eco | até 2; 1 em máquinas de até 4 GiB | conforme memória efetiva | conforme memória efetiva | 0 s |

Os valores de CPU se sujeitam também a quotas e afinidade. O limite
de RAM não garante que o modelo Ollama escolhido caiba na máquina;
em hardware de 2–4 GiB, modelos maiores podem ser recusados ou
inviáveis. Sem margens adequadas, a inferência deve falhar de forma
controlada. O usuário ainda pode escolher explicitamente `eco` ou
`balanced`, assumindo os limites correspondentes.

## Desktop

A janela Tk mantém atualização de estado a cada **80 ms quando ativa**
(voz, câmera, conclusão de tarefas, encerramento) e passa a **250 ms
quando ociosa**, diminuindo a frequência de verificações em repouso
de 12,5 para 4 por segundo (estimativa matemática, não benchmark de CPU).
A consulta de conectividade local é limitada a no máximo uma a cada
dois segundos. Nenhuma checagem de internet é iniciada pelo Nexus.

## Diagnóstico read-only antes de testar

~~~bash
cd "$HOME/Projetos/Nexus-Core"
python3 -m nexus.main --resource-check
python3 -m nexus.main --platform-check
~~~

O primeiro comando retorna memória, swap, modelos já carregados
que a API local Ollama consegue informar e um novo campo
`effective_profile`: RAM efetiva/atual, perfil, limite de threads,
contexto e tamanho máximo de imagem. Não faz inferência, não baixa modelos,
não altera ou inicializa PostgreSQL/Ollama e não acessa hosts externos.
O segundo faz checagens passivas de suporte Linux.

Para uma sessão real, use os scripts de sessão existentes sob comando do
usuário, **não** `systemctl enable`:

~~~bash
bash scripts/nexus_core_session.sh start
NEXUS_RESOURCE_PROFILE=auto bash scripts/nexus_core_session.sh desktop
bash scripts/nexus_core_session.sh stop
~~~

O gerenciamento de serviços deve preservar instâncias preexistentes e
parar apenas instâncias iniciadas pelo Nexus, com controle pela identidade
do processo. Quando PostgreSQL ou Ollama não estiverem disponíveis,
a experiência completa não estará operacional; funções puramente locais
seguem sujeitas a permissões e dependências específicas.

## Gates de estabilidade

- CI GitHub: Python 3.12, PostgreSQL 16, testes Tk/Xvfb, compilação e
  regressão de funcionalidades. **Exigir verde no commit final.**
- Ubuntu 26.04, notebook de RAM limitada: medir PSS/RSS, swap, CPU, latência,
  aquecimento e resposta em pelo menos dois turnos de voz consecutivos.
- Testar dois perfis de máquina (4 GiB e 16 GiB ou mais) em sistemas Linux
  reais, não somente mocks de cgroups.
- Testar Wayland e X11, indisponibilidade de áudio/câmera, ausência de
  FFmpeg/Kiwix/Kolibri, e ausência de PostgreSQL/Ollama.
- Confirmar retorno ao repouso e ausência de processos que persistam após
  fechar o assistente; nunca desativar serviços não iniciados por ele.

**Status:** implementação na branch do PR #102, não é release estável nem
homologação de compatibilidade universal. Recursos de imagem/IA/voz exigem
hardware e dependências suficientes; execução local e offline não equivale
a execução em qualquer plataforma.
