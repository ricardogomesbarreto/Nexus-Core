# NEXUS CORE — Fechamento de código 0.9.12 e roadmap de release

**Data da revisão:** 18/10/2026 · **Versão do pacote:** 0.9.12
· **candidata publicada:** [v0.9.12-rc.3](https://github.com/ricardogomesbarreto/Nexus-Core/releases/tag/v0.9.12-rc.3), commit `6429a5e`, CI main de 1.798 testes
· **estável:** **BLOQUEADA** até homologação física.

Este documento complementa a seção [Roadmap consolidado](../README.md#roadmap-consolidado-e-auditoria-técnica--nexus-core)
e substitui afirmações antigas de CI como indicadores do **estado atual**.
Não renomeia o produto nem transfere interfaces de projetos externos.
O [inventário auditado dos ZIPs em 19/10](ZIP_CAPABILITY_GAP_2026-10-19.md)
detalha cada fonte, as funções implementadas depois da candidata rc.3 e as
lacunas. Este incremento de código **não altera** a tag rc.3 nem o gate G0.
O [quadro de recursos offline](OFFLINE_WORKBENCH_2026-10-19.md) detalha
notas, transformações de dados, medição local e as capacidades mais extensas
ainda não integradas. O teste de voz agora exige duas respostas faladas com
retomada da escuta, sem antecipar a homologação física.

## Balanço do ciclo

| Entrega | Estado verificável | Critério para próximo passo |
| --- | --- | --- |
| Núcleo local-first, Python, PostgreSQL, SecurityGate e auditoria | Código integrado/CI | Teste real de instalação, autorização e recuperação no Ubuntu |
| Conversação e motor local, memória e conhecimento explícitos | Código integrado/CI | Testes de latência, streaming e descarregamento do modelo em perfil eco |
| Interface desktop vinho, mensagens, atalhos, preview, controles de voz, vision e privacidade | Código integrado/CI | Conferir fonte, escala, layout Wayland/X11 e responsividade na máquina real |
| Áudio, Vosk, saída falada, escuta contínua | Código integrado; aceite físico **parcial** | Duas respostas consecutivas na janela, cancelamento e retomada após TTS |
| Captura de imagem/tela/câmera e análise autorizada | Código integrado; aceite físico **parcial** | Prévia correta, consentimento repetido, qualidade e tempo de análise |
| Criação/edição de fotos e resumo de luminosidade com Pillow e arquivos protegidos | Código integrado/CI | Verificar fidelidade, transparência e original intacto no notebook |
| Documentos e PDFs, conversão/metadados, extração, render, junção, giro e movimento de página | Código integrado; **CLIs opcionais não homologados** | Executáveis reais, versão/fonte/hashes, saídas em leitores independentes |
| Análise REA estrutural offline | Código integrado/CI | Corpus defensivo, relatórios/limites, ausência de execução dos alvos |
| REA profundo, OCR, geração generativa de imagens, edição de documento complexa | **Não implementado integralmente** | Arquitetura separada, isolamento, custo em RAM e novos gates específicos |
| CI da 0.9.12, tags rc.1/rc.2 e publicação rc.3 | **1.798 testes aprovados na main**; rc.3 publicada com wheel e SHA256SUMS | Candidata imutável e verificável; não é release estável |
| Aceite físico G0 para release estável | **11 PASSOU / 10 PENDENTE no relatório de 18/10** | Concluir e comprovar as dez etapas; nenhuma omissão equivale a sucesso |

## G0 — Bloqueio de publicação estável v0.9.12

**0. Preparação:** atualizar a main; capturar SHA, OS/Python, sessão gráfica,
perfil de recursos e estado dos serviços. Executar CI de push **no mesmo SHA
da release**. Não ativar Ollama/PostgreSQL na inicialização do sistema.

**1. Assistente na janela:** envio por teclado, respostas distintas para
perguntas distintas, histórico e cancelamento de operação pendente.

**2. Voz:** escuta contínua com duas trocas completas, pausa/retomada,
resposta falada compreensível, recuperação de transcrição falha e consentimento
falado sem autorização implícita.

**3. Visão:** câmera com prévia, foto explícita, tela sob autorização,
rejeição de nova captura negada e coerência da resposta; registrar tempos e
consumo de RAM/swap no perfil eco.

**4. Segurança:** negar/aceitar ações distintas, saída nova com permissões
privadas, arquivo original intacto, nenhuma leitura por symlink, fluxo de
cancelamento e reinicialização segura.

**5. Serviços:** teste separado com PostgreSQL/Ollama preexistentes e
com instâncias iniciadas pelo próprio Nexus; stop nunca deve desligar
dependências alheias, autostart não deve ser habilitado.

**6. CLIs externos:** identificar CLI e versões, conferir integridade das
instalações; executar somente após consentimento
`python3 scripts/validate_craft_cli.py --smoke --advanced`.
Binário ausente ou mock = **pendente**, não aprovado.

**7. Desktop Linux:** Wayland e X11 por capacidades realmente suportadas,
dimensões mínima e maximizada, teclado, escala, diálogo de autorização,
performance e logs sem dados privados.

**Critério final:** checklist assinado/registrado na documentação,
nenhuma falha crítica sem tratamento, CI verde em SHA exato, atualização
do README e notas estáveis, aprovação explícita da mudança que remove o
bloqueio do workflow `release-v0.9.12.yml`. Até lá a candidata é pré-release.

## Publicação no GitHub sem falsos positivos

A pré-release [`v0.9.12-rc.3`](https://github.com/ricardogomesbarreto/Nexus-Core/releases/tag/v0.9.12-rc.3)
**foi publicada em 18/10/2026**, no commit de código
`6429a5e61235588feb5c4eb46838c61793bf43ec`, após
[CI de 1.798 testes](https://github.com/ricardogomesbarreto/Nexus-Core/actions/runs/39126833572)
e [workflow de publicação verde](https://github.com/ricardogomesbarreto/Nexus-Core/actions/runs/39126956436).
Artefatos: `nexus_core-0.9.12-py3-none-any.whl` (959.084 bytes) e
`SHA256SUMS`. SHA-256 do wheel:
`0d6ec807c6d00fa8774c0e1caa0430b5a83f4c50a1b97356e9309ce0f1674125`.
O workflow é idempotente: após publicação, futuras atualizações de
`main` verificam que a candidata existe e **não reescrevem a tag**.

A publicação é **pré-release**, não muda `releases/latest` estável
(v0.7.2) e não desbloqueia o workflow `release-v0.9.12.yml`.
Somente o aceite físico completo poderá liberar a release estável.

## Roadmap pós-0.9.12

| Marco | Prioridade | Condição de entrada/saída |
| --- | --- | --- |
| G1 — Registro de adaptadores opcionais | Alta | Detecção de versão/capacidade; CLI real sob limites e consentimento |
| G2 — Imagem profissional NEXUS | Alta | Recorte, escala e camadas opcionais; prévia/resultado fiel, sem editor clonado |
| G3 — Documento estruturado | Alta | Estilos e tabelas/abertura cruzada com suíte independente; sem corrupção silenciosa |
| G4 — PDF expandido | Alta | Giro e movimento de uma página agora no adaptador; divisão em vários arquivos, formulários e OCR exigem parser e verificação externos |
| G5 — Engenharia reversa defensiva | Média | Binários autorizados; isolamento real, evidência reprodutível, sem runtime no host sem consentimento |
| G6 — Ollama/perfil eco | Alta | Modelo certo para RAM disponível, streaming, medição e cancelamento sem serviços fixos |
| G7 — UX/voz/visão e acessibilidade | Alta | Wayland/X11, microfone contínuo, câmera, estados, qualidade e tempo reais |
| G8 — Segurança/qualidade/distribuição | Contínua | Builds reproduzíveis, testes adversariais, licença/SBOM e outras distros por aceite |

Sem declarar “100% funcional” nem alterar a identidade vinho.
A ordem e o inventário aprofundado das funcionalidades permanecem no README.
