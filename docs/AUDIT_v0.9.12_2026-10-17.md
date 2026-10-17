# Auditoria técnica e documental — NEXUS CORE v0.9.12

**Data:** 17/10/2026. **Escopo:** repositório GitHub `ricardogomesbarreto/Nexus-Core`,
histórico das solicitações do usuário sobre NEXUS CORE e módulos de runtime,
instalação, segurança, UI, áudio, visão, ferramentas criativas, testes e
workflows de release. Esta é uma auditoria dirigida por código e evidências
disponíveis, **não** uma afirmação de leitura manual linha por linha de cada
arquivo binário, nem homologação independente de hardware ou de ferramentas
Rust não instaladas.

## Escopo e fontes verificáveis

O inventário do commit-base `9de8aa7870d275b184ea077b4f06bd36d2f13daf`
registra **345 arquivos versionados**. Os pontos de maior risco foram
inspecionados no código e cruzados com os respectivos testes e as diretrizes:

- `nexus/agent/planner.py`, `nexus/core/application.py`,
  `nexus/tools/{executor,contracts,creative,filesystem,terminal,desktop_apps}.py`,
  `nexus/security/{security_gate,paths,policies}.py`;
- `nexus/desktop/{window,conversation,chat_archive,preferences,runtime_log}.py`,
  `nexus/voice/local.py`, `nexus/vision/local.py`,
  `nexus/models/{resource_budget,ollama_provider}.py`;
- `scripts/{install_linux,nexus_core_session}.sh/.py`, conforme a extensão,
  `nexus/platforms/resources.py`, `nexus/updates/*`;
- `README.md`, `docs/PROJECT_GUIDELINES.md`,
  `docs/RELEASE_NOTES_v0.9.12.md`,
  `docs/UBUNTU_PHYSICAL_ACCEPTANCE_v0.9.12.md`,
  `.github/workflows/ci.yml` e `release-v0.9.12.yml`;
- testes de instalador e serviços, conversões autorizadas, integração de
  interface, reconhecimento, paths protegidos, limites de recursos e releases.

A última CI confirmada **antes desta auditoria** foi a da PR #69:
`1631 passed`, Ubuntu 24.04/Python 3.12/PostgreSQL 16/Xvfb, execução
`39065716000`. O executável reportou `Nexus Core 0.9.12`.
Isso **não comprova** funcionamento ou desempenho de Ollama, Vosk,
câmera ou os CLIs reais no computador físico.

## Achados e tratamento

| ID | Severidade | Evidência e implicação | Medida |
| --- | --- | --- | --- |
| A01 | Alta | `scripts/install_linux.py::_user_ollama_service` executava `systemctl --user enable --now` e criava uma unidade `WantedBy=default.target`. Isso permitia Ollama na próxima sessão mesmo quando o usuário não estivesse utilizando o Nexus | Nova unidade estática, sem bloco `[Install]`, com apenas `daemon-reload` e `start` nesta sessão. Não altera serviços do sistema/instalações antigas. Testes de boot e de não sobrescrever unidade existente |
| A02 | Alta | `CraftConvertTool` verificava `outfile.is_file()` e depois usava `outfile.read_bytes()`, ambos seguindo eventual symlink criado por um processo externo | Lê o resultado por descriptor de arquivo regular e `O_NOFOLLOW`, com raiz ancorada na pasta temporária privada e tamanho máximo |
| A03 | Média | Conversor podia retornar código zero e arquivo vazio ou com bytes incompatíveis com a extensão, que seriam publicados como sucesso | Rejeita saída vazia e formatos conhecidos com assinatura incompatível (PDF, PNG, JPEG, WebP, DOCX e ODT); isso não substitui validador semântico nem teste do CLI real |
| A04 | Média | `EditImageTool` tratava advertência de imagem-bomba, mas não o erro `Image.DecompressionBombError` | Tratamento explícito sem expor arquivo/bytes ou exceção bruta ao chat |
| A05 | Baixa | Caminho único de fonte DejaVu referenciava layout Ubuntu/Debian e o fallback tinha tamanho reduzido | Fontes alternativas para Fedora, Arch e Liberation, preservando cores e layout; não declara suporte universal |
| A06 | Média | README e notas v0.9.12 destacavam apenas PR #66 e 1.619 testes, embora #69 já estivesse integrada com 1.631 | Estado atual colocado no topo, com referência a esta auditoria, à CI, aos limites e às pendências |
| A07 | Risco residual | O adaptador opcional de PhotoCraft/WordCraft/PdfCraft roda um programa de terceiros como usuário do Linux, **sem isolamento por contêiner** | Declaração explícita dessa restrição no README; autorizar somente binários instalados pelo próprio usuário e fontes confiáveis. Sem download/execução automática dos ZIPs |
| A08 | Dependência física | No notebook Ubuntu/Wayland, houve transcrição pontual Vosk em ALSA/PipeWire, mas escuta contínua apresentou falhas em outra sessão; inferência visual CPU chegou a cerca de 68–119 s e alta pressão de RAM/swap | Não afirmar resolução definitiva por CI. Repetir testes reais de escuta contínua, visão, temperatura e permissões |

