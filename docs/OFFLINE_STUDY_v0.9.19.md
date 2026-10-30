# NEXUS CORE — Exercícios offline (etapa inicial v0.9.19)

Esta proposta acrescenta um gerador **determinístico** de questões de lacuna,
com resposta literal e trecho-fonte. É uma implementação original inspirada
nos fluxos educacionais observados no DeepTutor; nenhum código de terceiros
foi copiado.

- Entrada: somente texto explicitamente fornecido pelo chamador.
- Saída: perguntas, respostas literais e trechos de origem.
- Sem acesso a rede, arquivos, câmera, microfone, PostgreSQL ou Ollama.
- Limites: 16.000 caracteres de entrada e 10 questões por chamada.
- Não produz avaliação semântica, não persiste progresso e não substitui o
  sistema de cartões existente na v0.9.18.
- **Ainda não conectado à interface gráfica ou à biblioteca**; exige uma
  etapa posterior com autorização explícita e testes de integração.

Teste previsto: `python -m unittest discover -s tests -p 'test_offline_study.py'`
no ambiente do projeto, com o pacote `nexus_core` disponível no PYTHONPATH.

Integrações de VoiceStudio e NOMAD permanecem separadas; serviços pesados,
downloads de modelos e servidores não devem ser ativados automaticamente.
