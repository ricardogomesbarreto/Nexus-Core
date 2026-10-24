# Nexus Core 0.9.14 — estabilidade da câmera e do cancelamento visual

Versão de código em desenvolvimento. A publicação estável depende da CI do
commit final e dos testes físicos documentados no roteiro da v0.9.12.

## Correções

- A webcam não publica um quadro lido depois de `stop()`. `latest()` deixa de
  entregar a imagem quando o stream está encerrado, mesmo se o worker do
  FFmpeg ainda não terminou. Um teste reproduz o atraso entre leitura e parada.
- Uma captura de tela, arquivo ou câmera que termina após o pedido de cancelar
  não enfileira prévia nem inicia a descrição pelo modelo. A análise de quadro
  ao vivo verifica o cancelamento antes de iniciar a inferência.
- Nenhuma dessas alterações inicia a câmera sem a autorização já exigida.

## Limites e verificação

Uma inferência Ollama que começou antes do cancelamento pode continuar até o
timeout do transporte. A interface descarta sua resposta cancelada; medir o
consumo real e a latência no notebook continua necessário. No Ubuntu, testar
uma captura, cancelar durante a seleção/captura e desligar o vídeo ao vivo
durante a atualização. Depois executar `--resource-check` e confirmar que a
prévia não reaparece e que o indicador de câmera fica desligado.

O pacote mantém PostgreSQL local como banco único, Ollama local e o perfil
`eco`. Não há mudança de compatibilidade declarada ou tag estável nesta etapa.
