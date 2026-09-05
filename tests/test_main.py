import pytest

import nexus.main as nexus_main
from nexus.core.runtime import RuntimeMode


class FakeHealth:
    core = True
    configuration = True
    database = True
    logger = True
    event_bus = True
    security_gate = True
    tool_registry = True
    terminal_sandbox = True

    network_online = False
    runtime_mode = RuntimeMode.OFFLINE

    @property
    def ready(self):
        return True

    def runtime_snapshot(self):
        class Snapshot:
            network_online = self.network_online
            runtime_mode = self.runtime_mode
            runtime_reason = None

        return Snapshot()


def test_main_always_shuts_down_after_success(monkeypatch):
    lifecycle = []

    class FakeApplication:
        def initialize(self):
            lifecycle.append("initialize")

        def status(self):
            lifecycle.append("status")
            return FakeHealth()

        def shutdown(self):
            lifecycle.append("shutdown")

    monkeypatch.setattr(
        nexus_main,
        "NexusApplication",
        FakeApplication,
    )

    nexus_main.main()

    assert lifecycle == [
        "initialize",
        "status",
        "shutdown",
    ]


def test_main_shuts_down_when_runtime_fails_after_initialize(
    monkeypatch,
):
    lifecycle = []

    class FakeApplication:
        def initialize(self):
            lifecycle.append("initialize")

        def status(self):
            lifecycle.append("status")
            raise RuntimeError("simulated runtime failure")

        def shutdown(self):
            lifecycle.append("shutdown")

    monkeypatch.setattr(
        nexus_main,
        "NexusApplication",
        FakeApplication,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated runtime failure",
    ):
        nexus_main.main()

    assert lifecycle == [
        "initialize",
        "status",
        "shutdown",
    ]


def test_main_uses_runtime_snapshot_for_runtime_fields(
    monkeypatch,
):
    lifecycle = []

    class FakeRuntimeSnapshot:
        network_online = True
        runtime_mode = RuntimeMode.ONLINE
        runtime_reason = "Conectividade externa disponível"

    class SnapshotHealth:
        core = True
        configuration = True
        database = True
        logger = True
        event_bus = True
        security_gate = True
        tool_registry = True
        terminal_sandbox = True

        @property
        def ready(self):
            return True

        def runtime_snapshot(self):
            lifecycle.append("runtime_snapshot")
            return FakeRuntimeSnapshot()

        @property
        def network_online(self):
            raise AssertionError(
                "main() não deve ler network_online diretamente"
            )

        @property
        def runtime_mode(self):
            raise AssertionError(
                "main() não deve ler runtime_mode diretamente"
            )

    class FakeApplication:
        def initialize(self):
            lifecycle.append("initialize")

        def status(self):
            lifecycle.append("status")
            return SnapshotHealth()

        def shutdown(self):
            lifecycle.append("shutdown")

    monkeypatch.setattr(
        nexus_main,
        "NexusApplication",
        FakeApplication,
    )

    nexus_main.main()

    assert lifecycle == [
        "initialize",
        "status",
        "runtime_snapshot",
        "shutdown",
    ]
