# Nexus Core 0.9.15 — controle de memória no perfil eco

Versão de código para validação. PostgreSQL permanece o único banco; Ollama,
voz e visão continuam locais. Não foi criada tag estável nem alterado o gate
de aceite físico da v0.9.12.

## Entrega

- Antes de carregar o modelo de conversa em perfil `eco`, a memória
  disponível é medida novamente. Com menos de 1 GiB, a solicitação recebe
  uma explicação acionável; nenhuma requisição de inferência é iniciada.
- Antes de codificar/enviar a imagem, a visão lê o tamanho em disco do modelo
  instalado pelo endpoint local `/api/tags` do Ollama e compara com a memória
  disponível, mantendo 512 MiB de margem. Sob menos de 1 GiB, bloqueia mesmo
  sem metadados. Outros aplicativos e modelos carregados não são desligados.
- A normalização de arquivo, tela e foto da webcam usa diretamente o limite
  visual do perfil. No `eco`, o intermediário passa de até 1536 px para até
  768 px. A conversão final ainda ocorre, para sanitizar toda imagem antes
  do envio. A amostra de imagem escura é reduzida antes da conversão para
  tons de cinza.

Em cinco processos isolados por caminho, uma foto JPEG sintética de
2500×1900 pixels (~3,0 MB) apresentou mediana de pico RSS de **77.424 KiB**
na sequência 1536→768 px e **35.824 KiB** na sequência direta 768→768 px
neste ambiente. A medição inclui a importação Python e o Pillow, mas não
inclui Ollama, Tk, Vosk ou hardware do notebook. A entrada sintética não
representa todas as imagens reais.

## Limites

O tamanho do arquivo do modelo não prevê exatamente RAM/VRAM de inferência.
O teste protege contra cenários evidentemente insuficientes, mas não garante
ausência de swap, travamento ou aquecimento. Modelos já carregados também são
bloqueados sob pressão crítica; liberar memória e tentar novamente é o caminho
mais seguro. Alterar para `balanced` contorna esses limites e requer que o
operador confira os recursos. Nenhum download ou substituição de modelo é
automático. O Ollama já executando uma inferência ainda não é interrompido
imediatamente ao cancelar.

## Aceite no Ubuntu

Executar `--resource-check`, `free -h` e `ollama ps` antes, durante e após
uma pergunta textual e uma captura autorizada; testar com aplicativos abertos
e fechados. Registrar latência, RAM/swap e resposta audível. Observar que
uma recusa por pressão de memória apareça na janela e seja falada quando a
voz estiver habilitada. As verificações automatizadas simulam as fronteiras
de memória; não representam o notebook Asus com 6,5 GiB e Ubuntu Wayland.

Referência de contrato: [API local de modelos do Ollama](https://docs.ollama.com/api/tags).
