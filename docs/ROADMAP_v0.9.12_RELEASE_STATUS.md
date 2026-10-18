# NEXUS CORE — Fechamento de código 0.9.12 e roadmap de release

**Data da revisão:** 18/10/2026 · **Versão do pacote:** 0.9.12
· **candidata planejada:** v0.9.12-rc.3
· **estável:** **BLOQUEADA** até homologação física.

Este documento complementa a seção [Roadmap consolidado](../README.md#roadmap-consolidado-e-auditoria-técnica--nexus-core)
e substitui afirmações antigas de CI como indicadores do **estado atual**.
Não renomeia o produto nem transfere interfaces de projetos externos.

## Balanço do ciclo

| Entrega | Estado verificável | Critério para próximo passo |
| --- | --- | --- |
| Núcleo local-first, Python, PostgreSQL, SecurityGate e auditoria | Código integrado/CI | Teste real de instalação, autorização e recuperação no Ubuntu |
| Conversação e motor local, memória e conhecimento explícitos | Código integrado/CI | Testes de latência, streaming e descarregamento do modelo em perfil eco |
| Interface desktop vinho, mensagens, atalhos, preview, controles de voz, vision e privacidade | Código integrado/CI | Conferir fonte, escala, layout Wayland/X11 e responsividade na máquina real |
| Áudio, Vosk, saída falada, escuta contínua | Código integrado; aceite físico **parcial** | Duas respostas consecutivas na janela, cancelamento e retomada após TTS |
| Captura de imagem/tela/câmera e análise autorizada | Código integrado; aceite físico **parcial** | Prévia correta, consentimento repetido, qualidade e tempo de análise |
| Criação/edição de fotos com Pillow e arquivos protegidos | Código integrado/CI | Verificar fidelidade, transparência e original intacto no notebook |
| Documentos e PDFs, conversão/metadados, extração, render e junção de dois PDFs | Código integrado; **CLIs opcionais não homologados** | Executáveis reais, versão/fonte/hashes, saídas em leitores independentes |
| Análise REA estrutural offline | Código integrado/CI | Corpus defensivo, relatórios/limites, ausência de execução dos alvos |
| REA profundo, OCR, geração generativa de imagens, edição de documento complexa | **Não implementado integralmente** | Arquitetura separada, isolamento, custo em RAM e novos gates específicos |
| CI de 0.9.12 e tags históricas rc.1/rc.2 | Registradas no GitHub | Candidata rc.3 deve corresponder ao SHA da main aprovado na CI |
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

A pré-release `v0.9.12-rc.3` tem workflow independente
`.github/workflows/release-candidate-v0.9.12.yml`: após CI de push
verde no SHA atual da `main` com versão 0.9.12, constrói wheel
e publica tag anotada imutável + `SHA256SUMS` como **prerelease**.
Não muda `releases/latest` estável e não desbloqueia
`release-v0.9.12.yml`. Consulte a página GitHub Releases para
confirmar a existência real: uma PR aprovada não equivale à publicação.
Se o workflow falhar, registrar a falha; não editar tags já criadas.

## Roadmap pós-0.9.12

| Marco | Prioridade | Condição de entrada/saída |
| --- | --- | --- |
| G1 — Registro de adaptadores opcionais | Alta | Detecção de versão/capacidade; CLI real sob limites e consentimento |
| G2 — Imagem profissional NEXUS | Alta | Recorte, escala e camadas opcionais; prévia/resultado fiel, sem editor clonado |
| G3 — Documento estruturado | Alta | Estilos e tabelas/abertura cruzada com suíte independente; sem corrupção silenciosa |
| G4 — PDF expandido | Alta | Rotação, separação, formulários e OCR somente com parser e verificação externos |
| G5 — Engenharia reversa defensiva | Média | Binários autorizados; isolamento real, evidência reprodutível, sem runtime no host sem consentimento |
| G6 — Ollama/perfil eco | Alta | Modelo certo para RAM disponível, streaming, medição e cancelamento sem serviços fixos |
| G7 — UX/voz/visão e acessibilidade | Alta | Wayland/X11, microfone contínuo, câmera, estados, qualidade e tempo reais |
| G8 — Segurança/qualidade/distribuição | Contínua | Builds reproduzíveis, testes adversariais, licença/SBOM e outras distros por aceite |

Sem declarar “100% funcional” nem alterar a identidade vinho.
A ordem e o inventário aprofundado das funcionalidades permanecem no README.
