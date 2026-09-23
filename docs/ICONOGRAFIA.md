# Nexus Line — Nexus Core

O Nexus Core adota a família visual **Nexus Line** com uma extensão própria para inteligência artificial local, controle operacional e segurança. Estes ativos preparam a futura interface nativa sem antecipar funcionalidades ainda não implementadas.

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

## Uso futuro em uma interface SVG

```html
<svg class="nexus-icon" aria-hidden="true">
  <use href="/assets/icons/nexus-core-icons.svg#icon-agent"></use>
</svg>
```

```css
.nexus-icon {
  width: 24px;
  height: 24px;
  fill: none;
  stroke: currentColor;
  stroke-width: 1.75;
  stroke-linecap: round;
  stroke-linejoin: round;
}
```

Controles apenas visuais devem receber nome acessível no botão. Situações críticas não podem depender apenas de cor ou ícone.

## Coerência entre produtos

Ações genéricas devem conservar o significado da Nexus Line. Extensões refletem o domínio: ERP usa operações empresariais, Nutra usa cuidado nutricional, Core usa IA local e segurança, e ADV terá vocabulário jurídico quando existir um repositório próprio.
