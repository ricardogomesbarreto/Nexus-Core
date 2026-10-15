# NEXUS CORE v0.8.5 — Ubuntu Recovery & Documentation Integrity

## Objetivo

Reforçar a recuperação de falhas do atualizador gerenciado antes de ampliar a distribuição do NEXUS CORE para outras variantes Linux, e reconciliar toda a documentação disponível com o estado de implementação e publicação. **Ubuntu Desktop 24.04 LTS continua o alvo prioritário**; o CORE continua gratuito, open source, local, com banco PostgreSQL e Ollama locais, interface Tk preservada e ações sensíveis sujeitas a autorização.

## Entregas implementadas

- `nexus/updates/recovery.py`: recuperação **offline, sem dependências externas do Python**, executável independentemente do ambiente virtual selecionado. Não carrega a aplicação, o banco nem o modelo.
- Instalador gerenciado Ubuntu passa a disponibilizar `~/.local/bin/nexus-core-recover`, cópia autônoma com caminho gerenciado definido na instalação e permissões restritas, recusando sobrescrever um utilitário desconhecido ou link simbólico.
- `nexus-core-recover --status`: relatório limitado de versão `current`, `previous`, disponibilidade de reversão e estado de atualização automática, sem apresentar caminhos, variáveis, credenciais nem executar comandos.
- `nexus-core-recover --rollback`: solicita `REVERTER` em terminal interativo e **recusa** sem autorização, com versão anterior ausente, adulteração dos links, links que escapem da pasta gerenciada, diretórios permissivos ou binário inválido. Troca o apontador para versão anterior sem instalar pacotes, criar banco, apagar dados ou reiniciar o assistente.
- **Atualizações automáticas desativadas na reversão**, para impedir reaplicação imediata da versão problemática no lançamento seguinte. O operador pode reativá-las posteriormente com a configuração já prevista pelo instalador.
- Testes cobrindo recusa de TTY, confirmação inexata, versão ausente, symlinks externos, permissões inseguras, binário malformado, rollback sem internet, preferência desativada, execução independente do checkout e respeito a ferramentas já existentes.
- Auditoria documental em `docs/DOCUMENTATION_AUDIT_v0.8.5.md`: README, identidade visual, homologação X11, notas históricas e workflows, com matriz de contratos operacionais, inconsistências e estado de publicação.
- Referências operacionais de PRs antigos corrigidas; notas históricas receberam esclarecimento de que **apenas Ubuntu 24.04** está no baseline atual de instalação guiada.

## Uso após instalação gerenciada desta versão

```bash
# Primeiro, encerre as instâncias do NEXUS CORE.
~/.local/bin/nexus-core-recover --status

# Somente se precisar desfazer uma atualização de código:
~/.local/bin/nexus-core-recover --rollback
```

É necessário haver uma versão anterior já preservada; o comando não inventa backups. Não utilize `sudo`; nenhuma ação ocorrerá sem confirmação explícita no terminal.

## Limites reais

- A recuperação é **do seletor de versão do aplicativo**, não um restore completo. Não desfaz alterações de schema PostgreSQL, nem garante que código e banco de versões distintas sejam semanticamente compatíveis.
- Não é uma assinatura independente nem checksum de todos os arquivos de Python instalados; venv e pacote podem exigir inspeção/reinstalação manual se adulterados. O programa recusa links/arquivos claramente inseguros e encerra sem vazamento de detalhes privados.
- A reversão não interrompe a aplicação aberta, não restaura câmera/microfone e **não substitui a homologação de recuperação em Ubuntu físico**. O procedimento exige fechar o assistente antes de executá-lo.
- A primeira instalação não possui versão `previous` até uma atualização válida posterior.
- Não habilita suporte Arch, Fedora, Debian, SteamOS ou instalação de outros modelos/dispositivos automaticamente.
- Não altera o design da janela, a segurança do `SecurityGate`, os contratos de voz/visão, nem as políticas de transmissão de dados para fora do dispositivo.

## Validação e publicação

- Rodar CI Ubuntu 24.04 com Python 3.12, PostgreSQL 16, Docker, Xvfb e suíte de regressão anterior, mais testes isolados de recuperação e documentos.
- Respeitar os PRs anteriores **#15 v0.8.3** e **#16 v0.8.4**, ambos em draft antes deste marco.
- **Nenhuma tag/release v0.8.5 será publicada** enquanto não houver CI do commit exato, homologação X11, instalação, voz/visão e ciclo real de atualização/rollback no Ubuntu. O workflow de release desta versão permanece intencionalmente desativado.
