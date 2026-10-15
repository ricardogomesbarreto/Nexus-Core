# NEXUS CORE v0.9.9 — Spoken Desktop Controls

## Entrega

- Frases completas em português solicitam análise de **imagem**, **tela** ou **câmera** na janela desktop. O reconhecimento local abre o mesmo fluxo já usado pelos botões e atalhos: seleção, pergunta e consentimento explícito para uma única análise. Recusa ou cancelamento não captura nem envia imagem e retoma a escuta se ela estiver habilitada.
- **"Desative a voz"** e **"Ative a voz"** alteram somente a saída falada. O desligamento responde por texto; a ativação confirma também por voz. As frases são tratadas localmente, sem chamada ao agente ou execução de ferramentas.
- O modo opcional de frase de ativação continua valendo: com ele ligado, o usuário precisa iniciar o pedido por **"Nexus"**. Testes Tk em Xvfb verificam frases aceitas/rejeitadas, as três fontes sem consentimento, seleção cancelada, captura autorizada única e alternância de voz.
- Correção de instalação: sem uma credencial PostgreSQL privada válida ou `NEXUS_DATABASE_PASSWORD` informado pelo usuário, uma recusa/falha de provisionamento encerra a instalação antes de criar o ambiente gerenciado e o launcher; não exibe mais sucesso falso. Um arquivo privado com JSON inválido também deixa de ser aceito. Testes cobrem recusa, configuração manual e provisionamento simulado.

## Limites

Com escuta pausada, comandos de voz não são recebidos; retome pelo botão ou `Ctrl+Shift+M`. Durante reprodução de áudio e operações em andamento, o reconhecimento fica suspenso para evitar eco e concorrência; use os atalhos e controles da janela. A escolha da imagem/pergunta e a autorização visual continuam na interface Tk, não são aprovações faladas. Os testes simulam dispositivos e não homologam microfone, câmera, áudio, Ollama multimodal ou teclado físico no Ubuntu Desktop 24.04 LTS.
O instalador verifica a disponibilidade de uma senha com formato válido, mas não comprova a autenticação dessa senha no banco durante o bootstrap; use o preflight e os testes reais na máquina alvo.

## Integração e publicação

Código integrado à `main` em ordem pelos PRs #15–#31 (v0.8.3–v0.9.9). A última release oficial continua v0.7.2. O workflow de release v0.9.9 permanece desabilitado; CI no SHA final da `main`, aceite físico registrado e revisão específica do workflow precedem tag/release estável.
