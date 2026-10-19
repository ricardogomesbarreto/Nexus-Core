# Compatibilidade dos recursos offline consultados — 19/10/2026

Esta avaliação distingue **licença do código** de **licença do conteúdo**.
O Nexus Core é um aplicativo desktop local, com dados persistentes no
PostgreSQL. A instalação não inicia servidores web ou contêineres adicionais.
As fontes abaixo são os repositórios e documentos oficiais dos respectivos
projetos; a aprovação de software não autoriza redistribuir acervos, cursos
ou mapas de terceiros.

| Referência | Código e licença verificados | Decisão no Nexus Core |
| --- | --- | --- |
| Kiwix/kiwix-tools e openZIM | [Ferramentas GPL-3.0](https://github.com/kiwix/kiwix-tools), leitor Python [GPL-3.0 ou posterior](https://github.com/openzim/python-libzim) | Arquivos ZIM não estão integrados: o serviço HTTP contraria a interface nativa; ligação direta exige revisão de redistribuição e testes de leitura/segurança. Conteúdo de cada ZIM possui licença própria. Não instalar como requisito. |
| Kolibri | [MIT](https://github.com/learningequality/kolibri) | Plataforma completa de ensino com serviço, contas e gestão própria. Não instalar no assistente pessoal nem anunciar cursos e progresso que ele não implementa. |
| Protomaps/PMTiles | [BSD-3-Clause no leitor e ferramentas; especificação CC0/domínio público](https://github.com/protomaps/PMTiles/blob/main/LICENSE) | **Adaptador opcional implementado.** O leitor Python 3.8.1 foi baixado do código oficial e testado isoladamente; o instalador inclui `maps` no ambiente virtual. A janela nativa lê um mosaico raster PNG/JPEG/WebP de arquivo `.pmtiles` escolhido no diretório pessoal. Não busca ou baixa mapas. Cada pacote de dados tem licença/créditos próprios. |
| CyberChef | [Apache-2.0](https://github.com/gchq/CyberChef) | Aplicativo web/Node; não instalado. O Nexus tem operações textuais próprias e limitadas; não afirma equivalência às centenas de receitas do outro produto. |
| flatnotes | [MIT](https://github.com/dullage/flatnotes) | Aplicativo web com arquivos Markdown como armazenamento. Não instalado: notas nativas já existem no PostgreSQL; formatos e exportação exigem etapa própria. |
| Benchmark “Built-in” | Função interna da referência, sem pacote independente | Medição limitada de CPU e RAM já existe no Nexus. Pontuação comparável e ranking comunitário não existem. |
| Catálogo “Built-in” | Função interna da referência, sem pacote independente | Nenhuma biblioteca a baixar. Instalação de terceiros e orquestração de contêineres não foram adicionadas. |

## Entrega incremental

No menu **Recursos → Mapas locais…**, o usuário escolhe um arquivo raster
próprio. A prévia mostra um mosaico por vez e oferece navegação horizontal,
vertical e zoom nos níveis presentes no arquivo. O Nexus mantém o descritor
aberto com proteção contra links simbólicos e lê o arquivo em processo separado
com limite de tempo e memória. Há limites de 20 GiB para o arquivo (leitura
pontual, sem cópia integral), 2 MiB por bloco, 4 milhões de pixels por
imagem e 8 segundos por consulta. Os dados não entram no PostgreSQL nem no
contexto do Ollama; créditos fornecidos pelo mapa aparecem na prévia.

Arquivos vetoriais, outros formatos, geocodificação, busca por locais,
licença do conteúdo, continuidade entre mosaicos e operação física no
Ubuntu/Wayland permanecem **pendentes**. Esta prévia não é um navegador
cartográfico completo. O pacote do usuário não continha dados de mapas.
`pip install -e '.[maps,vision]'` no ambiente virtual de desenvolvimento
instala as dependências opcionais; o instalador Ubuntu inclui o leitor de
mapas, mas o conteúdo `.pmtiles` é sempre fornecido pelo usuário.

O código desta etapa é complementar à candidata v0.9.12. Ela **não** publica
release ou tag estável nem conclui o gate físico G0 do roadmap.
