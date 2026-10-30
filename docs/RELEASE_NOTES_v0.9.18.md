# Nexus Core 0.9.18 — estudo local e prévia de voz

## Código

- Biblioteca PostgreSQL: criação voluntária de cartão para o primeiro trecho
  de uma busca, com pergunta e resposta fornecidas pelo usuário. O banco
  verifica a existência da resposta no trecho no instante do salvamento.
- Revisão local: resposta escondida até pedido explícito; acerto move a
  próxima revisão para 1/3/7/14 dias, erro para 10 minutos. A exclusão de um
  documento elimina seus cartões por chave estrangeira. Não há servidor,
  sincronização externa nem modelo adicional de estudo.
- Painel de testes: amostra curta da voz selecionada, com escuta interrompida
  durante a reprodução e retomada pelo fluxo existente. Não é clonagem de voz.

## Restrições e validação

O estudo depende da biblioteca textual já importada pelo usuário e do login
PostgreSQL local. A resposta é literal, não uma avaliação semântica. A
interface, o desempenho e a voz física no Ubuntu 26.04/Wayland continuam
pendentes de aceite. Testes automatizados/CI não comprovam webcam, alto-falante
ou consumo de RAM no notebook. A v0.9.12-rc.3 permanece candidata imutável;
nenhuma tag estável 0.9.x é publicada por esta mudança.

O [inventário das fontes anexadas](ZIP_INTEGRATION_v0.9.18.md) registra
funções próximas e o que não é adequado à instalação leve atual.
