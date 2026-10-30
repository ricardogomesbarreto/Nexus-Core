# NEXUS CORE — v0.9.19 (proposta técnica em PR #102)

Status: **implementação em branch, sem merge/tag/release**. A CI do SHA final e o
aceite físico no Ubuntu ainda são obrigatórios. Não alterar design do Nexus Core.

## Fontes inspecionadas

- `VoiceStudio-main(1).zip`: AGPL-3.0; ditado, prévia de voz, ASR, motores e
  serviços de mídia. **Não copiamos código, frontend, binários ou modelos**.
- `project-nomad-main(3).zip`: Apache-2.0; bibliotecas e catálogos offline,
  ZIM/Kiwix, cursos Kolibri, mapa, Ollama, dados e servidores.
- `DeepTutor-main(1).zip`: Apache-2.0; biblioteca, prática, tutoria, questões,
  leitura fundamentada e rotinas de estudo.

Os três são referências funcionais. Esta etapa contém implementação **original**,
mínima e local, sem integração das aplicações terceiras como serviços.

## Entregas desta branch

| Origem | Entrega implementada em código | Limite / lacuna |
|---|---|---|
| DeepTutor | `nexus/offline_study.py`: gerar lacunas com trechos-fonte | Heurístico, não é IA generativa nem avaliação semântica |
| DeepTutor | `nexus/study_session.py`: sequência de questões, respostas e acertos | Respostas vivem apenas em RAM durante a sessão |
| DeepTutor | `nexus/desktop/study_panel.py`: exercícios na janela existente | Exige trecho da Biblioteca escolhido pelo usuário |
| DeepTutor | `nexus/study/store.py`: resultado opcional por trecho no PostgreSQL | Até 200 sessões, sem respostas; exclusão da fonte remove resultados |
| VoiceStudio | `nexus/voice/file_transcription.py`: transcrição Vosk de WAV escolhido | PCM mono, 16-bit/16 kHz, até 180 s e 16 MiB; nada de MP3 ou ditado contínuo de arquivo |
| VoiceStudio | `nexus/desktop/library_panel.py`: botão de transcrição | Resultado efêmero na janela; não grava nem importa automaticamente |
| VoiceStudio | `nexus/desktop/study_panel.py`: leitura local de trecho e interrupção | Usa Piper/RHVoice/eSpeak já disponíveis; sem clonagem, mixer ou pausa no meio |
| NOMAD | `nexus/knowledge/offline_catalog.py`: inventário de ZIM e materiais educativos | Lista somente metadados de até 60 arquivos em pasta escolhida; não lê ZIM nem roda Kolibri |
| NOMAD | `nexus/desktop/library_panel.py`: botão de catálogo | Sem recursão, download, instalação ou servidores |

## Resumo e roteiro de estudos local

Na Biblioteca, **Resumir trechos com IA local** e **Plano de estudo com IA
local** consultam até três trechos recuperados explicitamente do PostgreSQL
e enviam apenas esse contexto ao Ollama local. Não geram arquivo, não salvam
o plano nem prometem personalização pedagógica. Se não houver fonte, não
carregam modelo. O conteúdo é gerado e exige conferência humana.

## Compatibilidade e privacidade

- PostgreSQL permanece o único banco do NEXUS CORE.
- Vosk, Piper/RHVoice e Ollama são reutilizados; **sem downloads e sem iniciar
  serviços automaticamente**. Transcrição usa somente Vosk instalado.
- Arquivos são autorizados pelos descritores seguros de `PathSecurity`; catálogo
  de pasta não percorre subdiretórios nem segue symlinks.
- Não é salvo conteúdo de áudio, transcrição, exercícios respondidos ou arquivos
  do catálogo; gravação de pontuação exige confirmação.
- Mensagens de erros para a interface omitem textos privados e caminhos.
- A rotina atual de cartões e a interface visual existente são preservadas.

## Itens ainda não integrados dos 38 recursos desejados

**VoiceStudio**: ajustes adicionais de áudio e pausa/retomada em ponto exato,
processamento avançado de áudio, ASR em outros formatos, melhorias físicas de
latência e testes contínuos de microfone. Voz masc./fem., fala, Vosk, controle
de interrupção e conversação contínua têm implementação preexistente, mas
necessitam de aceite real de hardware.

