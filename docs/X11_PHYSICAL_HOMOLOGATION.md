# Aceite físico X11 — NEXUS CORE v0.7.3

Este documento separa **evidência de CI em Xvfb** de **homologação real no computador Linux do operador**. A CI de PR #11 passou com 952 testes no SHA `b256ab5a` antes da adição deste roteiro, mas não demonstrou que teclas sintéticas funcionam na sessão gráfica física. A integração das versões v0.7.3 e v0.8.0 continua condicionada ao aceite exigido na política de release.

## Pré-requisitos

- Uma sessão **Linux X11 local**, não Wayland nem acesso remoto. Verifique `echo "$XDG_SESSION_TYPE"`; o valor esperado é `x11`. `DISPLAY` deve identificar um display local como `:0`.
- `Python 3.12+`, `python3-tk` e `xdotool` instalados pelo gerenciador de pacotes do Linux.
- Diretório do NEXUS CORE na **branch do PR #11** com dependências locais instaladas. Não executar como `root`.
- Nenhuma senha nem janela com informação sensível deve ser usada. O roteiro cria uma janela Tk temporária que se encerra ao fim.
- É necessário um terminal **interativo**. O script não executa comandos de teclado sem confirmação humana por operação.

## Procedimento

No diretório do projeto:

```bash
nexus-core --desktop-check
python -m scripts.x11_manual_acceptance
```

O programa:

1. Confere os pré-requisitos de sessão X11 local/xdotool.
2. Cria uma janela Tk temporária e busca **somente** a janela com título aleatório gerado pelo processo e com o **mesmo PID**; a consulta exige um único resultado.
3. Revalida ID/título/PID/WM_CLASS e tenta deliberadamente uma requisição com **PID incorreto**. A chamada deve recusar antes de enviar texto.
4. Pede `AUTORIZO` para uma digitação curta de teste, enviada **somente** à janela temporária. Verifica se o campo recebeu exatamente a sequência prevista.
5. Pede **nova** confirmação `AUTORIZO` para enviar **uma única tecla Tab**, verificando foco no segundo campo da mesma janela de teste.
6. Emite um JSON limitado com `identity`, `mismatched_identity_denied`, `typing`, `navigation` e `passed`, sem IDs, capturas de tela, tokens, segredos ou conteúdo privado.

O código usa `xdotool --window` e não altera foco de outras janelas intencionalmente. **O X11 não é uma fronteira de segurança criptográfica:** clientes maliciosos na mesma sessão podem forjar metadados e `xdotool` pode devolver sucesso mesmo se um aplicativo ignorar `XSendEvent`. Por isso o teste confere o **efeito observado no campo e no foco**, não somente o código de retorno do subprocesso.

## Critérios de aceite

| Verificação | Critério |
| --- | --- |
| Sessão local | `--desktop-check` informa `reason=READY` |
| Identificação | Janela descartável é única e tem PID/classe disponíveis |
| Negação da identidade | `mismatched_identity_denied=true` |
| Digitação | `typing=passed` |
| Navegação | `navigation=passed` |
| Evidência completa | `passed=true`, exit code 0 e execução no Linux físico |
| Recusa/falha | `refused`, `failed`, erro ou exit code não zero bloqueiam o aceite |

Uma falha por aplicativo que ignore eventos sintéticos, por ausência de `_NET_WM_PID` ou por WM_CLASS indisponível deve ser **registrada como falha de compatibilidade**, não disfarçada de sucesso. O uso de `xvfb-run` é útil para regressões, mas **não substitui o teste físico**.

## Registro do aceite

O operador pode enviar à revisão do PR #11 somente o **JSON final** emitido pelo teste e um resumo não sensível da sessão (distribuição, desktop X11, versão Python e versão xdotool). Não anexar prints com dados pessoais nem logs de outras janelas.

Até haver esse registro e uma CI novamente aprovada no commit final da `main`, o PR #11 continua em rascunho e a v0.7.3 não pode receber tag/release estável. O PR #12 (v0.8.0) é empilhado e deve ser atualizado e integrado **após** v0.7.3, também com CI própria na `main`.
