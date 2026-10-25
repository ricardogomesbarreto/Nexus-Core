# Nexus Core 0.9.16 — encerramento da sessão local

Versão de código para validação no Ubuntu. PostgreSQL continua sendo o único
banco. Não há tag estável nem homologação física nesta etapa.

Ao escolher **Desligar assistente**, fechar a janela ou encerrar o iniciador,
o Nexus encerra voz, câmera, trabalhos pendentes e conexões do aplicativo.
Depois verifica o registro privado da sessão em `XDG_RUNTIME_DIR`: para
primeiro Ollama e depois o cluster PostgreSQL **somente** se cada instância
foi iniciada pelo Nexus e conserva o mesmo `InvocationID` do systemd.
Também vale para `~/.local/bin/nexus-core --desktop`, com ou sem o script
`nexus_core_session.sh`. O script `desktop` faz uma segunda tentativa de
limpeza ao sair, inclusive se o lançador falhar. O instalador agora registra
as instâncias que inicia; serviços já ativos não se tornam propriedade do
Nexus.

Para serviços de sistema, tenta `sudo -n` sem bloquear o fechamento da
janela; quando há agente gráfico e `pkexec` instalado, pode pedir a senha
administrativa para concluir a parada. Se a autorização for negada, não
houver agente ou ocorrer falha, mantém o registro para um `stop` manual e
informa no terminal. Um Ollama ou PostgreSQL iniciado fora do Nexus ou
reiniciado por outro programa é preservado. Fechar o aplicativo não desliga
o Docker, outros aplicativos nem todos os processos do computador.

## Verificação no Ubuntu

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
python3 scripts/install_linux.py
NEXUS_RESOURCE_PROFILE=eco bash scripts/nexus_core_session.sh desktop
bash scripts/nexus_core_session.sh status
ollama ps
```

Inicie a janela com serviços inicialmente parados; use o botão **Desligar
assistente** e confira as mensagens `[NEXUS] Serviço iniciado pelo Nexus
encerrado`. Se alguma parada falhar, use
`bash scripts/nexus_core_session.sh stop` no terminal com autenticação sudo.
Repita com serviços iniciados antes do Nexus: estes devem permanecer ativos.
Teste também o comando de voz explícito e o fechamento pelo controle da
janela. A CI usa serviços simulados; não comprova a parada no notebook ou
uma sessão de autenticação gráfica real.
