# Nexus Core 0.9.13 — código integrado: memória do desktop

Esta é uma versão **de código integrada à main**, sem
tag/release estável nem homologação do Ubuntu físico. O aceite físico e o publicador estável da
0.9.12 continuam pendentes; não alterar as tags candidatas existentes.

## Entrega verificável

- O histórico **visível** no widget Tk fica limitado a 32.000 caracteres.
  Mensagens antigas saem somente da janela, preferencialmente por parágrafos;
  contexto curto do modelo e arquivo de conversas opt-in seguem suas regras.
- A preparação de JPEG para a visão local solicita decodificação em resolução
  reduzida ao Pillow antes da conversão para RGB; outros formatos são
  redimensionados antes da conversão. Mantêm-se formato, dimensão original
  validada, orientação EXIF, descarte de metadados e limites da saída.
- O perfil `eco` permanece com `keep_alive: "0s"` por requisição ao Ollama.
  A mudança acima reduz alocações do processo Nexus; não modifica tamanho,
  desempenho ou uso de memória do modelo Ollama durante a inferência.

## Medição local reproduzível, não física

Para uma imagem JPEG sintética uniforme de 3000×2400 pixels reduzida a
768 pixels, cinco novos processos Python por versão apresentaram mediana
`ru_maxrss` de **103.412 KiB antes** e **38.492 KiB depois** neste ambiente.
Isso não representa pico total do desktop, consumo de câmera real, Ollama,
temperatura ou latência no notebook Ubuntu. A comparação depende do Pillow,
do sistema e da imagem usada.

## Portas de validação

Rodar CI do SHA final e repetir no Ubuntu 26.04 com o perfil `eco`:
`--resource-check` antes/depois de perguntas, captura de câmera e análise
visual; conferir `ollama ps`, duas falas e resposta audível, permissões e
encerramento sem processos restantes. O teste de limite do widget Tk exige
um display virtual na CI. Sem esses registros, nenhuma tag estável.

O encadeamento de tarefas proposto anteriormente para a 0.9.13 **não foi
implementado** nesta entrega; cada turno continua limitado a uma ação
sob autorização.
