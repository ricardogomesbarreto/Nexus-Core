# NEXUS CORE v0.9.19 — Compatibilidade offline com exportações Kolibri

**Status:** recurso de inspeção somente de metadados em PR #102 (Draft). Não
importa conteúdos Kolibri, não copia bancos nem executa o servidor.

## Formato oficial

A documentação do Kolibri descreve exportações offline em uma pasta
`KOLIBRI_DATA`, com os arquivos dos canais em `content/databases` e
os recursos em `content/storage`.

- [Kolibri — Canais e recursos](https://kolibri.readthedocs.io/en/latest/manage/resources.html)
- [Kolibri — Estrutura de armazenamento](https://kolibri.readthedocs.io/en/latest/manage/provision.html)

Para inspecionar, **copie** o diretório `KOLIBRI_DATA` para uma pasta dentro
do seu HOME que não seja protegida pela política do NEXUS CORE. Na Biblioteca
local, clique em **Inspecionar exportação Kolibri**, selecione a própria
pasta `KOLIBRI_DATA` e confirme. Este recurso não acessa USB montado fora
do HOME; não conceda permissões mais amplas apenas para contornar a regra.

O NEXUS CORE lista até 60 IDs de canais (hexadecimal com 32 caracteres)
e o tamanho do arquivo de banco de cada canal. Também indica a existência
do diretório de recursos. Nomes de disciplinas, títulos e conteúdo não são
extraídos. O banco SQLite interno do Kolibri **não é aberto** pelo NEXUS CORE:
o PostgreSQL permanece o banco de persistência do assistente.

A inspeção é limitada a até 300 entradas no diretório de bancos, não é
recursiva e não segue links simbólicos. Não instala Kolibri, não inicia
serviços, não lê conteúdos dos arquivos, não executa comandos, não cria
conexões HTTP, não modifica a exportação e não grava inventário no banco.

## O que está e não está implementado

**Disponível nesta etapa:** detectar um conjunto exportado, verificar IDs e
tamanhos dos canais e se a pasta de recursos existe. Isto ajuda a organizar
materiais e planejar uma integração futura.

**Não disponível:** executar lições ou exercícios Kolibri no NEXUS CORE,
converter automaticamente recursos Kolibri em aulas nativas, importar
canais, acessar conteúdo protegido, autenticar usuários Kolibri ou
sincronizar dados educativos.

Para usar cursos Kolibri reais, a importação deve ser feita pelo próprio
Kolibri, seguindo a documentação oficial. O NEXUS CORE não automatiza esse
processo sem validação adicional de segurança, consentimento e desempenho.

## Testes

~~~bash
python -m pytest -q tests/test_kolibri_export_v0919.py tests/test_kolibri_desktop_v0919.py
~~~

Validar no Ubuntu 26.04 com exportação genuína e autorização explícita,
verificando também que nenhum serviço ou socket é iniciado.
