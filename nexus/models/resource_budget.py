"""Bounded offline inference budgets based on the actual Linux machine.

No downloads, no elevated privileges, no network and no changes to system CPU
frequency. Runtime memory limits (cgroup/container) are respected when known.
"""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


_GIB = 1024 ** 3


def _positive_int(text: str) -> int | None:
    try:
        number = int(text.strip())
    except (ValueError, TypeError):
        return None
    return number if 0 < number < 1 << 60 else None


def _read_positive(path: str) -> int | None:
    try:
        return _positive_int(Path(path).read_text(encoding="ascii"))
    except (OSError, ValueError):
        return None


def _memory_bytes() -> tuple[int | None, int | None]:
    """Use the smallest active Linux memory cap, including cgroup v1/v2.

    The process must never budget against the host's free RAM when it is
    constrained by a much smaller container/systemd memory allowance.
    """
    total = available = None
    try:
        for line in Path("/proc/meminfo").read_text(encoding="ascii").splitlines():
            if line.startswith("MemTotal:"):
                total = _positive_int(line.split(":", 1)[1].split()[0])
            elif line.startswith("MemAvailable:"):
                available = _positive_int(line.split(":", 1)[1].split()[0])
    except (OSError, ValueError):
        pass
    if total is not None:
        total *= 1024
    if available is not None:
        available *= 1024

    # v1 often reports a near-2**63 sentinel for an unlimited container.
    # Discard implausible values and combine every *real* cap conservatively.
    caps = (
        ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory.current"),
        ("/sys/fs/cgroup/memory/memory.limit_in_bytes",
         "/sys/fs/cgroup/memory/memory.usage_in_bytes"),
    )
    for limit_path, usage_path in caps:
        limit = _read_positive(limit_path)
        if limit is None or limit >= (1 << 60):
            continue
        if total is None or limit < total:
            total = limit
        usage = _read_positive(usage_path)
        if usage is not None:
            remaining = max(0, limit - usage)
            available = min(available, remaining) if available is not None else remaining
        elif available is not None:
            available = min(available, limit)
    if total is not None and available is not None:
        available = min(total, available)
    return total, available


def _cpu_quota_cores() -> int | None:
    """Read CPU quotas; never change frequencies, priorities or CPU affinity."""
    try:
        parts = Path("/sys/fs/cgroup/cpu.max").read_text(encoding="ascii").split()
        if len(parts) == 2 and parts[0] != "max":
            quota = _positive_int(parts[0])
            period = _positive_int(parts[1])
            if quota is not None and period is not None:
                return max(1, (quota + period - 1) // period)
    except (OSError, ValueError):
        pass
    quota = _read_positive("/sys/fs/cgroup/cpu/cpu.cfs_quota_us")
    period = _read_positive("/sys/fs/cgroup/cpu/cpu.cfs_period_us")
    if quota is not None and period is not None:
        return max(1, (quota + period - 1) // period)
    return None


def _logical_cores() -> int:
    try:
        affinity = (max(1, len(os.sched_getaffinity(0)))
                    if hasattr(os, "sched_getaffinity")
                    else max(1, os.cpu_count() or 1))
    except OSError:
        affinity = max(1, os.cpu_count() or 1)
    quota = _cpu_quota_cores()
    return min(affinity, quota) if quota is not None else affinity

@dataclass(frozen=True)
class ResourceBudget:
    mode: str
    total_ram_mib: int | None
    available_ram_mib: int | None
    num_thread: int
    text_context: int
    text_predict: int
    vision_context: int
    vision_predict: int
    vision_edge: int
    keep_alive: str

    @staticmethod
    def available_now_mib() -> int | None:
        """Recheck current pressure before inference, not just at startup."""
        _total, available = _memory_bytes()
        return available // (1024 * 1024) if available is not None else None

    def text_memory_low(self) -> bool:
        available = self.available_now_mib()
        return self.mode == "eco" and available is not None and available < 1024

    @classmethod
    def detect(cls, *, requested: str | None = None,
               total_bytes: int | None = None,
               available_bytes: int | None = None,
               cores: int | None = None) -> ResourceBudget:
        setting = requested if requested is not None else os.environ.get(
            "NEXUS_RESOURCE_PROFILE", "auto")
        if setting not in ("auto", "eco", "balanced"):
            raise ValueError("NEXUS_RESOURCE_PROFILE deve ser auto, eco ou balanced.")
        if total_bytes is None or available_bytes is None:
            actual_total, actual_available = _memory_bytes()
            if total_bytes is None:
                total_bytes = actual_total
            if available_bytes is None:
                available_bytes = actual_available
        count = _logical_cores() if cores is None else max(1, int(cores))
        low_memory = (
            (total_bytes is not None and total_bytes <= 8 * _GIB)
            or (available_bytes is not None and available_bytes <= 2 * _GIB)
        )
        mode = ("eco" if low_memory else "balanced") if setting == "auto" else setting
        if mode == "eco":
            return cls(
                mode, total_bytes // (1024 * 1024) if total_bytes else None,
                available_bytes // (1024 * 1024) if available_bytes is not None else None,
                min(count, 2), 1024, 160, 1024, 144, 768, "0s",
            )
        return cls(
            mode, total_bytes // (1024 * 1024) if total_bytes else None,
            available_bytes // (1024 * 1024) if available_bytes is not None else None,
            min(count, 4), 2048, 320, 2048, 256, 1536, "45s",
        )

    def text_options(self, context: int, max_output: int | None) -> dict:
        options = {
            "num_ctx": min(context, self.text_context),
            "num_thread": self.num_thread,
            "num_batch": 64 if self.mode == "eco" else 128,
        }
        if max_output is not None:
            options["num_predict"] = min(max_output, self.text_predict)
        else:
            options["num_predict"] = self.text_predict
        return options

    def vision_options(self) -> dict:
        return {
            "num_ctx": self.vision_context,
            "num_predict": self.vision_predict,
            "num_thread": self.num_thread,
            "num_batch": 64 if self.mode == "eco" else 128,
            "temperature": 0.2,
        }
