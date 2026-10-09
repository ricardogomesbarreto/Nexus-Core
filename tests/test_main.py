import pytest
from nexus.tools import ToolResult

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
    model_layer = True

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
        "build_application",
        lambda: FakeApplication(),
    )

    nexus_main.main()

    assert lifecycle == [
        "initialize",
        "status",
        "shutdown",
    ]


def test_cli_sandbox_command_uses_executor_and_shuts_down(monkeypatch, capsys):
    calls = []

    class FakeExecutor:
        def execute(self, name, **kwargs):
            calls.append((name, kwargs))
            return ToolResult(True, name, data={"stdout": "OK\n", "stderr": ""})

    class FakeApplication:
        tool_executor = FakeExecutor()

        def initialize(self):
            calls.append("initialize")

        def status(self):
            return FakeHealth()

        def shutdown(self):
            calls.append("shutdown")

    monkeypatch.setattr(nexus_main, "build_application", FakeApplication)
    assert nexus_main.main("echo OK", "/workspace") == 0
    assert calls == [
        "initialize",
        ("terminal_sandbox", {"command": "echo OK", "workspace": "/workspace"}),
        "shutdown",
    ]
    assert capsys.readouterr().out.endswith("OK\n")


def test_cli_rejects_workspace_without_command(capsys):
    with pytest.raises(SystemExit) as exc:
        nexus_main.cli(["--workspace", "/tmp"])
    assert exc.value.code == 2
    assert "--workspace exige --sandbox-command" in capsys.readouterr().err


def test_cli_rejects_simultaneous_agent_and_sandbox(capsys):
    with pytest.raises(SystemExit) as exc:
        nexus_main.cli(["--agent-prompt", "oi", "--sandbox-command", "pwd"])
    assert exc.value.code == 2


def test_agent_prompt_uses_planner_and_shuts_down(monkeypatch, capsys):
    from nexus.agent import AgentOutcome

    calls = []

    class FakeAgent:
        def run(self, prompt):
            calls.append(prompt)
            return AgentOutcome(True, content="Olá")

    class FakeApplication:
        agent = FakeAgent()

        def initialize(self):
            calls.append("initialize")

        def status(self):
            return FakeHealth()

        def shutdown(self):
            calls.append("shutdown")

    monkeypatch.setattr(nexus_main, "build_application", FakeApplication)
    assert nexus_main.main(agent_prompt="oi") == 0
    assert calls == ["initialize", "oi", "shutdown"]
    assert capsys.readouterr().out.endswith("Olá\n")


def test_no_argument_cli_starts_desktop(monkeypatch):
    import nexus.desktop.window as window

    calls = []
    monkeypatch.setattr(window, "launch_desktop", lambda: calls.append("desktop") or 0)
    monkeypatch.setattr(
        nexus_main, "build_application",
        lambda: (_ for _ in ()).throw(AssertionError("CLI should not start")),
    )
    nexus_main.cli([])
    nexus_main.cli(["--desktop"])
    assert calls == ["desktop", "desktop"]


def test_desktop_cli_propagates_startup_error(monkeypatch):
    import nexus.desktop.window as window

    monkeypatch.setattr(window, "launch_desktop", lambda: 2)
    with pytest.raises(SystemExit) as exc:
        nexus_main.cli(["--desktop"])
    assert exc.value.code == 2


def test_status_option_keeps_terminal_health(monkeypatch):
    calls = []

    class FakeApplication:
        def initialize(self):
            calls.append("initialize")

        def status(self):
            return FakeHealth()

        def shutdown(self):
            calls.append("shutdown")

    monkeypatch.setattr(nexus_main, "build_application", FakeApplication)
    nexus_main.cli(["--status"])
    assert calls == ["initialize", "shutdown"]


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
        "build_application",
        lambda: FakeApplication(),
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
        model_layer = True

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
        "build_application",
        lambda: FakeApplication(),
    )

    nexus_main.main()

    assert lifecycle == [
        "initialize",
        "status",
        "runtime_snapshot",
        "shutdown",
    ]



def test_main_reports_model_layer_status(
    monkeypatch,
    capsys,
):
    class FakeApplication:
        def initialize(self):
            pass

        def status(self):
            return FakeHealth()

        def shutdown(self):
            pass

    monkeypatch.setattr(
        nexus_main,
        "build_application",
        lambda: FakeApplication(),
    )

    nexus_main.main()

    output = capsys.readouterr().out

    assert nexus_main.status_line(
        "Model Layer",
        "✓ READY",
    ) in output


def test_main_shuts_down_when_initialize_fails(
    monkeypatch,
):
    lifecycle = []

    class FakeApplication:
        def initialize(self):
            lifecycle.append("initialize")
            raise RuntimeError(
                "simulated initialize failure"
            )

        def status(self):
            raise AssertionError(
                "status() não deve ser chamado"
            )

        def shutdown(self):
            lifecycle.append("shutdown")

    monkeypatch.setattr(
        nexus_main,
        "build_application",
        lambda: FakeApplication(),
    )

    with pytest.raises(
        RuntimeError,
        match="simulated initialize failure",
    ):
        nexus_main.main()

    assert lifecycle == [
        "initialize",
        "shutdown",
    ]


def test_main_shuts_down_when_initialize_fails(monkeypatch):
    lifecycle = []

    class FakeApplication:
        def initialize(self):
            lifecycle.append("initialize")
            raise RuntimeError(
                "simulated initialize failure"
            )

        def shutdown(self):
            lifecycle.append("shutdown")

    monkeypatch.setattr(
        nexus_main,
        "build_application",
        lambda: FakeApplication(),
    )

    with pytest.raises(
        RuntimeError,
        match="simulated initialize failure",
    ):
        nexus_main.main()

    assert lifecycle == [
        "initialize",
        "shutdown",
    ]
