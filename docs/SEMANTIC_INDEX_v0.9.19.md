# Índice semântico local — v0.9.19.dev0 (Draft)

O banco do assistente continua sendo somente PostgreSQL. O índice é
**opcional**: importar um texto `.txt` ou `.md` não chama Ollama nem cria
embeddings. O usuário escolhe o documento na Biblioteca, abre o menu
**Índice semântico** e confirma a indexação. A interface também oferece
**Pesquisar no índice** e **Remover índice do documento**.

O modelo de embeddings precisa estar **previamente instalado** no Ollama
local, ter no máximo 900 MiB e passar no teste de memória disponível. Cada
indexação envia ao serviço local até 16 trechos iniciais de 1.000 caracteres,
em uma única solicitação. A resposta e os vetores são limitados em tamanho;
o modelo é descarregado após a chamada (`keep_alive=0`). A transação grava
no máximo 16 vetores por ação e mantém o índice global em até 256 linhas.
Cada vetor está ligado ao trecho e é excluído quando o documento é apagado.

Comandos no terminal, depois de iniciar o PostgreSQL e o Ollama local:

~~~bash
~/.local/bin/nexus-core --knowledge-list
ollama list
~/.local/bin/nexus-core --knowledge-index ID_DO_DOCUMENTO --embedding-model NOME_EXATO
~/.local/bin/nexus-core --knowledge-semantic-search 'pergunta' --embedding-model NOME_EXATO
~/.local/bin/nexus-core --knowledge-index-delete ID_DO_DOCUMENTO
~~~

O último comando remove os vetores, preservando o texto. A consulta verifica
se o modelo já possui vetores indexados **antes** de carregar o Ollama. O
índice não instala modelos, não consulta outra máquina e não transmite os
documentos à internet. Cada pesquisa lê no máximo 256 linhas PostgreSQL e
retorna até cinco fontes. Trocar o modelo não reaproveita vetores de outro
modelo; reindexe explicitamente quando necessário. O limite de 256 entradas
protege o perfil `eco`, mas não cobre uma biblioteca arbitrariamente grande.

Aceite físico pendente: importar dois textos reais, indexar ambos, pesquisar
uma frase sem coincidência literal, conferir pertinência e fonte, medir RAM,
swap e tempo, remover um índice, excluir o outro documento e comprovar que
os vetores não reaparecem. Nenhum resultado automatizado substitui essa
observação no Ubuntu/Fedora.
