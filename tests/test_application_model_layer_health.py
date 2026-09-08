import nexus.core.application as application_module

from nexus.config.settings import load_settings
from nexus.core.application import NexusApplication


class HealthWriteProbe:
    def __init__(self):
        self.core = False
        self.configuration = False
        self.database = False
        self.logger = False
        self.event_bus = False
        self.security_gate = False
        self.tool_registry = False
        self.terminal_sandbox = False

        self._model_layer = False
        self.generic_model_layer_writes = 0

        self.network_online = False
        self.runtime_mode = None
        self.runtime_reason = None

    @property
    def model_layer(self):
        return self._model_layer

    @model_layer.setter
    def model_layer(self, value):
        self.generic_model_layer_writes += 1
        self._model_layer = value

    @property
    def local_model_layer(self):
        return self._model_layer

    @local_model_layer.setter
    def local_model_layer(self, value):
        raise AssertionError(
            "NexusApplication deve escrever em health.model_layer"
        )

    def update_runtime(
        self,
        *,
        network_online,
        runtime_mode,
        runtime_reason,
    ):
        self.network_online = network_online
        self.runtime_mode = runtime_mode
        self.runtime_reason = runtime_reason


def test_application_initializes_generic_model_layer(
    monkeypatch,
):
    configured_settings = load_settings(
        {
            "NEXUS_OFFLINE_MODE": "true",
        }
    )

    monkeypatch.setattr(
        application_module,
        "settings",
        configured_settings,
    )

    app = NexusApplication()
    probe = HealthWriteProbe()
    app.health = probe

    try:
        app.initialize()

        assert probe.model_layer is True
        assert probe.generic_model_layer_writes == 1
    finally:
        app.shutdown()
