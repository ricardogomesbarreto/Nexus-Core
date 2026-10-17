#!/usr/bin/env bash
# Nexus Core: explicit start/desktop/status/stop. Never enables boot services.
# Ubuntu/Debian first; systemd distributions with PostgreSQL and Ollama
# services also work. Does not download models, touch config or save secrets.
set -euo pipefail

action="${1:-status}"
case "$action" in start|desktop|status|stop) ;; *)
  printf 'Uso: bash scripts/nexus_core_session.sh {start|desktop|status|stop}\n' >&2
  exit 2 ;;
esac

port="${NEXUS_DATABASE_PORT:-5432}"
if ! [[ "$port" =~ ^[0-9]{1,5}$ ]] || (( 10#$port < 1 || 10#$port > 65535 )); then
  printf 'Porta PostgreSQL inválida.\n' >&2
  exit 2
fi

postgres_unit() {
  if command -v pg_lsclusters >/dev/null 2>&1; then
    local row version cluster
    row="$(pg_lsclusters --no-header 2>/dev/null | awk -v port="$port" '$3 == port {print $1 " " $2; exit}')"
    if [[ -n "$row" ]]; then
      read -r version cluster <<< "$row"
      if [[ "$version" =~ ^[0-9]+$ && "$cluster" =~ ^[a-zA-Z0-9_-]+$ ]]; then
        printf 'postgresql@%s-%s.service\n' "$version" "$cluster"
        return 0
      fi
    fi
  fi
  printf 'postgresql.service\n'
}
pg_unit="$(postgres_unit)"

postgres_ready() {
  command -v pg_isready >/dev/null 2>&1 &&
    pg_isready -q -h 127.0.0.1 -p "$port"
}
ollama_ready() {
  command -v curl >/dev/null 2>&1 &&
    curl --noproxy '*' -fs --connect-timeout 2 --max-time 3 \
      'http://127.0.0.1:11434/api/tags' >/dev/null 2>&1
}
wait_for_ollama() {
  local attempt deadline=$((SECONDS + 30))
  for ((attempt=0; attempt<30 && SECONDS<deadline; attempt++)); do
    if ollama_ready; then return 0; fi
    if ((SECONDS >= deadline)); then break; fi
    sleep 1
  done
  return 1
}
has_service() {
  local name="$1"
  systemctl cat "$name" >/dev/null 2>&1
}

start_services() {
  if ! postgres_ready; then
    if command -v systemctl >/dev/null 2>&1 && has_service "$pg_unit"; then
      printf '[SERVIÇO] Iniciando PostgreSQL em %s (%s)\n' "$port" "$pg_unit"
      sudo systemctl start "$pg_unit"
    else
      printf '[ERRO] PostgreSQL na porta %s indisponível. Inicie manualmente conforme a sua distro.\n' "$port" >&2
      return 1
    fi
  fi
  if ! postgres_ready; then
    printf '[ERRO] PostgreSQL não respondeu na porta %s. Verifique pg_lsclusters e pg_isready.\n' "$port" >&2
    return 1
  fi
  printf '[SERVIÇO] PostgreSQL local: pronto.\n'
  if ! ollama_ready; then
    if command -v systemctl >/dev/null 2>&1 && has_service ollama.service; then
      printf '[SERVIÇO] Iniciando Ollama local\n'
      sudo systemctl start ollama.service
    elif command -v systemctl >/dev/null 2>&1 &&
         systemctl --user cat nexus-core-ollama.service >/dev/null 2>&1; then
      printf '[SERVIÇO] Iniciando Ollama do usuário\n'
      systemctl --user start nexus-core-ollama.service
    else
      printf '[ERRO] Serviço Ollama não encontrado. Em outro terminal execute: ollama serve\n' >&2
      return 1
    fi
  fi
  if ! wait_for_ollama; then
    printf '[ERRO] Ollama não respondeu em 127.0.0.1:11434 após 30 segundos. Confira systemctl status ollama.\n' >&2
    return 1
  fi
  printf '[SERVIÇO] Ollama local: pronto.\n'
}

if [[ "$action" == "status" ]]; then
  printf '[NEXUS] PostgreSQL unidade=%s porta=%s\n' "$pg_unit" "$port"
  if postgres_ready; then printf '[NEXUS] PostgreSQL: pronto\n'
  else printf '[NEXUS] PostgreSQL: indisponível\n'; fi
  if ollama_ready; then printf '[NEXUS] Ollama: pronto\n'
  else printf '[NEXUS] Ollama: indisponível\n'; fi
elif [[ "$action" == "start" || "$action" == "desktop" ]]; then
  start_services
  if [[ "$action" == "desktop" ]]; then
    executable="${HOME}/.local/bin/nexus-core"
    if [[ ! -x "$executable" ]]; then
      printf '[ERRO] Nexus Core não encontrado: %s. Execute python3 scripts/install_linux.py.\n' "$executable" >&2
      exit 1
    fi
    exec "$executable" --desktop
  fi
else
  if command -v systemctl >/dev/null 2>&1; then
    if has_service ollama.service; then
      sudo systemctl stop ollama.service
    elif systemctl --user cat nexus-core-ollama.service >/dev/null 2>&1; then
      systemctl --user stop nexus-core-ollama.service
    fi
    if has_service "$pg_unit"; then
      sudo systemctl stop "$pg_unit"
    fi
  fi
  printf '[SERVIÇO] Solicitação de parada concluída. Os serviços continuam instalados.\n'
fi
