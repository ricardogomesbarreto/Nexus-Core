# Nexus Core 0.9.14 — estabilidade da câmera e do cancelamento visual

Versão de código integrada à `main`. A publicação estável depende da CI do
commit final e dos testes físicos documentados no roteiro da v0.9.12.

## Correções

- A webcam não publica um quadro lido depois de `stop()`. `latest()` deixa de
  entregar a imagem quando o stream está encerrado, mesmo se o worker do
  FFmpeg ainda não terminou. Um teste reproduz o atraso entre leitura e parada.
- Uma captura de tela, arquivo ou câmera que termina após o pedido de cancelar
  não enfileira prévia nem inicia a descrição pelo modelo. A análise de quadro
  ao vivo verifica o cancelamento antes de iniciar a inferência.
- O motor visual verifica o cancelamento antes da consulta do modelo, depois
  da consulta, depois da normalização da imagem e antes do POST local. Isso
  evita codificar e enviar uma imagem quando o usuário cancelou nesse intervalo.
- Nenhuma dessas alterações inicia a câmera sem a autorização já exigida.

## Limites e verificação

Uma inferência Ollama que começou antes do cancelamento pode continuar até o
timeout do transporte. A interface descarta sua resposta cancelada; medir o
consumo real e a latência no notebook continua necessário. No Ubuntu, testar
uma captura, cancelar durante a seleção/captura e desligar o vídeo ao vivo
durante a atualização. Depois executar `--resource-check` e confirmar que a
prévia não reaparece e que o indicador de câmera fica desligado.

O pacote mantém PostgreSQL local como banco único, Ollama local e o perfil
`eco`. A [CI da PR #95](https://github.com/ricardogomesbarreto/Nexus-Core/actions/runs/40100346524)
passou; o workflow de push da `main` no SHA final e o aceite físico continuam
necessários para a tag estável. Não há mudança de compatibilidade declarada.
