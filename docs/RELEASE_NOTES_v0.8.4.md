# NEXUS CORE v0.8.4 — Ubuntu Readiness Preflight

## Escopo: verificar dependências do uso real, sem modificar o Ubuntu

A v0.8.4 evolui o `--ubuntu-doctor` da v0.8.3 com o comando adicional **`nexus-core --ubuntu-preflight`**, destinado ao Ubuntu Desktop 24.04 LTS e executado apenas mediante ação explícita do usuário.

O preflight verifica de forma limitada e **somente leitura**:

1. **PostgreSQL**: autentica com as credenciais locais já configuradas no NEXUS CORE (incluindo `NEXUS_DATABASE_PASSWORD` quando presente), aceita apenas endereços de loopback `127.0.0.1`, `localhost` ou `::1`, impõe timeout de 3 segundos, habilita `default_transaction_read_only=on` e executa exclusivamente `SELECT 1`. Nenhuma tabela, schema ou registro é consultado ou alterado. Ausência de senha e falhas de autenticação são reportadas sem expor segredos.
2. **Modelo Ollama**: consulta unicamente `GET http://127.0.0.1:11434/api/tags`, em conexão HTTP ao loopback, timeout de 3 segundos e resposta limitada a 64 KiB/256 entradas. Compara apenas o nome com `local_model_name` (padrão `qwen3:1.7b`). O relatório indica se o modelo está **listado**; não baixa o modelo nem testa sua inferência ou desempenho. A lista real de modelos não é incluída no relatório.
3. **Voz**: reutiliza o diagnóstico passivo da v0.8.3, verificando presença dos recursos `arecord`, `espeak-ng`, pacote Python Vosk e diretório do modelo offline. **Não abre nem grava o microfone**, não reproduz voz e não testa permissões reais do hardware.
4. **Plataforma/serviços**: agrega o resumo local da v0.8.3 (Ubuntu, pacotes, `pg_isready`, API de versão Ollama) e diferencia a possibilidade de tentar chat por texto e de tentar chat por voz.

## Utilização

```bash
nexus-core --platform-check   # estritamente passivo, sem conexões
nexus-core --ubuntu-doctor    # serviços locais sem autenticação
nexus-core --ubuntu-preflight # login SQL read-only, inventário local Ollama e voz passiva
```

A saída é JSON `nexus.ubuntu-preflight.v1` e contém somente flags e estados conhecidos, itens pendentes e recomendações genéricas. Não grava informações, não aciona `apt`, `sudo`, serviços, atualizações, modelos, áudio, vídeo ou redes externas.

**`text_chat_dependencies_ready_to_try` e `voice_chat_dependencies_ready_to_try` são apenas indicações de dependências básicas**, e não garantias de que o assistente falará, compreenderá, ouvirá microfone, reconhecerá imagens ou suportará uso prolongado. O teste físico de dispositivos e a execução real dos modelos permanecem obrigatórios.

## Testes e critérios de segurança

- Rejeitar host PostgreSQL remoto, credenciais ausentes e respostas SQL inesperadas; nenhum log pode conter a senha ou mensagens de exceção de drivers.
- Consulta Ollama apenas ao loopback e ao caminho fixo `/api/tags`; rejeitar códigos HTTP diferentes de 200, JSON inválido, listas grandes e valores inesperados.
- Testar serviço indisponível, falha de autenticação, voz incompleta e agregação de recomendações.
- Comando CLI isolado de demais operações; testes de CI Ubuntu 24.04/PG16/Docker/Xvfb com regressão da arquitetura anterior.

## Publicação e dependências

O PR da v0.8.4 fica empilhado sobre a **v0.8.3 (PR #15)**, que tem CI aprovada, mas não foi integrada nem homologada fisicamente. As versões v0.7.3–v0.8.2 estão integradas no código da `main`, porém a **última release estável continua v0.7.2**. Nenhuma tag/release v0.8.4 deve ser criada antes da homologação Ubuntu real e da revisão do bloqueio de publicação.

**Prioridade de plataforma:** Ubuntu Desktop 24.04 LTS. A ampliação para outras distribuições Linux será feita posteriormente, com adaptadores e testes dedicados. Não há hospedagem, serviço de nuvem nem ferramentas pagas adicionais.
