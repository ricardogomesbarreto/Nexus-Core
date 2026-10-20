# Análise estática avançada opcional (REA) — Nexus Core v0.9.12

## Origem e compatibilidade

Anexo inspecionado: `rea-main.zip`, projeto **REA — Reverse Engineer Anything**
(morluto/rea), licença MIT, desenvolvido principalmente em Node.js/TypeScript.
O ZIP contém 4.665 entradas incluindo fontes, ferramentas, documentação e testes.
Sua presença no chat **não instala** nem autentica o REA no computador.

Documentação upstream no arquivo: `README.md`, `docs/cli.md`,
`LICENSE` e `DISCLAIMER.md`. O projeto especifica Node.js
22.19+, 24.11+ ou 26+, npm e dependências particulares para alguns modos.
Ferramentas comerciais de depuração/descompilação exigem licença própria.
O NEXUS CORE não incorpora os arquivos desse ZIP ao repositório, não instala
REA e não executa `npx`/MCP automaticamente.

O REA complementa, mas não substitui, os três editores locais opcionais
PhotoCraft (imagem), PdfCraft (PDF) e WordCraft (documento) já integrados
por adaptadores delimitados. Nem o REA nem o Ollama permitem gerar
automaticamente fotos por IA a partir do nada.

## Modos permitidos nesta etapa

| Modo para o usuário | Comando CLI existente | Extensões admitidas |
| --- | --- | --- |
| `go` | `rea inspect-go-binary` | `.elf`, `.bin`, `.so`, `.exe` |
| `rust` | `rea inspect-rust-binary` | `.elf`, `.bin`, `.so`, `.exe` |
| `dotnet` | `rea inspect-managed-artifact` | `.dll`, `.exe` |
| `electron` | `rea analyze-javascript-application` | `.asar` |

Somente uma operação por mensagem, por caminho absoluto dentro da pasta
pessoal. O `SecurityGate` exige autorização individual de risco médio,
mesmo quando a frase é reconhecida diretamente sem carregar o modelo.

## Controles de recursos e confidencialidade

- Até 16 MiB de dados da origem, aberta com descritor de arquivo regular,
  sem seguir links simbólicos;
- Cópia temporária privada, argumentos fixos e no máximo 45 segundos;
- Saída JSON até 1 MiB após o processo e resumo apenas dos nomes de campos
  ou número de entradas. O resultado completo **não** vai para o chat,
  arquivo de histórico ou logs. O diretório temporário é destruído;
- Ausência do CLI gera mensagem informativa; não dispara instalador,
  `npm`, `npx`, conexão com servidor MCP ou download;
- Formatos/métodos não previstos são recusados.

**Importante:** executar `rea` não é um sandbox. O programa Node.js
externo pode acessar recursos do usuário ou rede. O NEXUS CORE **não
garante** que uma execução do REA seja totalmente offline, nem que
o motor instalado seja seguro ou atualizado. Para artefatos não
confiáveis, execute em ambiente isolado que você tenha homologado
independentemente.

Não estão integrados nesta etapa: análise dinâmica, depuração,
captura de tráfego, Ghidra/Hopper/IDA, conexão com dispositivos,
execução de binários investigados, exploração, bypass de controles,
instalação automática de pontes e comandos de engenharia reversa
arbitrários. A licença MIT do REA não concede licença para
ferramentas comerciais usadas como dependência externa.

## Como testar no Ubuntu

Com internet, se precisar instalar dependências por sua decisão e
seguindo a documentação upstream oficial. Para verificar o que já
está instalado:

```bash
command -v rea
rea --help
node --version
```

Abra o Nexus Core na versão integrada à `main` e solicite:

```text
Analise o binário Rust /home/usuario/Projetos/programa.elf
```

Recuse uma vez e verifique que nenhum processo é iniciado.
Depois autorize com arquivo de teste não sensível. Se o REA não
estiver instalado, a resposta indicará que o componente é opcional.
Não confunda testes simulados de CI com uma inspeção real no notebook.

Para manter o assistente leve, use `NEXUS_RESOURCE_PROFILE=eco` e
encerre serviços locais não usados. **A nova integração não foi
homologada fisicamente e não desbloqueia a release v0.9.12.**
