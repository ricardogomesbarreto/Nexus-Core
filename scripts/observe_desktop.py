#!/usr/bin/env python3
"""Run the installed desktop session and print coarse, local resource samples.

This is a measurement aid, not a benchmark or automatic hardware acceptance.
Only numeric process and memory data are printed; desktop runtime logs remain
on the terminal. Nothing is saved, downloaded or sent to an external service.
"""

import argparse
import os
from pathlib import Path
import subprocess
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from nexus.platforms.resources import inspect_resources  # noqa: E402


def _children(pid: int) -> list[int]:
    try:
        text = Path(f"/proc/{pid}/task/{pid}/children").read_text(encoding="ascii")
        return [int(value) for value in text.split() if value.isdecimal()]
    except OSError:
        return []


def _rss_kib(pid: int) -> int | None:
    try:
        for line in Path(f"/proc/{pid}/status").read_text(encoding="ascii").splitlines():
            if line.startswith("VmRSS:"):
                parts = line.split()
                if len(parts) == 3 and parts[1].isdecimal() and parts[2] == "kB":
                    return min(int(parts[1]), 1 << 40)
    except OSError:
        pass
    return None


def _tree_rss_mib(pid: int) -> int | None:
    """Sum resident memory of the session script and at most 256 descendants."""
    pending, visited, total, found = [pid], set(), 0, False
    while pending and len(visited) < 256:
        current = pending.pop()
        if current in visited:
            continue
        visited.add(current)
        pending.extend(child for child in _children(current)
                       if child not in visited and len(pending) < 256)
        rss = _rss_kib(current)
        if rss is not None:
            total += rss
            found = True
    return total // 1024 if found else None


def _number(value: object) -> str:
    return str(value) if type(value) is int and 0 <= value <= 1_000_000 else "indisponivel"


def _sample(pid: int, *, elapsed: int, inspect=inspect_resources,
            rss=_tree_rss_mib) -> dict[str, int | None]:
    snapshot = inspect()
    memory, ollama = snapshot.get("memory", {}), snapshot.get("ollama", {})
    numbers = {
        "ram_disponivel_mib": memory.get("available_mib") if memory.get("status") == "available" else None,
        "swap_usada_mib": memory.get("swap_used_mib") if memory.get("status") == "available" else None,
        "modelos_carregados": ollama.get("loaded_models") if ollama.get("status") == "available" else None,
        "nexus_rss_mib": rss(pid),
    }
    print("[MEDICAO-LOCAL] " + " ".join(
        [f"tempo_s={max(0, elapsed)}"] + [f"{key}={_number(value)}" for key, value in numbers.items()]
    ), flush=True)
    return numbers


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Mede a sessão desktop local do Nexus Core.")
    parser.add_argument("--interval", type=int, default=10, metavar="SEGUNDOS")
    arguments = parser.parse_args(argv)
    if not 2 <= arguments.interval <= 60:
        parser.error("--interval deve estar entre 2 e 60 segundos")
    launcher = ROOT / "scripts" / "nexus_core_session.sh"
    print("[MEDICAO-LOCAL] Iniciando sessão desktop; feche a janela para obter o resumo. ",
          "RSS soma processos da sessão; Ollama/PostgreSQL são medidos pela memória geral. ",
          "Nenhuma amostra avalia qualidade de resposta ou ausência de travamento.",
          sep="", flush=True)
    start = time.monotonic()
    try:
        process = subprocess.Popen(["bash", str(launcher), "desktop"], cwd=ROOT,
                                   env=os.environ.copy())
    except OSError:
        print("[MEDICAO-LOCAL] Não foi possível iniciar a sessão.", file=sys.stderr)
        return 1
    samples: list[dict[str, int | None]] = []
    try:
        while process.poll() is None:
            samples.append(_sample(process.pid, elapsed=int(time.monotonic() - start)))
            try:
                process.wait(timeout=arguments.interval)
            except subprocess.TimeoutExpired:
                pass
    except KeyboardInterrupt:
        # The terminal also delivers Ctrl+C to the child shell, whose EXIT
        # handler releases only the services recorded as started by Nexus.
        try:
            process.wait(timeout=20)
        except subprocess.TimeoutExpired:
            print("[MEDICAO-LOCAL] Sessão ainda ativa; feche a janela normalmente.",
                  file=sys.stderr)
            return 130
    elapsed = int(time.monotonic() - start)
    peak_swap = max((item["swap_usada_mib"] for item in samples
                     if type(item["swap_usada_mib"]) is int), default=None)
    peak_rss = max((item["nexus_rss_mib"] for item in samples
                    if type(item["nexus_rss_mib"]) is int), default=None)
    min_available = min((item["ram_disponivel_mib"] for item in samples
                         if type(item["ram_disponivel_mib"]) is int), default=None)
    print("[MEDICAO-LOCAL] resumo "
          f"duracao_s={elapsed} amostras={len(samples)} "
          f"ram_disponivel_min_mib={_number(min_available)} "
          f"swap_usada_max_mib={_number(peak_swap)} "
          f"nexus_rss_max_mib={_number(peak_rss)} "
          f"codigo_saida={process.returncode}", flush=True)
    return process.returncode if process.returncode is not None else 130


if __name__ == "__main__":
    raise SystemExit(main())
