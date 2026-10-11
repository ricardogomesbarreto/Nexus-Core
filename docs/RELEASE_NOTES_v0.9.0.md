# NEXUS CORE v0.9.0 — Multimodal Privacy & Accessibility Status

## Objetivo e aderência ao roadmap

**Início da linha v0.9.x — Multimodal Interface**, prevista no README. Esta versão faz um incremento funcional **conservador** na janela Tk já existente: apresenta ao usuário estados textuais de escuta, saída por voz e análise de imagem/tela/câmera, e oferece um atalho acessível por teclado para pausar ou retomar a escuta. Não altera a marca Nexus Line, cor `#722F37`, hierarquia dos controles, arquitetura local ou consentimento individual.

O NEXUS CORE permanece **desktop Linux, gratuito/open source, PostgreSQL local, Ollama local**, com Ubuntu Desktop 24.04 LTS como primeiro alvo de instalação e validação física.

## Implementação

- Novo `nexus/desktop/multimodal_status.py`: estado imutável e função determinística para três descrições curtas; biblioteca padrão, sem acesso à câmera, microfone, rede, PostgreSQL, arquivo do usuário ou Tk.
- O painel Tk apresenta **Escuta**, **Voz** e **Visão** logo após os controles visuais, sem ícones novos ou necessidade de serviço externo. Textos utilizam cores e tipografia já definidas pela janela.
- Escuta: `pausada` quando desabilitada; `aguardando` quando habilitada mas não há reconhecimento em curso; `solicitada` quando a tarefa de reconhecimento foi iniciada (sem alegar que o hardware esteja efetivamente capturando).
- Saída por voz: `desativada`, `habilitada` ou `saída solicitada`. Assim a interface **não afirma áudio efetivamente audível** antes do resultado real do eSpeak NG.
- Visão: `sem captura` por padrão; só mostra `processando imagem/tela/câmera` **depois da autorização específica de uma análise**; `cancelamento solicitado` durante a interrupção, sem alegar falsamente que uma operação externa terminou. Não expõe nomes de arquivos nem imagens.
- Estados `encerrando` na fase de desligamento. Atualização dos rótulos ocorre no loop Tk, não nas threads de áudio/visão, com renderização somente se o conteúdo mudou.
- Atalho `Ctrl+Shift+M` chama a **mesma ação** do botão `Pausar escuta / Retomar escuta`. Não libera câmera, visão, shell, digitação X11, automações ou ferramentas do Agent. Uma nova permissão visual continua sendo necessária em cada solicitação.

## Testes

- Testes unitários da máquina de apresentação em estados de voz, visão, cancelamento, encerramento e fontes visuais inválidas.
- Testes Tk no display virtual da CI: rótulos presentes antes de qualquer captura, atalho de microfone com impacto somente na escuta, recusa de consentimento sem captura, e análise autorizada bloqueada até confirmação do estado visual/cancelamento. São usados apenas fakes de áudio, câmera, modelo e Agent; nenhuma imagem real sai do computador.
- A suíte completa de regressão anterior, com Ubuntu 24.04, Python 3.12, PostgreSQL 16, Docker e Xvfb, permanece obrigatória no commit final.

## Limites e riscos reais

Os rótulos retratam **estado de software**, não são atestados físicos de microfone, alto-falantes ou câmera. A interface Tk pode oferecer acesso textual e por teclado, mas não constitui homologação de leitores de tela, tecnologias assistivas, contraste ou WCAG sem testes de acessibilidade com hardware e usuários reais. A escuta contínua existente não é alterada; quem quiser pausar deve usar botão, atalho ou comando de voz já autorizado.

Cancelamento de visão é uma solicitação *best effort*: não desfaz capturas já realizadas e não garante interromper instantaneamente um backend em andamento. O indicador utiliza `cancelamento solicitado` precisamente por esse motivo. O módulo não registra áudio/imagens nem transmite telemetria e não amplia poderes do assistente. Nenhuma tag estável deve ser publicada com base apenas em Xvfb.

## Dependências e publicação

A v0.9.0 é empilhada sobre o **PR #21 (v0.8.9)**; os PRs #15–#20 também exigem integração ordenada. `main` permanece com código até v0.8.2; última release pública verificada **v0.7.2**. Workflow `.github/workflows/release-v0.9.0.yml` seguirá com execução manual e **`if: ${{ false }}`** para impedir publicação até a homologação física Ubuntu, voz, visão, X11, Ollama, PostgreSQL, instalação e recuperação, além de CI exata do SHA da `main`.

Próximos incrementos v0.9.x devem evoluir testes de acessibilidade e diagnóstico de interfaces/dispositivos **sem alterar design aprovado ou relaxar consentimentos**.
