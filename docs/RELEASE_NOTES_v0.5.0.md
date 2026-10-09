# Nexus Core v0.5.0 — Voice Foundation

## Entregas

- Consolidação da conversa contínua local Vosk/ALSA (fala para texto) e eSpeak NG (texto para fala), com opções de voz feminina/masculina e pausa de microfone já existentes.
- Novo controle de interface `Exigir "Nexus" para ativar`: ao ser ativado, descarta transcrições sem o prefixo no início e envia apenas o trecho da solicitação para o Agent.
- Modo padrão de escuta sem palavra-chave permanece intacto; sem necessidade de pressionar botão para falar.
- Diagnóstico `nexus-core --voice-check` verifica dependências locais e presença do modelo Vosk sem acessar microfone, alto-falantes ou PostgreSQL.
- Testes de regressão para comandos de voz, prefixos, modo sem wake, isolamento do diagnóstico e uso real da interface Tk sob display virtual Linux.
- Nenhum serviço de voz externo, nenhuma dependência paga e nenhuma alteração no design principal.

## Limitações

A frase de ativação é detectada **depois** da transcrição Vosk; não é um wake word engine dedicado. O microfone continua acessível enquanto a escuta está ligada; use **Pausar escuta** para interromper a captação. A CI usa microfone simulado e não substitui a homologação de entrada e saída reais de áudio no hardware Linux.

## Qualificação

Tag gerada somente após CI bem-sucedida para o commit exato na `main` (Python 3.12, PostgreSQL 16, Docker, Xvfb, eSpeak NG).
