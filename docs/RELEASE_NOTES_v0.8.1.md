# NEXUS CORE v0.8.1 — Linux Bootstrap & Verified Self-Update

> **Nota de compatibilidade retrospectiva (10/10/2026):** a formulação original desta versão mencionava Ubuntu/Debian. A diretriz oficial posterior da **v0.8.2 restringiu a instalação automática ao Ubuntu Desktop 24.04 LTS**. Mencionar Debian neste histórico não constitui suporte/homologação atual. Este marco foi integrado como código à `main`, porém segue sem tag estável própria, aguardando aceite físico.\n\n## Instalação e primeira execução

- Novo instalador interativo `python3 scripts/install_linux.py`, destinado inicialmente a Ubuntu/Debian com Python 3.12+.
- Detecção de ferramentas Linux e opção de instalação de pacotes oficiais mediante confirmação e senha do `sudo`: Tk, PostgreSQL, xdotool, eSpeak NG, ALSA, FFmpeg e suporte a `venv`. Não executa `curl | bash`, não opera como root e não concede automaticamente acesso ao grupo Docker.
- Provisionamento **não destrutivo** de PostgreSQL local com usuário e banco dedicados `nexus`: se encontrar recursos existentes, preserva os dados e solicita configuração manual. Senha aleatória fica em arquivo 0600 e jamais é exibida nos logs.
- Ambiente Python isolado por versão em `~/.local/share/nexus-core/managed/versions/`, com instalação das dependências `.[voice,vision]`; launcher no `~/.local/bin/nexus-core`.
- O instalador pergunta se o usuário deseja habilitar atualizações automáticas. A preferência pode ser desligada alterando `auto-update.enabled` para `0`. Sem consentimento, nenhum acesso à API do GitHub ocorre por este mecanismo.

## Atualizações automáticas seguras

- O launcher gerenciado verifica releases estáveis no repositório oficial `ricardogomesbarreto/Nexus-Core` usando HTTPS.
- Aceita apenas versões sem sufixos e **wheel oficial com nome esperado**, URL de download pertencente àquela tag, tamanho limitado e digest SHA-256 anunciado na API GitHub.
- Downloads são limitados, verificados integralmente por SHA-256 e preparados em diretório privado. Nada é executado antes da verificação.
- A versão é instalada em um **novo ambiente virtual isolado**; executável/versionamento são verificados antes de comutar atomicamente o apontador `current`. O ambiente anterior permanece preservado como `previous` para recuperação operacional.
- Enquanto o assistente está aberto, um verificador **opt-in** consulta periodicamente (intervalo de 1 hora) e **apenas baixa/prepara** o pacote. Uma nova versão é **aplicada no próximo início**, não durante a fala, gravação, conversa, visão ou operação de dispositivo.
- Ausência de rede, release incompleta, SHA incorreto, URL inesperada, dependências indisponíveis ou versão não crescente **não alteram o ambiente instalado**.
- A release v0.8.1 adiciona um workflow que gera e publica wheel após CI verde do **commit exato integrado à main**. Não existe lançamento automático de versão anterior sem artefato verificável.

## Limites importantes

- Atualizações estão disponíveis **somente para instalações criadas pelo instalador gerenciado**; iniciar diretamente o script da árvore Git ou o Python do sistema não habilita atualizações.
- O GitHub fornece canal HTTPS e hash de integridade do pacote, mas esse fluxo **não fornece assinatura independente ou atestado criptográfico de procedência**; a segurança ainda depende da conta e das permissões de release no GitHub.
- Bibliotecas Python transitivas são adquiridas de repositórios de pacotes durante criação do novo ambiente, respeitando dependências e restrições do `pyproject.toml`, mas **não há lockfile completo com hashes** nessa versão. A falta de rede interrompe a instalação da nova versão, preservando a anterior.
- Não promete rollback de migrações de banco futuras. A automação é restrita a código/venv e não reconfigura nem exclui dados do usuário.
- O Ollama é um runtime externo: a v0.8.1 **não executa scripts remotos para instalá-lo** e orienta a usar fontes oficiais. Modelos `qwen3:1.7b` e `gemma3:4b` (bem como modelos Vosk), Docker e permissões de microfone/câmera podem exigir download e configuração/consentimento separados.
- Planos Ubuntu/Debian são contemplados para `apt`; SteamOS/Arch, Fedora e outras distribuições recebem diagnóstico, sem tentar executar comandos incompatíveis.
- Sem root silencioso, serviços de sistema criados sem consentimento, mudança do visual Tk, integração de VPS/Hostinger ou modificação de NEXUS ERP/NUTRA/ADV.

## Testes e publicação

- Testar parsing das releases, rejeição de URLs e hashes inválidos, falhas de download, comportamento offline, preparação/atualização atômica, caminho de execução, consentimento no instalador e integração sem atualizações durante testes de desenvolvimento.
- A v0.8.1 é empilhada sobre o PR #12 (v0.8.0), que depende do PR #11 (v0.7.3). A homologação física X11 permanece um gate anterior.
- **Nenhum merge ou tag/release v0.8.1** sem dependências integradas, CI verde na `main`, validação de instalação real Ubuntu 24.04 e teste de atualização/rollback na máquina Linux.

## Próximo refinamento

Apoio a pacotes de outras distribuições, assinatura independente/atestação do artefato, cache offline de dependências, progresso visual, e testes reais de upgrades de PostgreSQL/Ollama deverão ser tratados como marcos adicionais, não pressupostos da v0.8.1.
