# Nexus Core v0.9.21-rc.2

O texto começa a aparecer com o primeiro fragmento. Durante uma rajada, o transporte agrega os fragmentos e atualiza a prévia em intervalos de 80 ms. O último trecho é entregue ao concluir. O monitor de sessão calcula os picos de RAM e swap sem acumular amostras na memória.

O teste de desktop executa a janela Tk, PostgreSQL e Ollama com qwen3:1.7b em um contêiner Ubuntu sob limite compartilhado de 4 GB, duas CPUs e sem swap. Verifica perguntas consecutivas, cancelamento, nova pergunta e encerramento. Voz, câmera, Wayland e desempenho no notebook físico precisam de homologação separada.
