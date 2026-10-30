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

**VoiceStudio**: painel de velocidade/volume, pausa/retomada em ponto exato,
processamento avançado de áudio, ASR em outros formatos, melhorias físicas de
latência e testes contínuos de microfone. Voz masc./fem., fala, Vosk, controle
de interrupção e conversação contínua têm implementação preexistente, mas
necessitam de aceite real de hardware.

**NOMAD**: leitura e pesquisa dentro de arquivos ZIM, execução opcional e
controlada de cursos Kolibri, mapa avançado, pesquisa **semântica por embeddings**,
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
