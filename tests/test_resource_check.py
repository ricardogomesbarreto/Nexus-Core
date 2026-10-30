"""Read-only resource diagnostics must stay local and omit private model data."""

import json

import pytest

from nexus.platforms.resources import inspect_resources
from nexus.updates.launcher import should_run_maintenance


MEMINFO = """MemTotal:       8388608 kB
MemAvailable:   3145728 kB
SwapTotal:      2097152 kB
SwapFree:       1572864 kB
"""


class LocalConnection:
    last = None
    body = b'{"models":[{"name":"private-model-name","size":3145728000,"size_vram":0}]}'

    def __init__(self, host, port, timeout):
        self.host, self.port, self.timeout = host, port, timeout
        self.calls = []
        self.closed = False
        LocalConnection.last = self

    def request(self, method, path):
        self.calls.append((method, path))

    def getresponse(self):
        class Response:
            status = 200
            def read(self, limit):
                assert limit <= 65_537
                return LocalConnection.body
        return Response()

    def close(self):
        self.closed = True


def test_resource_snapshot_uses_loopback_and_only_fixed_metrics():
    snapshot = inspect_resources(read_text=lambda: MEMINFO, connect=LocalConnection)
    assert snapshot["memory"] == {"status": "available", "total_mib": 8192,
                                  "available_mib": 3072, "swap_used_mib": 512}
    assert snapshot["ollama"] == {"status": "available", "loaded_models": 1,
                                  "reported_model_size_mib": 3000, "reported_vram_mib": 0}
    assert (LocalConnection.last.host, LocalConnection.last.port) == ("127.0.0.1", 11434)
    assert LocalConnection.last.calls == [("GET", "/api/ps")]
    assert LocalConnection.last.closed
    assert "private-model-name" not in json.dumps(snapshot)
    assert snapshot["external_network_used"] is False


def test_bad_or_unavailable_resources_do_not_claim_readiness():
    class BadConnection(LocalConnection):
        def getresponse(self):
            class Response:
                status = 200
                def read(self, limit):
                    return b'{"models":[{"name":"secret","size":true,"size_vram":0}]}'
            return Response()

    snapshot = inspect_resources(read_text=lambda: "MemTotal: 123 kB", connect=BadConnection)
    assert snapshot["memory"] == {"status": "unavailable"}
    assert snapshot["ollama"] == {"status": "unavailable"}
    assert "secret" not in json.dumps(snapshot)


def test_resource_cli_never_starts_database_or_prelaunch_updates(monkeypatch, capsys):
    import nexus.main as main
    import nexus.platforms.resources as resources

    monkeypatch.setattr(main, "build_application", lambda **kw: pytest.fail("No app startup"))
    monkeypatch.setattr(resources, "inspect_resources", lambda: {"schema": "nexus.resources.v1"})
    assert should_run_maintenance(["--resource-check"]) is False
    main.cli(["--resource-check"])
    assert json.loads(capsys.readouterr().out) == {"schema": "nexus.resources.v1"}


@pytest.mark.parametrize("profile,expected", [("eco", "0s"), ("balanced", "45s")])
def test_visual_request_respects_adaptive_model_residency(monkeypatch, profile, expected):
    from test_vision_runtime import Transport, image_bytes
    from nexus.config.settings import Settings
    from nexus.vision.local import LocalVision

    monkeypatch.setenv("NEXUS_RESOURCE_PROFILE", profile)
    transport = Transport({"done": True, "message": {"content": "Uma imagem."}})
    LocalVision(Settings(), transport=transport).describe(image_bytes())
    payload, _ = transport.calls[0]
    assert payload["keep_alive"] == expected


def test_resource_check_reports_effective_profile_without_model_activation(monkeypatch):
    from nexus.models.resource_budget import ResourceBudget
    import nexus.platforms.resources as resource_module
    detected = ResourceBudget.detect(
        requested="auto", total_bytes=4 * 1024 ** 3,
        available_bytes=1200 * 1024 ** 2, cores=16,
    )
    monkeypatch.setattr(ResourceBudget, "detect", lambda **kw: detected)
    result = resource_module.inspect_resources(
        read_text=lambda: MEMINFO, connect=LocalConnection,
    )
    assert result["effective_profile"] == {
        "status": "available", "profile": "eco",
        "effective_total_ram_mib": 4096,
        "effective_available_ram_mib": 1200,
        "inference_threads": 1,
        "text_context_tokens": 768,
        "vision_max_edge_pixels": 512,
        "model_keep_alive": "0s",
    }
    assert not result["inference_tested"]
    assert result["external_network_used"] is False


def test_resource_check_unverifiable_memory_is_not_claimed(monkeypatch):
    from nexus.models.resource_budget import ResourceBudget
    import nexus.platforms.resources as resource_module
    detected = ResourceBudget.detect(
        requested="auto", total_bytes=32 * 1024 ** 3,
        available_bytes=20 * 1024 ** 3, cores=8,
    )
    from dataclasses import replace
    monkeypatch.setattr(ResourceBudget, "detect",
                        lambda **kw: replace(detected, total_ram_mib=None))
    assert resource_module._profile_snapshot() == {"status": "unavailable"}
