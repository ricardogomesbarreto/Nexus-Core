"""Medição voluntária e limitada de CPU, sem rede ou gravação em disco."""
import hashlib
from time import perf_counter


def benchmark_cpu(duration_ms: int = 400) -> dict:
    if type(duration_ms) is not int or not 200 <= duration_ms <= 1500:
        raise ValueError("Duração deve ficar entre 200 e 1500 ms.")
    payload = bytes(1024 * 1024)
    start = perf_counter()
    deadline = start + duration_ms / 1000
    loops = 0
    while perf_counter() < deadline:
        hashlib.sha256(payload).digest()
        loops += 1
    elapsed = perf_counter() - start
    return {
        "schema": "nexus.benchmark.v1", "mode": "explicit_local",
        "cpu_hash_mib_per_s": round(loops / elapsed, 1),
        "elapsed_ms": round(elapsed * 1000), "bytes_per_iteration": len(payload),
        "external_network_used": False, "disk_written": False,
        "leaderboard_uploaded": False,
        "notice": "Taxa local de SHA-256; não representa desempenho geral nem temperatura.",
    }


def benchmark_local(duration_ms: int = 400) -> dict:
    """Opt-in bounded CPU and memory-copy measurements, without disk or network.

    Rates are observational and must not be compared with a global leaderboard.
    """
    if type(duration_ms) is not int or not 200 <= duration_ms <= 1500:
        raise ValueError("Duração deve ficar entre 200 e 1500 ms.")
    cpu = benchmark_cpu(duration_ms)
    block = bytes(4 * 1024 * 1024)
    target = bytearray(len(block))
    start = perf_counter()
    end = start + duration_ms / 1000
    loops = 0
    while perf_counter() < end:
        target[:] = block
        loops += 1
    elapsed = perf_counter() - start
    return {
        "schema": "nexus.benchmark.v2", "mode": "explicit_local",
        "cpu_hash_mib_per_s": cpu["cpu_hash_mib_per_s"],
        "memory_copy_mib_per_s": round(loops * 4 / elapsed, 1),
        "elapsed_ms": round((elapsed + cpu["elapsed_ms"] / 1000) * 1000),
        "peak_working_buffer_mib": 8,
        "external_network_used": False, "disk_written": False,
        "leaderboard_uploaded": False,
        "notice": "Medições locais indicativas de SHA-256 e cópia em RAM; não medem temperatura nem desempenho geral.",
    }