**NOMAD**: pesquisa integral nos arquivos ZIM, execução opcional e
controlada de cursos Kolibri, mapa avançado, **indexação vetorial completa**,
catálogo executável de apps e benchmark de inferência de ponta a ponta.
Biblioteca .txt/.md, FTS PostgreSQL, consulta via Ollama, notas, conversões,
SHA-256 e mapas PMTiles já existiam; não foram reimplementados nesta branch.

**DeepTutor**: agente tutor personalizado com plano adaptativo, geração de
atividades pelo modelo, correção semântica fundamentada, explicação pedagógica
de erros, planos de aula, métricas de domínio e multimodalidade integrada ao
tutor. A v0.9.19 **não** afirma entregar essas capacidades.

## Gates para fechamento

1. CI no SHA final, com testes unitários, PostgreSQL 16 e Tk/Xvfb.
2. Aceite manual no Ubuntu 26.04: importar arquivo local, selecionar trecho,
   gerar/responder questões, salvar/ler resultados e remover documento;
   escolher WAV, transcrever com Vosk e não persistir sem consentimento;
   ler/interromper voz masculina e feminina; visualizar pasta com ZIM sem
   iniciar serviços.
3. Medir RAM/swap e latência em perfil `eco`; validar que serviços preexistentes
   não são desligados e que o programa não cria autostart.
4. Revisão de acessibilidade, licenças e privacidade. Não realizar merge nem
   publicação estável antes dos gates.

Comandos de testes relativos à raiz do repositório:

```bash
python -m pytest -q tests/test_offline_study.py tests/test_study_session.py \
  tests/test_voice_file_transcription_v0919.py \
  tests/test_offline_catalog_v0919.py tests/test_study_progress_v0919.py
```

## Ampliação da etapa seguinte

Ajustes de voz de **velocidade 75%, 100%, 125%** e **volume 50%, 75%,
100%, 125%, 150%** estão em **Recursos → Configurar voz local**. São preferências locais,
validadas e retrocompatíveis com JSON v1. eSpeak usa flags próprias;
Piper/RHVoice geram WAV local e, apenas quando há ajustes, FFmpeg processa
a velocidade/ganho antes da reprodução. A falta do FFmpeg gera erro claro,
sem download automático. Foi acrescentada pausa/retomada do processo local em Linux com SIGSTOP/SIGCONT; a precisão da retomada audível ainda exige teste físico.

O catálogo ZIM agora pode ler um **artigo individual identificado pela URL**
via `zimdump show`, sem iniciar `kiwix-serve`. A leitura usa descritor
autorizado, subprocesso sem shell, limites de tempo/saída e extração textual
básica de HTML; exige `zim-tools` instalado opcionalmente. Não são
implementados busca de texto integral no ZIM, exibição com imagens ou gestão
de bibliotecas gigantes. Testar com ZIM real no Ubuntu é obrigatório.

O botão **Tutor guiado por fontes** usa três níveis explícitos (Iniciante,
Intermediário e Avançado). A pergunta é estruturada em até 160 caracteres
e segue a implementação existente que utiliza somente até três fontes
locais para solicitar resposta ao Ollama. Não faz diagnóstico do aluno,
nem adapta conteúdo automaticamente entre sessões.

## Similaridade semântica leve com Ollama (opt-in)

O botão **Similaridade semântica local** utiliza um modelo de embeddings
**já instalado**. O Nexus consulta somente `/api/tags` e `/api/embed`
no Ollama de loopback, sem redirecionamento HTTP, download ou inicialização
automática. A pesquisa compara a pergunta com **até oito candidatos** recuperados do
PostgreSQL: até quatro resultados por texto/FTS, complementados por trechos de
documentos recentes distintos. Exibe até cinco resultados por cosseno.

O modelo precisa ser indicado explicitamente pelo usuário, estar instalado e
ter tamanho informado de até 900 MiB. As entradas e respostas são limitadas,
o parâmetro `keep_alive: 0` solicita descarregar o modelo. Nenhum embedding
fica salvo no disco. Antes de carregar o modelo, é verificada a memória
realmente disponível; sem margem suficiente a operação é recusada.
**Essa é uma amostra semântica limitada**, não indexação
semântica global de todos os documentos nem busca exaustiva em toda a base. O modo anterior FTS segue disponível.