## Decisões de arquitetura preservadas

- **Local-first, gratuito e open source**, sem hospedagem, cobrança, API paga ou
  dependência permanente da internet. PostgreSQL e Ollama são locais.
- Ubuntu/Debian como baseline inicial, evolução progressiva para outras distros.
  Não anunciar instalação automática validada em todas as distribuições.
- Nenhum serviço deve ser habilitado automaticamente no boot pela nova
  instalação; iniciá-los manualmente só durante o uso e encerrá-los quando
  nenhum outro aplicativo depender deles. Um serviço **preexistente** ainda
  pode estar habilitado: confira e desabilite explicitamente.
- Cor vinho `#722F37`, identidade NEXUS, UI Tk e preferências de voz e
  histórico são mantidas.
- Ferramentas de criação e edição produzem **cópias novas**, dentro de HOME,
  após passar pelo `SecurityGate` e confirmação conforme risco. Saídas
  originais não são substituídas. Nada permite shell do host livre.
- A geração de fotografia do zero por IA **não foi implementada**.
  `create_graphic_local` gera cartaz gráfico; edição Pillow é limitada.
  Conversão externa exige binários reais disponíveis e integração testada.
- Compensações de desempenho `eco`/ `balanced` seguem configuráveis.
  `keep_alive=0s` libera modelo entre respostas, mas pode aumentar a
  latência de carregamento posterior; não promete menor temperatura por si só.

## Pendências de homologação — NÃO publicar versão estável

1. Instalação a partir de ambiente limpo no Ubuntu, unidade Ollama estática
   realmente desabilitada no login e PostgreSQL `start.conf=manual` quando
   apropriado, sem quebrar outros projetos.
2. Reconhecimento de **duas ou mais falas seguidas** sem pressionar botão,
   pausa/retomada, autorização de operações por botão/texto/voz, audibilidade
   feminina e masculina.
3. Webcam ao vivo, nova captura com consentimento e pertinência da resposta
   visual; memória, swap, temperatura e ventoinha durante Ollama.
4. Execução **real e identificada** dos três programas PhotoCraft,
   WordCraft e PdfCraft instalados no Ubuntu: confirmar versões/sintaxes,
   conversão de conteúdo real, desempenho e limitações de segurança. Os
   testes simulados não bastam.
5. Testes de instalação/atualização/reversão em ambiente descartável e
   automação X11/Wayland com escopo autorizado.
6. CI `push` do SHA exato da `main` e revisão expressa do bloqueio
   `if: false` do workflow de publicação; **não desbloquear por esta PR**.

## Procedimento reprodutível no Ubuntu

Com internet para baixar código e componentes previamente autorizados:

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
python3 scripts/install_linux.py
bash scripts/nexus_core_session.sh start
NEXUS_RESOURCE_PROFILE=eco ~/.local/bin/nexus-core --desktop 2>&1 | tee "$HOME/nexus-core-desktop.log"
```

Em outro terminal, durante os testes:

```bash
tail -f "$HOME/nexus-core-desktop.log" | grep --line-buffered 'TESTE-LOCAL'
~/.local/bin/nexus-core --acceptance-log
```

Para conferir autostart sem alterar o sistema:

```bash
systemctl --user is-enabled nexus-core-ollama.service
systemctl is-enabled ollama.service postgresql.service postgresql@18-main.service
cat /etc/postgresql/18/main/start.conf
```

Depois de fechar o assistente, caso outros produtos NEXUS não dependam
dos mesmos serviços:

```bash
bash scripts/nexus_core_session.sh stop
```

O script de sessão não habilita serviços no boot. O histórico de
conversas (se a opção `Salvar conversas` estiver ativa) é **texto local
legível pelo usuário da conta Linux**; perguntas contendo segredos
também podem ser armazenadas. O software não oferece criptografia
integral automática desses registros.

**Situação da auditoria:** código e testes de regressão preparados;
somente considerar essas correções integradas após CI real bem-sucedida
e merge. A publicação v0.9.12 permanece **bloqueada** até os gates
físicos acima.
