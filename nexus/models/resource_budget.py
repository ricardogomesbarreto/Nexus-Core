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


def _memory_bytes() -> tuple[int | None, int | None]:
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
    # Linux cgroup v2 is used on modern Ubuntu/Debian and other distros.
    # cgroup v1 is supported for older container environments.
    for name in ("/sys/fs/cgroup/memory.max",
                 "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
        try:
            limit = _positive_int(Path(name).read_text(encoding="ascii"))
        except (OSError, ValueError):
            continue
        if limit is not None and (total is None or limit < total):
            total = limit
        break
    try:
        current = _positive_int(Path("/sys/fs/cgroup/memory.current").read_text())
        if total is not None and current is not None:
            remain = max(0, total - current)
            available = min(available, remain) if available is not None else remain
    except (OSError, ValueError):
        pass
    return total, available


def _logical_cores() -> int:
    try:
        if hasattr(os, "sched_getaffinity"):
            return max(1, len(os.sched_getaffinity(0)))
    except OSError:
        pass
    return max(1, os.cpu_count() or 1)


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
