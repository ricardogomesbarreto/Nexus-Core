#!/usr/bin/env bash
# For the disposable acceptance image only.
set -euo pipefail
limit=$(cat /sys/fs/cgroup/memory.max)
(( limit >= 3999995904 && limit <= 4000004096 ))
test "$(cat /sys/fs/cgroup/memory.swap.max)" = 0
pg_ctlcluster 16 main start
runuser -u postgres -- psql -v ON_ERROR_STOP=1 -c "CREATE ROLE nexus LOGIN PASSWORD 'local-disposable'"
runuser -u postgres -- createdb -O nexus nexus
ollama serve >/tmp/ollama.log 2>&1 &
for attempt in {1..60}; do
  if ollama list >/dev/null 2>&1; then break; fi
  sleep 1
done
ollama pull qwen3:1.7b
timeout 11m xvfb-run -a python3 tests/acceptance/desktop_4gb.py
cat /sys/fs/cgroup/memory.events /sys/fs/cgroup/memory.peak /sys/fs/cgroup/cpu.stat
test "$(awk '$1=="oom_kill"{print $2}' /sys/fs/cgroup/memory.events)" = 0
