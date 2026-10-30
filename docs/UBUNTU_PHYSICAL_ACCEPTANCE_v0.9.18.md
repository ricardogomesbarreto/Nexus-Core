# Aceite físico complementar — Nexus Core 0.9.18

Este roteiro acrescenta o estudo local e a prévia de voz aos
[gates físicos anteriores](UBUNTU_PHYSICAL_ACCEPTANCE_v0.9.17.md). Não afirma
que a versão 0.9.18 foi homologada no notebook. Use o SHA da `main` e a
versão instalada para evitar testar um executável antigo.

```bash
cd "$HOME/Projetos/Nexus-Core"
git switch main && git pull --ff-only
git rev-parse HEAD
python3 scripts/install_linux.py
~/.local/bin/nexus-core --version
NEXUS_RESOURCE_PROFILE=eco python3 scripts/observe_desktop.py
```

Na janela, abra **Recursos → Biblioteca local**, importe um `.txt` ou `.md`
próprio (até 256 KiB), pesquise uma palavra presente e escolha **Criar cartão
do 1º trecho**. Escreva uma pergunta e copie uma resposta literal que esteja
no trecho exibido. Confirme o salvamento; em **Revisar cartões**, selecione a
pergunta, mostre a resposta e clique **Acertei**. Confira que ela sai da lista
de revisões imediatas. Faça outro cartão e clique **Repetir**; a revisão volta
após 10 minutos. Uma resposta que não conste da fonte deve falhar sem criar
cartão. Exclua o documento e confirme que seus cartões desaparecem.

Em **Testes locais → Voz: ouvir seleção atual**, escolha primeiro Feminina,
depois Masculina. Confira som, pausa da escuta durante a reprodução, retomada
após a fala e respeito à opção **Responder em voz** desligada. Isso testa a
seleção, não a naturalidade da voz nem as duas perguntas consecutivas.

Continue os testes de voz contínua, câmera, RAM/swap, permissões, arquivos
reais, serviços e restauração do roteiro 0.9.17. Após fechar a janela:

```bash
bash scripts/nexus_core_session.sh start
~/.local/bin/nexus-core --acceptance-log
bash scripts/nexus_core_session.sh stop
```

Marque `n` para o que não executou e `f` para falha observada. Um registro
`RELATADO` não é aprovação automática. CI verde do SHA da PR e testes locais
não substituem aceite físico e CI de `push` do SHA final da `main`; a release
estável continua bloqueada até o fechamento desses gates.
