# Aceite físico Ubuntu — Nexus Core v0.9.12

**Estado em 17/10/2026: PENDENTE.** Este documento é um roteiro de execução
no notebook do usuário. Nenhuma etapa abaixo está marcada como aprovada pela
CI nem pelos testes simulados. Registre data, versão, SHA, sessão gráfica,
resultado observado e eventuais falhas antes de propor uma tag.

**Evidência histórica informada pelo usuário, ainda não aceite da v0.9.12:**
Ubuntu 26.04.1, Python 3.14.4 e Wayland; o teste de microfone da linha 0.9.11
registrou sinal PipeWire, o diagnóstico reconheceu um modelo Vosk instalado,
e uma pergunta isolada pelo Ollama recebeu uma resposta curta. Houve relatos
posteriores de problemas de câmera, latência e escuta contínua. Esses testes
não foram repetidos nesta versão e não comprovam o funcionamento conjunto.

## Identificação e instalação

No terminal do Ubuntu do usuário:

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main
git pull --ff-only
git rev-parse HEAD
grep '^version = ' pyproject.toml
python3 --version
echo "$XDG_SESSION_TYPE"
python3 scripts/install_linux.py --check
python3 scripts/install_linux.py
~/.local/bin/nexus-core --version
~/.local/bin/nexus-core --ubuntu-preflight | python3 -m json.tool
~/.local/bin/nexus-core-recover --status
```

O instalador pode pedir autorização para pacotes oficiais, modelos, usuário
PostgreSQL e configuração de atualização. Revise cada pedido. O resultado
esperado da versão é `Nexus Core 0.9.12`; o preflight deve indicar login
PostgreSQL autenticado. Não copie senhas, tokens nem caminhos privados para
issues ou PRs. O comando de recuperação acima apenas consulta o status:
**não execute rollback em uma instalação de uso real para homologar**.

## Conversa, áudio e câmera

```bash
~/.local/bin/nexus-core --agent-prompt 'Responda em uma frase: você está funcionando?'
~/.local/bin/nexus-core --microphone-test | python3 -m json.tool
~/.local/bin/nexus-core --recognition-test | python3 -m json.tool
~/.local/bin/nexus-core --camera-list | python3 -m json.tool
~/.local/bin/nexus-core --camera-test 0 | python3 -m json.tool
~/.local/bin/nexus-core --desktop
```

O índice `0` é apenas exemplo; use o índice retornado por `--camera-list`.
Confirme que a resposta do Ollama é nova e pertinente, que o teste físico
transcreve uma frase falada, que as vozes feminina e masculina são audíveis,
e que a prévia da webcam exibe imagem. Com a câmera aberta, faça uma pergunta
visual autorizada e compare a resposta ao quadro visto; a prévia não equivale
a inferência contínua de todos os quadros.

## Ações e permissões

Na janela, digite ou fale **“Crie uma pasta chamada NexusAceite”**. Confira o
caminho completo na autorização falada e visual. Primeiro **Negar**: a pasta
não deve existir. Faça um segundo pedido e autorize por botão ou pela frase
exata **“Nexus, autorizo esta ação”**: deve aparecer uma única pasta na sua
home. Confira a trilha de auditoria e remova a pasta depois do teste.

Repita com **“Abra o navegador”** e escolha Negar antes de permitir uma
segunda chamada. A janela precisa mostrar a ação e aceitar também a decisão
digitada. Suspenda a escuta e confira que a fala de autorização não instrui
o uso do microfone pausado. Em Wayland, **não marque navegação/digitação
em outras janelas como aprovada**: a implementação atual exige X11. Se desejar
testá-la em sessão X11 local, use separadamente
`python3 -m scripts.x11_manual_acceptance`, que cria uma janela temporária e pede
consentimento por operação.

## Registro de evidências

Preencha esta tabela somente com observações reais. Use `PENDENTE`,
`APROVADO`, `FALHOU` ou `NÃO APLICÁVEL`; anexe resumo de comandos sem segredos
e descreva qualquer erro reproduzível.

| Critério | Resultado | Evidência resumida |
| --- | --- | --- |
| SHA da main, Ubuntu/Python/sessão registrados | PENDENTE | — |
| Instalação, login PostgreSQL e status de recuperação | PENDENTE | — |
| Resposta pertinente do Ollama sem internet externa | PENDENTE | — |
| Microfone e transcrição Vosk de fala real | PENDENTE | — |
| Voz feminina e masculina audíveis, pausa e retomada | PENDENTE | — |
| Webcam, foto e descrição coerente após consentimento | PENDENTE | — |
| Criar pasta: negação e autorização individuais | PENDENTE | — |
| Abrir aplicativo: negação e autorização individuais | PENDENTE | — |
| Permissão falada, digitada e por botão; cancelamento | PENDENTE | — |
| Navegação/digitação em janela X11 temporária | PENDENTE | — |
| CI de `push` para o SHA final da main | PENDENTE | — |

**Decisão de release: PENDENTE.** Registre qualquer falha como falha; CI verde
não altera esta decisão automaticamente. Recuperação por reversão real e
atualização gerenciada devem ser ensaiadas somente em uma instalação
descartável com backup e plano de restauração, nunca inferidas pelo `--status`.
