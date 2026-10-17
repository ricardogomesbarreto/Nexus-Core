# Diretrizes do Nexus Core

## Objetivo

Assistente pessoal gratuito e open source para desktop Linux, com conversa
natural em português, execução local com Ollama, voz e visão mediante escolha
do usuário, e PostgreSQL como banco de dados principal e único. A referência
de experiência é um assistente capaz de conversar, observar sob autorização
e ajudar em tarefas reais no computador. O comportamento publicado deve
corresponder ao código e à homologação, sem prometer recursos de ficção.

## Ambiente de segurança e hacking autorizado

O Nexus Core também é um ambiente para estudo de segurança, CTFs,
laboratórios, análise defensiva, auditoria e testes de invasão **em sistemas
próprios ou com autorização do responsável**. O usuário deve definir o escopo
de cada trabalho (alvos, janela de tempo, técnicas e limites) antes de
iniciar qualquer teste que interaja com outra máquina ou serviço.

- A assistência pode explicar técnicas, organizar evidências locais e propor
  ações. Cada execução potencialmente sensível passa por contrato de
  ferramenta, `SecurityGate`, confirmação individual e registro de auditoria.
- Comandos de laboratório executáveis usam isolamento e limites explícitos;
  não se concede shell irrestrito do host ao modelo. Uma recusa, falha de
  autorização ou cancelamento deve encerrar a ação pendente.
- Captura de câmera, tela, áudio, leitura de arquivos e tráfego de rede são
  recursos distintos. Abrir um aplicativo ou autorizar uma fotografia não
  autoriza automaticamente acesso aos demais recursos.
- A decisão sobre cada permissão pode ser dada pelos botões, digitada na
  janela de confirmação ou falada com frase explícita; transcrição incerta,
  escuta pausada e silêncio não concedem autorização.
- Ferramentas de reconhecimento de rede e pentest exigem uma implementação
  futura que valide o escopo autorizado. A existência de Docker ou de uma
  sessão de terminal **não significa** que varreduras de rede ou exploração
  automática já estejam disponíveis.
- O assistente deve mostrar alvo e efeito esperado antes de operações que
  alteram o sistema ou enviam tráfego; deve permitir parar a atividade e
  distinguir resultados observados de hipóteses do modelo.

## Consumo, inicialização e programas locais opcionais

- Nenhum instalador, rotina de primeiro uso ou atualização deve
  executar `systemctl enable` ou `systemctl --user enable` para
  serviços PostgreSQL, Ollama ou outras dependências sem uma ação
  específica e inequívoca solicitada pelo usuário. No perfil NEXUS,
  Ollama e PostgreSQL devem iniciar **sob demanda** e liberar recursos
  quando a sessão terminar, desde que nenhum outro aplicativo dependa
  deles. Não modificar ou parar serviços de terceiros silenciosamente.
- Ubuntu/Debian são a prioridade de instalação e testes físicos;
  outras distribuições Linux são alvos de compatibilidade progressiva,
  sem declarar funcionamento universal com base apenas em testes Xvfb.
- Ferramentas opcionais do sistema executadas por subprocesso **não**
  são automaticamente sandbox. Antes de invocar programas externos,
  confirmar o alvo, limitar argumentos, tempo e tamanho dos arquivos,
  validar entradas e saídas, e impedir leitura de links simbólicos.
  A autorização do usuário permite a ação; não transforma executáveis
  instalados por terceiros em programas seguros ou sem rede.
- Conversas arquivadas são texto local legível pela conta Linux e
  podem conter informações fornecidas pelo próprio usuário. Não
  prometer filtragem integral de segredos ou criptografia automática.
- Uma release não deve ser publicada apenas por `pytest`: exigir CI
  real no SHA da `main` e aceite em hardware físico para áudio,
  câmera, visão, consumo de recursos, atualização e permissões.

## Requisitos de experiência e critérios de aceite

| Requisito | Critério observável |
| --- | --- |
| Conversa | Cada pergunta recebe resposta pertinente, erro claro ou cancelamento; o chat não reutiliza uma resposta anterior para uma pergunta diferente. |
| Voz | Escuta contínua com pausa/retomada, feedback do microfone e resposta feminina ou masculina; comando e teclado seguem as mesmas permissões. |
| Visão | Câmera mostra prévia contínua e permite foto; tela e janela são selecionadas pelo usuário; distinguir prévia de inferência visual contínua. |
| Ações | Pastas e aplicativos são operações de escopo pequeno, auditadas e confirmadas; tarefas compostas preservam confirmação por etapa. |
| Privacidade | Modelos locais por padrão, dados e preferências protegidos no disco local, nenhuma captura implícita. |
| Compatibilidade | Ubuntu Desktop compatível com Python, PostgreSQL, áudio e componentes necessários, incluindo Wayland; homologar hardware físico antes de anunciar suporte completo. |

Este documento define direção do produto. O [README](../README.md) registra
o estado efetivo; lacunas são descritas como pendentes até implementação e
validação física.
