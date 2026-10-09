# NEXUS CORE v0.6.0 — Vision & Screen Understanding Foundation

## Entregas

- Entrada visual local sob comando explícito: PNG/JPEG/WEBP do HOME autorizado, captura única de tela via grim/Wayland compatível ou ImageMagick/X11 e câmera via FFmpeg/V4L2.
- Leitura de imagem protegida por descritores, sem seguir symlinks; imagens normalizadas por Pillow para PNG, com descarte de metadados e limites de 6 MiB, 4096 px por lado e 8 megapixels.
- Análise de uma única imagem por vez no Ollama local (API /api/chat em loopback validado) com modelo multimodal configurável e sem ferramentas autônomas do Agent.
- Diagnóstico `nexus-core --vision-check` sem captura ou envio; seleção `--vision-image`, `--vision-screen` ou `--vision-camera N` e pergunta `--vision-question`.
- Testes de entrada inválida, symlink, limite de captura, normalização e payload multimodal sem transmissão real de imagem.

## Limitações

A interface gráfica de visão está prevista para marco posterior; nesta versão a funcionalidade visual é exclusivamente CLI. Não há acesso automático à câmera ou tela, streaming, OCR independente, armazenamento local de capturas, nem conexão a servidores externos. Um modelo Ollama multimodal (ex.: gemma3:4b) deve ser instalado separadamente. A validação de hardware real e permissões de captura do Linux permanece pendente.

## Publicação

A tag v0.6.0 só deve ser criada após a CI do commit exato na branch main passar em Linux com Python 3.12, PostgreSQL 16, Docker, Xvfb e testes com Pillow.
