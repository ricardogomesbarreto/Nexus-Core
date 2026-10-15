# NEXUS CORE v0.8.3 — Ubuntu First-Run Doctor

## Objetivo

A v0.8.3 dá ao usuário do **Ubuntu Desktop 24.04 LTS** um diagnóstico de primeira execução, isolando problemas de dependências, PostgreSQL e Ollama **sem fazer modificações no sistema**. A evolução mantém o aplicativo local, sem hospedagem e open source. O suporte de instalação em outras distribuições continua pendente de homologação específica.

## Entregas

- Novo comando explícito `nexus-core --ubuntu-doctor`, independente da interface Tk, banco inicializado e modelo Ollama carregado.
- Usa a matriz somente leitura `nexus.platforms` criada na v0.8.2 e acrescenta somente duas verificações locais:
  - `pg_isready -h 127.0.0.1 -p 5432 -t 2`: com timeout controlado; confirma **aceitação de conexões pelo serviço**, não autentica o usuário, não verifica schema, não lê dados nem altera PostgreSQL.
  - `GET http://127.0.0.1:11434/api/version`: conexão HTTP **exclusivamente ao loopback**, timeout de dois segundos, resposta limitada a 2048 bytes e validação estrita de estrutura; verifica a disponibilidade da API do Ollama, **não** a instalação de um modelo, inferência, desempenho ou conversação por voz.
- Saída JSON estruturada `nexus.ubuntu-doctor.v1` com bloqueios, recursos ausentes e recomendações estáticas. Sem expor credenciais, conteúdo retornado pelo modelo, variáveis privadas, caminhos pessoais ou informações sobre processos do usuário.
- Em Ubuntu Wayland, a interface Tk pode funcionar, mas a automação opcional `xdotool` de janelas exige X11 local; o doctor apenas informa essa restrição.
- Verificações unitárias de indisponibilidade, timeouts, redirects HTTP recusados, respostas Ollama inválidas, ausência de binários, isolamento do CLI e recomendações sem execução.
- Nenhuma alteração de identidade visual, voz, permissões de câmera/tela, dados persistentes, dispositivos declarados, instalador com consentimento nem atualizações com verificação SHA-256.

## Como utilizar (após instalar esta versão)

```bash
nexus-core --platform-check
nexus-core --ubuntu-doctor
```

`--platform-check` permanece totalmente passivo, **sem conexão nem local**. `--ubuntu-doctor` faz somente consultas locais de serviço, sem autenticação e sem executar alterações, e pode funcionar mesmo quando o assistente principal ainda não consegue inicializar.

O campo `core_services_ready_to_try=true` significa apenas que os **serviços básicos** estão acessíveis e não foram encontrados binários obrigatórios faltantes. Não é garantia de funcionamento completo: modelo Ollama instalado, PostgreSQL autenticado, microfone, câmera, fala, consumo de RAM, GPU e interação real com a interface devem ser validados separadamente.

## Dependências de lançamento

1. Código das versões v0.7.3, v0.8.0, v0.8.1 e v0.8.2 **integrado em `main`**; nenhum dos quatro marcos recebeu certificação física ou nova tag estável.
2. CI Ubuntu 24.04 / Python 3.12 / PostgreSQL 16 / Docker / Xvfb aprovada no commit da v0.8.3 e após eventual integração futura.
3. Homologação da sequência X11, instalação Ubuntu, configuração de PostgreSQL/Ollama, recuperação de atualização e regressões de voz/visão **no desktop físico real**.
4. Publicação estável **intencionalmente desativada** em workflows enquanto não houver aceite físico documentado. Release workflow da v0.8.3 permanece bloqueado e requer uma alteração separada revisada antes de qualquer tag/release.

## Próximo passo previsto

Uma homologação real do Ubuntu Desktop seguida de estabilização do instalador e primeiros fluxos de voz/visão; depois, iniciar adaptadores individuais para outras distribuições sem introduzir `apt`/serviços incompatíveis.
