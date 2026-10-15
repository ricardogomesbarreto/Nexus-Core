# NEXUS CORE v0.9.11 — First-Run PostgreSQL Authentication

## Entrega

- O instalador guiado Ubuntu Desktop 24.04 LTS verifica a autenticação do usuário e banco PostgreSQL configurados no runtime Python instalado, com `SELECT 1` somente leitura no loopback local. Credenciais existentes e novas passam pela mesma verificação antes da troca da versão ativa.
- Uma senha presente no ambiente ou no arquivo privado já não basta para declarar a instalação concluída. Se a verificação falhar, a nova versão não é ativada e nenhum launcher é escrito. A falha é relatada com orientação fixa, sem exibir senha, consulta sensível ou mensagens brutas do driver.
- O pré-diagnóstico reutilizado observa a lista do modelo Ollama e dependências Vosk/eSpeak/ALSA sem baixar modelos nem usar microfone, câmera ou alto-falante. O instalador orienta a configuração manual e o comando `nexus-core --ubuntu-preflight`, sem confundir detecção de binário/diretório com prontidão física.
- Testes verificam passagem privada das credenciais ao processo filho, status de autenticação aceitos/recusados, arquivo privado e ausência de ativação ao falhar.

## Limites

A consulta não prova permissões de criação de tabelas, nem testa as operações completas do assistente. O diagnóstico de Ollama só inspeciona o catálogo local, sem inferência. A verificação Vosk testa visibilidade de dependências, sem reconhecer fala real. O instalador continua exigindo aceitação explícita dos pacotes e do provisionamento, e o aceite físico X11, áudio, câmera, modelo, PostgreSQL e recuperação em Ubuntu permanece pendente.

## Integração e publicação

Código da linha v0.9.x integrado à `main` sem tag deste marco. A última release oficial permanece v0.7.2. O workflow v0.9.11 fica desabilitado; publicação requer CI no commit final da `main`, homologação física registrada e revisão específica do workflow de release.
