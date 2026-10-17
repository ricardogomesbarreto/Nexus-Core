# Nexus Core v0.9.12 — Authorized Desktop Actions

**Estado: melhorias integradas à `main` pelo PR #66 (`bb7e487`); CI do PR
aprovada com 1.619 testes, sem tag/release estável.** O aceite físico no
notebook e a CI `push` do SHA final ainda são requisitos para publicação.

Ao executar `nexus-core --desktop` no terminal, eventos `TESTE-LOCAL`
registram ao vivo estados e duração de chat, escuta, fala, câmera, visão e
permissões sem imprimir conteúdo privado ou produzir log por quadro.

O comando `nexus-core --acceptance-log` reúne verificações locais e perguntas
de observação física em uma saída resumida para compartilhar, sem imprimir
credenciais, transcrição ou imagens. Uso de microfone e câmera pede consentimento
separado; as observações manuais não são aprovação automática de release.

## Entregas no código

- A frase exata “Crie uma pasta chamada Projetos” e nomes simples semelhantes
  escolhem uma pasta filha da home sem esperar o modelo local. A ação ainda passa
  pelo contrato de ferramenta, `SecurityGate`, prévia do caminho, confirmação
  individual e auditoria. Nenhuma frase de consentimento é inferida pelo modelo.
- Abrir o navegador padrão por comando exato em X11/Wayland dispensa
  confirmação adicional e não recebe URL; o gerenciador de arquivos e o
  terminal continuam a exigir confirmação. Frases ambíguas não abrem apps.
- A prévia da câmera oferece **Tentar novamente**, com autorização por nova
  foto. Entradas com sinal contínuo e sem palavras do Vosk encerram a tentativa
  após oito segundos; a qualidade de voz exige teste no equipamento real.
- A pergunta falada da janela de autorização respeita a escuta pausada e
  orienta responder por botão ou texto nesse estado.
- O workflow de publicação manual v0.9.11 usa o SHA do evento correto e exige
  uma CI `push` bem-sucedida para o commit exato da `main`. A mesma proteção
  prepara o workflow v0.9.12. Ambos continuam bloqueados por `if: false`.

## Limites e aceite

O comando de pasta aceita apenas uma filha imediata da home e não interpreta
caminhos arbitrários. A fala pode transcrever um nome diferente; conferir o
alvo mostrado antes de aprovar é obrigatório. Digitação e navegação em janelas
de terceiros continuam restritas a X11; não existe controle de teclado
Wayland homologado. Abrir um aplicativo confirma somente a solicitação de
abertura, não o comportamento posterior do aplicativo.

O [roteiro de aceite físico](UBUNTU_PHYSICAL_ACCEPTANCE_v0.9.12.md) começa
pendente. CI, Xvfb e mocks não comprovam inferência Ollama, áudio, webcam,
automação X11 nem recuperação no notebook do usuário. Nenhuma tag v0.9.12
deve ser criada sem registrar esses resultados, obter CI no SHA final da
`main` e revisar expressamente o bloqueio do workflow de release.
