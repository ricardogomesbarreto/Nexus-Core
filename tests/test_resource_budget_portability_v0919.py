"""Resource profiles must honor real Linux quotas on machines and containers."""
from pathlib import Path

import pytest

from nexus.models import resource_budget as budget

MIB = 1024 * 1024
GIB = 1024 * MIB


def simulate(monkeypatch, paths):
    def fake_read(path, *args, **kwargs):
        value = paths.get(str(path))
        if value is None:
            raise FileNotFoundError(str(path))
        return value
    monkeypatch.setattr(Path, "read_text", fake_read)


def test_automatic_profile_uses_v2_memory_cap_not_host_ram(monkeypatch):
    simulate(monkeypatch, {
        "/proc/meminfo": "MemTotal:  33554432 kB\nMemAvailable: 25165824 kB\n",
        "/sys/fs/cgroup/memory.max": str(4 * GIB),
        "/sys/fs/cgroup/memory.current": str(3 * GIB),
        "/sys/fs/cgroup/cpu.max": "200000 100000",
    })
    monkeypatch.setattr(budget.os, "sched_getaffinity", lambda pid: set(range(12)))
    total, available = budget._memory_bytes()
    assert (total, available) == (4 * GIB, GIB)
    profile = budget.ResourceBudget.detect(requested="auto")
    assert profile.mode == "eco"
    assert profile.num_thread == 1
    assert profile.text_context == 768
    assert profile.vision_edge == 512
    assert profile.available_ram_mib == 1024


def test_automatic_profile_respects_v1_usage_and_half_cpu(monkeypatch):
    simulate(monkeypatch, {
        "/proc/meminfo": "MemTotal: 16777216 kB\nMemAvailable: 12582912 kB\n",
        "/sys/fs/cgroup/memory/memory.limit_in_bytes": str(2 * GIB),
        "/sys/fs/cgroup/memory/memory.usage_in_bytes": str(1500 * MIB),
        "/sys/fs/cgroup/cpu/cpu.cfs_quota_us": "50000",
        "/sys/fs/cgroup/cpu/cpu.cfs_period_us": "100000",
    })
    monkeypatch.setattr(budget.os, "sched_getaffinity", lambda pid: set(range(16)))
    profile = budget.ResourceBudget.detect()
    assert profile.mode == "eco"
    assert profile.total_ram_mib == 2048
    assert profile.available_ram_mib == 548
    assert profile.num_thread == 1
    assert profile.keep_alive == "0s"


def test_unlimited_cgroups_do_not_hide_host_resource_estimate(monkeypatch):
    simulate(monkeypatch, {
        "/proc/meminfo": "MemTotal: 33554432 kB\nMemAvailable: 20971520 kB\n",
        "/sys/fs/cgroup/memory.max": "max",
        "/sys/fs/cgroup/memory/memory.limit_in_bytes": str((1 << 63) - 4096),
        "/sys/fs/cgroup/cpu.max": "max 100000",
        "/sys/fs/cgroup/cpu/cpu.cfs_quota_us": "-1",
    })
    monkeypatch.setattr(budget.os, "sched_getaffinity", lambda pid: set(range(6)))
    assert budget._memory_bytes() == (32 * GIB, 20 * GIB)
    assert budget._logical_cores() == 6
    assert budget.ResourceBudget.detect().mode == "balanced"


def test_memory_used_over_limit_is_zero_available(monkeypatch):
    simulate(monkeypatch, {
        "/proc/meminfo": "MemTotal: 8388608 kB\nMemAvailable: 7340032 kB\n",
        "/sys/fs/cgroup/memory.max": str(1024 * MIB),
        "/sys/fs/cgroup/memory.current": str(1300 * MIB),
    })
    assert budget._memory_bytes() == (GIB, 0)
    assert budget.ResourceBudget.available_now_mib() == 0


def test_most_restrictive_memory_cap_applies_if_both_are_readable(monkeypatch):
    simulate(monkeypatch, {
        "/proc/meminfo": "MemTotal: 8388608 kB\nMemAvailable: 7340032 kB\n",
        "/sys/fs/cgroup/memory.max": str(6 * GIB),
        "/sys/fs/cgroup/memory.current": str(4 * GIB),
        "/sys/fs/cgroup/memory/memory.limit_in_bytes": str(3 * GIB),
        "/sys/fs/cgroup/memory/memory.usage_in_bytes": str(2 * GIB),
    })
    assert budget._memory_bytes() == (3 * GIB, GIB)


@pytest.mark.parametrize("quota,period,expected", [
    ("100000", "100000", 1),
    ("150000", "100000", 2),
    ("200000", "100000", 2),
    ("50000", "100000", 1),
])
def test_cpu_quotas_do_not_overallocate_threads(monkeypatch, quota, period, expected):
    simulate(monkeypatch, {"/sys/fs/cgroup/cpu.max": f"{quota} {period}"})
    monkeypatch.setattr(budget.os, "sched_getaffinity", lambda pid: set(range(16)))
    assert budget._logical_cores() == expected


