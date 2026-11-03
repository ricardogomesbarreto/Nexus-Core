# NEXUS CORE v0.9.19 — Fedora Workstation (pré-homologação)

**Estado:** implementação em PR #102, sem publicação. A instalação foi
adaptada para Fedora **43, 44 e 45** desktop (x86_64 e outras arquiteturas
somente quando dependências e modelos forem suportados). **Não afirmar
compatibilidade total sem teste físico Fedora**. As versões anteriores à 43,
Rawhide ou derivadas que apenas declaram `ID_LIKE=fedora` continuam sem
instalador mutável autorizado.

## O que mudou

- Reconhecimento estrito de `ID=fedora`, `VERSION_ID` entre 43 e 45, Python
  3.12 ou superior, sessão gráfica X11 ou Wayland.
- Instalador existente `scripts/install_linux.py` passa a selecionar **dnf**
  para Fedora e **apt-get** para Ubuntu, sem misturar comandos.
- Pacotes Fedora necessários incluem `python3`, `python3-pip`,
  `python3-tkinter`, `postgresql`, `postgresql-server`, `espeak-ng`,
  `alsa-utils`, `ffmpeg-free`, `xdg-utils`, `gtk3` e `util-linux`;
  `ollama` é instalado separadamente mediante consentimento quando ausente.
- O instalador só tenta alterar pacotes **após confirmação interativa**.
  É proibido executar como root.
- PostgreSQL no Fedora utiliza `postgresql.service` sob demanda. O script
  **não executa initdb**, não apaga diretórios do banco, não modifica
  `pg_hba.conf` e não habilita unidades no boot.
- Ollama usa o RPM Fedora ou serviço já existente. Downloads de modelos
  de linguagem, reconhecimento Vosk ou voz Piper exigem autorização individual.
  A voz eSpeak continua como fallback sem dependência de RHVoice Ubuntu.
- O ambiente `venv` é privado no HOME; verificações isoladas de versão, pip
  e plataforma precedem ativação. Login PostgreSQL local é testado somente
  leitura. A atualização preserva o runtime anterior quando uma verificação
  falha.
- O script de sessão usa `postgresql.service` quando `pg_lsclusters`
  (característico de Debian/Ubuntu) não está instalado. A parada só tenta
  serviços que o Nexus iniciou e cujas identidades foram registradas.

## Instalar Fedora 43–45

Na pasta clonada do projeto (não execute scripts desconhecidos):

~~~bash
cd "$HOME/Projetos/Nexus-Core"
python3 scripts/install_linux.py --check
python3 scripts/install_linux.py
~~~

O instalador solicita autorização para pacotes e modelos. **Em instalação
nova**, se o serviço PostgreSQL recusar iniciar por não possuir cluster
inicializado, confira antes que `/var/lib/pgsql/data` não tenha dados
existentes. Somente para um cluster realmente novo:

~~~bash
sudo postgresql-setup --initdb
~~~

Esse comando é de inicialização de banco e **não deve ser repetido em um
banco existente**. Ele nunca é executado automaticamente pelo Nexus.
Depois:

~~~bash
sudo systemctl start postgresql.service
python3 scripts/install_linux.py
~~~

O instalador poderá criar um banco e usuário dedicados mediante confirmação
e salvar apenas credenciais locais privadas (0600). Não ativar
`systemctl enable` para PostgreSQL, Ollama ou Docker.

Se precisar instalar dependências manualmente, os nomes devem ser verificados
para a versão instalada:

~~~bash
sudo dnf install python3 python3-pip python3-tkinter \
    postgresql postgresql-server espeak-ng alsa-utils \
    ffmpeg-free xdg-utils gtk3 util-linux ollama
~~~

O `ffmpeg-free` possui codecs limitados; formatos de áudio que dependam
de codecs não incluídos podem falhar de forma controlada. O suporte a
Piper/RHVoice depende de pacotes/modelos realmente disponíveis, sem instalação
de componentes Ubuntu no Fedora.

## Uso e diagnóstico

~~~bash
~/.local/bin/nexus-core --platform-check
~/.local/bin/nexus-core --linux-doctor
~/.local/bin/nexus-core --linux-preflight
~/.local/bin/nexus-core --resource-check

bash scripts/nexus_core_session.sh start
NEXUS_RESOURCE_PROFILE=auto bash scripts/nexus_core_session.sh desktop
bash scripts/nexus_core_session.sh stop
~~~

Os nomes antigos `--ubuntu-doctor` e `--ubuntu-preflight` continuam
aceitos; o relatório preserva seus identificadores de schema por
retrocompatibilidade. Os diagnósticos não representam testes de hardware.
Se o Ollama/PostgreSQL já estava ativo antes da sessão, a parada do Nexus
**não deve** desligar esse serviço.

## Limites por funcionalidade

| Área | Compatibilidade prevista | Limitações atuais |
|---|---|---|
| Chat Ollama e PostgreSQL | Adaptado para Fedora | Exige modelos instalados, banco autenticado e RAM |
| Voz Vosk/eSpeak/Piper | Adaptado; fallback espeak | Microfone, PipeWire/ALSA e pacotes opcionais exigem teste real |
| Interface Tk | Adaptada, X11 e Wayland | Automação por xdotool somente X11 |
| Biblioteca e cursos nativos | Python + PostgreSQL local | Não é Kiwix/Kolibri completo |
| ZIM/Kiwix | Leitura pontual opcional via zimdump | Depende de zim-tools instalado |
| Mapas ProtoMaps | Mosaicos raster PMTiles locais | Sem mapas vetoriais completos ou download automático |
| CyberChef/FlatNotes | Operações e notas nativas | Ferramentas originais não integradas |
| Benchmark e Docker sandbox | Recursos locais opcionais | Não há leaderboard, Supply Depot ou Podman integrado |

## Aceite obrigatório antes de declarar estável

1. Testar instalação nova Fedora 43/44/45, pacote Tk e venv privado.
2. Confirmar inicialização segura do PostgreSQL, autenticação e preservação
   de um cluster preexistente.
3. Testar Ollama local, eSpeak, Piper quando disponível, Vosk, câmera,
   Wayland/X11 e permissões de dispositivos.
4. Medir RAM/swap, PSS, CPU e latência em equipamentos de 4/8/16 GiB,
   com modelos adequados a cada classe.
5. Verificar encerramento de processos e serviços, inclusive sem sudo
   armazenado e com serviços preexistentes de outros aplicativos.
6. Aprovar CI e testes de regressão do **SHA final do PR**. CI Ubuntu/Linux
   com testes simulados Fedora **não substitui Fedora real**.

**Sem recursos pagos, sem downloads automáticos e sem autostart de serviços.**
