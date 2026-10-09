# Nexus Core v0.7.2 — Desktop Interaction Safety & Diagnostics

## Entregas

- `nexus-core --desktop-check` apresenta `ready` e um motivo estável de indisponibilidade, sem conectar ao X11, consultar janela, pressionar tecla ou iniciar banco/modelo.
- O mesmo relatório explicita as quatro ações de navegação disponíveis, o limite de 300 caracteres para digitação e a confirmação por operação. Os campos anteriores permanecem compatíveis.
- Testes verificam sessão X11 local, Wayland/XWayland, display remoto ou ausente e falta do `xdotool`, além da ausência de efeitos durante o diagnóstico.
- Referências históricas a outro provedor foram removidas. A configuração de produção exige PostgreSQL local.
- README e versão do pacote alinhados à v0.7.2, com limites reais de interação, voz e visão preservados.

## Validação e limites

A CI executa a suíte Linux Python 3.12, com PostgreSQL 16, Docker e display virtual. O diagnóstico `ready` descreve pré-requisitos aparentes; não testa autorização X11, janela alvo, foco nem se o aplicativo aceitou o evento sintético. A operação de navegação/digitação ainda requer autorização individual e verificação do ID/título após consentimento. Homologação física em um Linux X11 real, microfone e câmera permanece necessária.

## Próximo marco

v0.7.3 — Desktop Target Integrity (planejado, não implementado).

## Publicação

Tag e release v0.7.2 somente após a CI aprovar o commit exato integrado à `main`.