def test_no_readable_proc_info_fails_conservatively(monkeypatch):
    simulate(monkeypatch, {})
    total, available = budget._memory_bytes()
    assert total is None and available is None
    assert budget.ResourceBudget.available_now_mib() is None


@pytest.mark.parametrize("ram_gib,expected_threads,expected_edge", [
    (2, 1, 512), (4, 1, 512), (6, 2, 768), (8, 2, 768),
    (16, 4, 1536), (32, 4, 1536),
])
def test_auto_tiers_by_effective_ram(ram_gib, expected_threads, expected_edge):
    profile = budget.ResourceBudget.detect(
        requested="auto", total_bytes=ram_gib * GIB,
        available_bytes=max(1, ram_gib - 1) * GIB, cores=16,
    )
    assert profile.num_thread == expected_threads
    assert profile.vision_edge == expected_edge
    if ram_gib <= 8:
        assert profile.mode == "eco"
        assert profile.keep_alive == "0s"
    else:
        assert profile.mode == "balanced"


def test_manual_balanced_does_not_silently_change_to_eco():
    # Explicit configuration remains user controlled; GUI warnings and
    # runtime pressure checks still protect individual model requests.
    profile = budget.ResourceBudget.detect(
        requested="balanced", total_bytes=4 * GIB,
        available_bytes=2 * GIB, cores=4,
    )
    assert profile.mode == "balanced"



def test_nested_systemd_v2_user_slice_memory_and_cpu_caps(monkeypatch):
    root = "/sys/fs/cgroup/user.slice/user-1000.slice/app.slice"
    simulate(monkeypatch, {
        "/proc/self/cgroup": "0::/user.slice/user-1000.slice/app.slice\n",
        "/proc/meminfo": "MemTotal: 33554432 kB\nMemAvailable: 25165824 kB\n",
        "/sys/fs/cgroup/memory.max": "max",
        "/sys/fs/cgroup/user.slice/memory.max": str(16 * GIB),
        "/sys/fs/cgroup/user.slice/memory.current": str(3 * GIB),
        root + "/memory.max": str(3 * GIB),
        root + "/memory.current": str(2400 * MIB),
        "/sys/fs/cgroup/cpu.max": "max 100000",
        "/sys/fs/cgroup/user.slice/cpu.max": "400000 100000",
        root + "/cpu.max": "150000 100000",
    })
    monkeypatch.setattr(budget.os, "sched_getaffinity", lambda pid: set(range(24)))
    total, free = budget._memory_bytes()
    assert total == 3 * GIB
    assert free == (3 * GIB - 2400 * MIB)
    profile = budget.ResourceBudget.detect()
    assert profile.mode == "eco"
    assert profile.num_thread == 1  # Host memory is 3 GiB; ultra-light.
    assert budget._logical_cores() == 2


def test_nested_v1_memory_and_cpu_limits(monkeypatch):
    root_mem = "/sys/fs/cgroup/memory/docker/abc"
    root_cpu = "/sys/fs/cgroup/cpu/docker/abc"
    simulate(monkeypatch, {
        "/proc/self/cgroup": "7:memory:/docker/abc\n6:cpu,cpuacct:/docker/abc\n",
        "/proc/meminfo": "MemTotal: 16777216 kB\nMemAvailable: 12582912 kB\n",
        root_mem + "/memory.limit_in_bytes": str(4 * GIB),
        root_mem + "/memory.usage_in_bytes": str(3 * GIB),
        root_cpu + "/cpu.cfs_quota_us": "200000",
        root_cpu + "/cpu.cfs_period_us": "100000",
    })
    monkeypatch.setattr(budget.os, "sched_getaffinity", lambda pid: set(range(8)))
    assert budget._memory_bytes() == (4 * GIB, GIB)
    assert budget._logical_cores() == 2


def test_cgroup_path_traversal_is_never_followed(monkeypatch):
    simulate(monkeypatch, {
        "/proc/self/cgroup": "0::/user.slice/../../etc\n",
        "/proc/meminfo": "MemTotal: 8388608 kB\nMemAvailable: 4194304 kB\n",
        "/sys/fs/cgroup/memory.max": str(5 * GIB),
        "/sys/fs/cgroup/memory.current": str(GIB),
        "/sys/fs/cgroup/user.slice/../../etc/memory.max": "1",
    })
    assert budget._cgroup_directories("/sys/fs/cgroup", "unified") == (
        Path("/sys/fs/cgroup"),
    )
    assert budget._memory_bytes() == (5 * GIB, 4 * GIB)
