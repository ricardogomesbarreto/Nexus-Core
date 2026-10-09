# Nexus Line — Nexus Core

O Nexus Core adota a família visual **Nexus Line** com uma extensão própria para inteligência artificial local, controle operacional e segurança. O logotipo PNG já é utilizado no cabeçalho da janela Tk a partir da v0.3.9. Os sprites e ícones SVG permanecem como catálogo para futuras integrações, sem antecipar funcionalidades não implementadas.

## Identidade da aplicação

- **Desktop Application:** Native
- **Web Application:** No
- **Primary Platform:** Linux
- **Primary Visual Identity:** Wine Red
- **Primary Color:** `#722F37`

O Nexus Core é projetado como aplicação desktop nativa. O uso de HTML no `README.md` existe exclusivamente para renderização da documentação no GitHub e não define uma arquitetura de aplicação web.

## Contrato visual

| Propriedade | Padrão |
|---|---|
| Grade | `24 × 24` |
| Traço | `1.75` |
| Terminações e junções | arredondadas |
| Cor na interface | `currentColor` |
| Preenchimento | nenhum, salvo a marca |
| Formato | SVG local, sem fonte ou CDN externa |

A marca utiliza vinho `#722F37`, variações `#A86B76` e superfície `#F7F2F3`. Gradientes pertencem somente à marca; ícones funcionais são monocromáticos.

## Vocabulário do Core

O sprite [`assets/icons/nexus-core-icons.svg`](../assets/icons/nexus-core-icons.svg) contém 20 símbolos autorais:

- inteligência: núcleo, agente, modelo, roteador, memória e conhecimento;
- interação: voz, visão e conectividade;
- operação: runtime, ferramentas, terminal, eventos, configurações e saúde;
- confiança: segurança, offline e auditoria;
- infraestrutura: banco de dados e nós distribuídos.

O catálogo legível por ferramentas está em [`assets/icons/manifest.json`](../assets/icons/manifest.json). A marca vetorial está em [`assets/brand/nexus-core-mark.svg`](../assets/brand/nexus-core-mark.svg).

## Desktop Visual Identity Foundation

A fundação visual desktop adiciona os seguintes assets:

- [`assets/brand/nexus-core-logo.png`](../assets/brand/nexus-core-logo.png) — logotipo horizontal oficial com transparência;
- [`assets/icons/nexus-core.svg`](../assets/icons/nexus-core.svg) — application icon;
- [`assets/icons/nexus-core-symbolic.svg`](../assets/icons/nexus-core-symbolic.svg) — symbolic icon;
- [`assets/icons/desktop-manifest.json`](../assets/icons/desktop-manifest.json) — catálogo dos ícones desktop;
- [`assets/icons/ui/`](../assets/icons/ui/) — conjunto essencial de 18 ícones para a futura interface nativa.

Os 18 ícones UI são: `add`, `attention`, `back`, `close`, `confirm`, `credentials`, `delete`, `edit`, `forward`, `history`, `menu`, `notifications`, `overview`, `profile`, `protected-access`, `refresh`, `search` e `system`.

## Uso atual e futuro na interface desktop nativa

A janela Tk atual carrega o logotipo PNG local `assets/brand/nexus-core-logo.png` sem um runtime web. Os arquivos SVG são assets vetoriais locais destinados à integração posterior nos controles da interface desktop nativa.

A camada de interface deverá carregar e renderizar esses assets diretamente por meio do toolkit gráfico adotado para o desktop, sem navegador, servidor web, Electron, React ou framework web.

A iconografia deve preservar proporção, legibilidade, significado semântico e consistência visual em diferentes escalas de interface.

Controles apenas visuais devem receber identificação acessível. Situações críticas não podem depender apenas de cor ou ícone.

## Coerência entre produtos

Ações genéricas devem conservar o significado da Nexus Line. Extensões refletem o domínio: ERP usa operações empresariais, Nutra usa cuidado nutricional, Core usa IA local e segurança, e ADV terá vocabulário jurídico quando existir um repositório próprio.
