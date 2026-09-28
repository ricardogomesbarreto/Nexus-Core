from types import SimpleNamespace

import nexus.main as main_module


class GenericHealthProbe:
    core = True
    configuration = True
    database = True
    logger = True
    event_bus = True
    security_gate = True
    tool_registry = True
    terminal_sandbox = True
    model_layer = True
    ready = True

    @property
    def local_model_layer(self):
        raise AssertionError(
            "main deve consultar health.model_layer"
        )

    def runtime_snapshot(self):
        return SimpleNamespace(
            network_online=False,
            runtime_mode=SimpleNamespace(
                value="OFFLINE"
            ),
        )


class FakeApplication:
    def __init__(self):
        self.health = GenericHealthProbe()
        self.initialized = False
        self.shutdown_called = False

    def initialize(self):
        self.initialized = True

    def status(self):
        return self.health

    def shutdown(self):
        self.shutdown_called = True


def test_main_uses_generic_model_layer_status(
    monkeypatch,
    capsys,
):
    app = FakeApplication()

    monkeypatch.setattr(
        main_module,
        "build_application",
        lambda: app,
    )

    monkeypatch.setattr(
        main_module,
        "settings",
        SimpleNamespace(
            version="0.3.1-test",
            node_name="TEST-NODE",
        ),
    )

    main_module.main()

    output = capsys.readouterr().out

    assert app.initialized is True
    assert app.shutdown_called is True

    assert "Model Layer" in output
    assert "Local Model Layer" not in output
