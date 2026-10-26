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

# Only a service started by this user's Nexus session can later be stopped.
# The runtime directory is private and disappears on reboot; InvocationID
# also prevents a stale record from stopping a service restarted elsewhere.
state_dir="${XDG_RUNTIME_DIR:-}/nexus-core"
state_file="$state_dir/started-services"
prepare_state() {
  local runtime="${XDG_RUNTIME_DIR:-}"
  if [[ -z "$runtime" || ! -d "$runtime" || -L "$runtime" || ! -O "$runtime" ]]; then
    printf '[ERRO] XDG_RUNTIME_DIR privado indisponível; não é seguro gerenciar a parada dos serviços.\n' >&2
    return 1
  fi
  if [[ -L "$state_dir" ]]; then return 1; fi
  if [[ ! -d "$state_dir" ]]; then
    (umask 077; mkdir -m 700 -- "$state_dir") || return 1
  fi
  if [[ ! -O "$state_dir" || "$(stat -c %a -- "$state_dir")" != 700 ||
        -L "$state_file" || ( -e "$state_file" &&
          ( ! -f "$state_file" || ! -O "$state_file" || "$(stat -c %a -- "$state_file")" != 600 ) ) ]]; then
    printf '[ERRO] Estado privado da sessão inválido.\n' >&2
    return 1
  fi
}
service_active() {
  local scope="$1" unit="$2"
  if [[ "$scope" == user ]]; then systemctl --user is-active --quiet "$unit" 2>/dev/null
  else systemctl is-active --quiet "$unit" 2>/dev/null; fi
}
invocation_id() {
  local scope="$1" unit="$2" value
  if [[ "$scope" == user ]]; then
    value="$(systemctl --user show "$unit" --property=InvocationID --value 2>/dev/null)"
  else
    value="$(systemctl show "$unit" --property=InvocationID --value 2>/dev/null)"
  fi
  if [[ "$value" =~ ^[a-fA-F0-9]{32}$ ]]; then printf '%s\n' "$value"; fi
}
record_started() {
  local scope="$1" unit="$2" identity
  identity="$(invocation_id "$scope" "$unit")"
  if [[ -z "$identity" ]]; then
    printf '[ERRO] Serviço %s iniciou, mas não foi possível registrar sua identidade; não o pararei automaticamente.\n' "$unit" >&2
    return 1
  fi
  (umask 077; printf '%s\t%s\t%s\n' "$scope" "$unit" "$identity" >> "$state_file")
}

start_services() {
  if ! postgres_ready; then
    if command -v systemctl >/dev/null 2>&1 && has_service "$pg_unit"; then
      if ! service_active system "$pg_unit"; then
        prepare_state
        printf '[SERVIÇO] Iniciando PostgreSQL em %s (%s)\n' "$port" "$pg_unit"
        sudo systemctl start "$pg_unit"
        record_started system "$pg_unit"
      fi
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
      if ! service_active system ollama.service; then
        prepare_state
        printf '[SERVIÇO] Iniciando Ollama local\n'
        sudo systemctl start ollama.service
        record_started system ollama.service
      fi
    elif command -v systemctl >/dev/null 2>&1 &&
         systemctl --user cat nexus-core-ollama.service >/dev/null 2>&1; then
      if ! service_active user nexus-core-ollama.service; then
        prepare_state
        printf '[SERVIÇO] Iniciando Ollama do usuário\n'
        systemctl --user start nexus-core-ollama.service
        record_started user nexus-core-ollama.service
      fi
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
  if [[ "$action" == "desktop" ]]; then
    # Also release services if the installed launcher fails or the GUI exits
    # without reaching its Python cleanup. The stop action is idempotent.
    cleanup_desktop() {
      local exit_status=$?
      trap - EXIT
      NEXUS_STOP_NONINTERACTIVE=1 bash "$0" stop || true
      exit "$exit_status"
    }
    trap cleanup_desktop EXIT
  fi
  start_services
  if [[ "$action" == "desktop" ]]; then
    executable="${HOME}/.local/bin/nexus-core"
    if [[ ! -x "$executable" ]]; then
      printf '[ERRO] Nexus Core não encontrado: %s. Execute python3 scripts/install_linux.py.\n' "$executable" >&2
      exit 1
    fi
    "$executable" --desktop
  fi
else
  prepare_state
  # A second invocation (including the fallback EXIT trap) must not stop
  # services while another GUI process still holds its desktop lease.
  lease_file="$state_dir/desktop.lock"
  if [[ -L "$lease_file" || ( -e "$lease_file" &&
        ( ! -f "$lease_file" || ! -O "$lease_file" || "$(stat -c %a -- "$lease_file")" != 600 ) ) ]]; then
    printf '[ERRO] Trava privada da sessão inválida.\n' >&2
    exit 1
  fi
  (umask 077; : >> "$lease_file")
  if ! command -v flock >/dev/null 2>&1; then
    printf '[ERRO] flock indisponível para parada segura da sessão.\n' >&2
    exit 1
  fi
  exec {lease_fd}<> "$lease_file"
  if ! flock -n "$lease_fd"; then
    printf '[SERVIÇO] Outra janela do Nexus ativa; parada adiada.\n'
    exit 0
  fi
  if [[ -f "$state_file" ]]; then
    remaining="$(mktemp "$state_dir/.remaining.XXXXXX")"
    mapfile -t started < "$state_file"
    for ((index=${#started[@]}-1; index>=0; index--)); do
      IFS=$'\t' read -r scope unit identity <<< "${started[index]}"
      if [[ ! "$identity" =~ ^[a-fA-F0-9]{32}$ ]] ||
         { [[ "$scope" != system || "$unit" != ollama.service && "$unit" != "$pg_unit" ]] &&
           [[ "$scope" != user || "$unit" != nexus-core-ollama.service ]]; }; then
        continue
      fi
      if service_active "$scope" "$unit" && [[ "$(invocation_id "$scope" "$unit")" == "$identity" ]]; then
        printf '[SERVIÇO] Parando instância iniciada pelo Nexus: %s\n' "$unit"
        if [[ "$scope" == user ]]; then
          if ! systemctl --user stop "$unit"; then printf '%s\t%s\t%s\n' "$scope" "$unit" "$identity" >> "$remaining"; fi
        else
          if [[ "${NEXUS_STOP_NONINTERACTIVE:-0}" == 1 ]]; then
            if ! sudo -n systemctl stop "$unit"; then
              printf '[SERVIÇO] Sem autorização sudo em cache para parar %s; rode stop manualmente.\n' "$unit" >&2
              printf '%s\t%s\t%s\n' "$scope" "$unit" "$identity" >> "$remaining"
            fi
          elif ! sudo systemctl stop "$unit"; then
            printf '%s\t%s\t%s\n' "$scope" "$unit" "$identity" >> "$remaining"
          fi
        fi
      fi
    done
    if [[ -s "$remaining" ]]; then mv -- "$remaining" "$state_file"
    else rm -f -- "$remaining" "$state_file"; fi
  fi
  printf '[SERVIÇO] Parada das instâncias registradas concluída; outros serviços preservados.\n'
fi
