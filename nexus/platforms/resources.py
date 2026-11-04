"""Bounded, read-only resource snapshot for the local Linux/Ollama runtime."""

from http.client import HTTPConnection, HTTPException
import json
from pathlib import Path


MAX_PS_BYTES = 65_536
MAX_LOADED_MODELS = 64
MAX_MODEL_BYTES = 1 << 50


def _memory_snapshot(read_text=None) -> dict:
    try:
        raw = (Path("/proc/meminfo").read_text(encoding="ascii")
               if read_text is None else read_text())[:8192]
        values = {}
        for line in raw.splitlines():
            key, separator, amount = line.partition(":")
            if separator and key in ("MemTotal", "MemAvailable", "SwapTotal", "SwapFree"):
                parts = amount.split()
                if len(parts) == 2 and parts[1] == "kB":
                    number = int(parts[0])
                    if 0 <= number <= 1 << 40:
                        values[key] = number
        total, available = values["MemTotal"], values["MemAvailable"]
        swap_total, swap_free = values["SwapTotal"], values["SwapFree"]
        if available > total or swap_free > swap_total:
            raise ValueError("invalid meminfo")
        return {"status": "available", "total_mib": total // 1024,
                "available_mib": available // 1024,
                "swap_used_mib": (swap_total - swap_free) // 1024}
    except (OSError, ValueError, KeyError, TypeError):
        return {"status": "unavailable"}


def _ollama_snapshot(connect=None) -> dict:
    connection = None
    try:
        factory = HTTPConnection if connect is None else connect
        connection = factory("127.0.0.1", 11434, timeout=2)
        connection.request("GET", "/api/ps")
        response = connection.getresponse()
        if response.status != 200:
            return {"status": "unavailable"}
        raw = response.read(MAX_PS_BYTES + 1)
        if len(raw) > MAX_PS_BYTES:
            return {"status": "unavailable"}
        data = json.loads(raw.decode("utf-8", errors="strict"))
        models = data.get("models") if type(data) is dict else None
        if type(models) is not list or len(models) > MAX_LOADED_MODELS:
            return {"status": "unavailable"}
        total_size = total_vram = 0
        for model in models:
            if type(model) is not dict:
                return {"status": "unavailable"}
            size, vram = model.get("size"), model.get("size_vram")
            if (type(size) is not int or type(vram) is not int
                    or not 0 <= vram <= size <= MAX_MODEL_BYTES):
                return {"status": "unavailable"}
            total_size += size
            total_vram += vram
        return {"status": "available", "loaded_models": len(models),
                "reported_model_size_mib": total_size // (1024 * 1024),
                "reported_vram_mib": total_vram // (1024 * 1024)}
    except (OSError, HTTPException, TimeoutError, ValueError, UnicodeError, TypeError):
        return {"status": "unavailable"}
    finally:
        if connection is not None:
            try:
                connection.close()
            except (OSError, HTTPException):
                pass


def _profile_snapshot() -> dict:
    """Read-only effective hardware budget; no inference or service startup."""
    from nexus.models.resource_budget import ResourceBudget
    try:
        profile = ResourceBudget.detect()
    except (OSError, ValueError):
        return {"status": "unavailable"}
    if profile.total_ram_mib is None:
        return {"status": "unavailable"}
    return {
        "status": "available",
        "profile": profile.mode,
        "effective_total_ram_mib": profile.total_ram_mib,
        "effective_available_ram_mib": profile.available_ram_mib,
        "inference_threads": profile.num_thread,
        "text_context_tokens": profile.text_context,
        "vision_max_edge_pixels": profile.vision_edge,
        "model_keep_alive": profile.keep_alive,
    }


def inspect_resources(*, read_text=None, connect=None) -> dict:
    """No model names, prompts, images, service mutations or external traffic."""
    return {"schema": "nexus.resources.v1", "mode": "passive_local",
            "memory": _memory_snapshot(read_text),
            "effective_profile": _profile_snapshot(),
            "ollama": _ollama_snapshot(connect),
            "inference_tested": False, "external_network_used": False}
