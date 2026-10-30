# NEXUS CORE v0.9.19 — Cursos offline nativos e acompanhamento

**Estado:** código em PR #102 (Draft); CI final e aceite físico no Ubuntu pendentes. Implementação original, sem copiar materiais de terceiros.

## Abrir um curso

Na janela Biblioteca local, selecione **Abrir curso offline**, escolha uma pasta permitida dentro do HOME e confirme. A pasta contém um arquivo chamado course.json e aulas Markdown (.md) ou texto (.txt) na mesma pasta. Há um curso original para teste em [examples/offline_course](../examples/offline_course).

Exemplo de course.json:

~~~json
{
  "version": 1,
  "title": "Meu curso local",
  "lessons": [
    {"title": "Aula 1", "file": "aula1.md"},
    {"title": "Aula 2", "file": "aula2.txt"}
  ]
}
~~~

**Pesquisar no curso** busca texto e expressões em até vinte aulas autorizadas, sob solicitação, com tolerância a acentos/maiúsculas e até oito trechos retornados, sem criar índice persistente. A busca é literal normalizada, não semântica. **Ler aula** abre apenas o arquivo escolhido. **Concluir aula** marca o item na memória. **Gerar exercícios** constrói lacunas literais do trecho lido, sem IA. **Responder exercício** confere a resposta literalmente (sem diferenças de caixa e espaços externos). **Próxima aula** não lê arquivos automaticamente.

**Sugerir próximo passo** usa somente a pontuação da sessão: com menos de cinco questões recomenda praticar; abaixo de 60% propõe revisão; de 60% até menos de 85% recomenda aplicação; a partir de 85% propõe desafios. É heurística, não avaliação semântica nem diagnóstico de aprendizagem. Na janela de cartões, o histórico PostgreSQL previamente autorizado também pode oferecer sugestão por fonte.

## Persistência opcional

- Leitura e exercícios funcionam sem iniciar PostgreSQL.
- **Salvar progresso** exige confirmação e registra somente índices de aulas concluídas na tabela PostgreSQL local nexus_offline_course_progress.
- **Carregar progresso** é manual e solicita confirmação antes de substituir marcações feitas na janela.
- Chave SHA-256 calculada da identidade local do curso (caminho e metadados) sem armazenar caminho, título, texto, áudio ou respostas em claro no banco.
- Limite de 100 cursos salvos. Mudança de caminho, título ou lista de aulas gera nova chave de curso.
- Nenhum servidor Kolibri/Kiwix, rede, Ollama, instalação ou serviço extra é iniciado automaticamente.

## Limites de segurança

- Pasta dentro de HOME, excluídos os diretórios protegidos.
- Linux com descritores ancorados e O_NOFOLLOW; links simbólicos e travessia de caminho são recusados.
- Manifesto JSON UTF-8 com no máximo 16 KiB, versão 1 e até 20 aulas.
- Aulas .md ou .txt no mesmo diretório, máximo de 64 KiB por aula e de 512 KiB de conteúdo do curso.
- Nenhuma execução de macros, HTML, código, notebooks ou conteúdos ativos.
- Não ocorre download, leitura recursiva, varredura de diretórios ou importação automática.

## Limitações

Esta implementação oferece **cursos nativos leves**, não uma instalação ou execução integral de cursos Kolibri. A integração Kolibri, busca semântica completa, tutoria adaptativa avançada e testes físicos de hardware continuam pendentes. O NEXUS CORE continua sendo assistente geral.

## Testes

~~~bash
python -m pytest -q tests/test_offline_course_v0919.py tests/test_offline_course_progress_v0919.py tests/test_study_recommendations_v0919.py tests/test_course_desktop_v0919.py
~~~

Validar no Ubuntu 26.04: abrir o curso demonstrativo, ler, concluir, responder exercícios, salvar progresso mediante confirmação, reabrir e restaurar. Medir RAM/swap e confirmar serviços sob demanda.