A configuração de velocidade e volume foi deslocada para **Recursos →
Configurar voz local**, evitando reduzir a área de conversa na janela mínima
(770×570). Uma execução anterior da CI detectou dois testes de layout falhos;
a correção requer nova execução de CI no SHA final. A prévia física é pendente.

## Transcrição de arquivos em formatos adicionais

O botão de transcrição da Biblioteca agora permite selecionar `.wav`, `.mp3`,
`.ogg`, `.flac` ou `.m4a` explicitamente. WAV PCM mono 16 kHz continua
usando leitura direta; formatos comprimidos exigem **FFmpeg instalado localmente**
e são decodificados em memória até 180 s para o Vosk já instalado. O arquivo
de origem é aberto com descritor seguro, sem shell, servidor, microfone, rede
ou armazenamento automático. Há limite de 32 MiB de entrada, timeout de 35 s
na conversão e limite de bytes de PCM decodificado. Não processa vídeos e não
promete transcrição em tempo real nem precisão de fala no hardware real.

## Cursos offline nativos e recomendações de estudo

A Biblioteca também abre **uma pasta escolhida pelo usuário** contendo um
manifesto JSON versionado e até vinte aulas TXT/Markdown com leitura individual.
A janela de cursos permite marcar conclusão, exercitar lacunas literais por
aula, receber sugestões indicativas a partir dos acertos e avançar sem abrir
automaticamente os próximos arquivos. Um exemplo original está em
[examples/offline_course](../examples/offline_course).

**Persistência:** explicitamente confirmada para salvar/restaurar, somente
índices de aulas concluídas e uma chave SHA-256 na tabela PostgreSQL local;
nenhum texto/arquivo/caminho/áudio/resposta é salvo nesse fluxo. A memória
temporária da janela pode ser descartada ao fechar. Não há sincronização
remota. Consulte [OFFLINE_COURSES_v0.9.19.md](OFFLINE_COURSES_v0.9.19.md).

Segurança: até 20 aulas, manifesto de 16 KiB, texto de 64 KiB por aula,
total de 512 KiB, sem travessia de caminho, sem symlinks, sem servidor.
Essa é uma **alternativa local de baixo consumo**, não execução do pacote
Kolibri nem leitura de cursos e vídeos Kolibri.

## Inspeção opcional de exportações Kolibri (somente metadados)

A Biblioteca oferece **Inspecionar exportação Kolibri**, opção que reconhece
a estrutura oficial `KOLIBRI_DATA/content/databases` e indica se existe
`content/storage` em uma exportação copiada para o HOME autorizado. Lista
somente IDs dos canais e tamanho dos bancos; não abre SQLite, não interpreta
atividades/arquivos nem inicia Kolibri, Docker, portas, downloads ou importações.

O limite é de 60 bancos de canais em até 300 entradas de diretório, com
proteção contra links simbólicos. A leitura/conversão integral de cursos
Kolibri permanece pendente. [Instruções e limitações](KOLIBRI_EXPORT_v0.9.19.md).

## Pesquisa e narração de aulas offline sob demanda

O leitor de cursos nativos agora oferece **Pesquisar no curso**, com busca
textual normalizada (maiúsculas/acentos), limitada ao manifesto autorizado,
no máximo vinte arquivos TXT/Markdown e oito excertos retornados. Não cria
índice local persistente, não acessa rede nem utiliza Ollama.

A janela oferece **Ouvir aula**, **Pausar/retomar áudio** e **Parar áudio**.
O usuário precisa primeiro selecionar e ler uma aula; a narração cobre até
2.400 caracteres por clique, usando voz masculina/feminina e velocidade/volume
selecionados no NEXUS CORE. Apenas processos TTS de propriedade do assistente
podem ser pausados/retomados; trocar de aula ou fechar a janela encerra a fala.
Não há leitura de arquivos em segundo plano nem download de vozes.

Testes específicos:
`tests/test_course_search_v0919.py` e
`tests/test_course_voice_search_desktop_v0919.py` (Tk/Xvfb simulado).
Aceite físico de áudio/latência no Ubuntu segue obrigatório.
