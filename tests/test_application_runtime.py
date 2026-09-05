from nexus.config.settings import settings
from nexus.core.application import NexusApplication
from nexus.core.connectivity import ConnectivityManager
from nexus.core.runtime import RuntimeMode
from nexus.events import EventType

def test_application_has_connectivity_manager():
    app = NexusApplication()

    try:
        assert app.connectivity_manager is not None
    finally:
        app.database.close()


def test_offline_mode_configuration():
    assert settings.offline_mode is True


def test_default_runtime_is_offline():
    app = NexusApplication()

    try:
        assert app.health.runtime_mode == RuntimeMode.OFFLINE
        assert app.health.network_online is False
    finally:
        app.database.close()

def test_application_initialize_forced_offline():
    app = NexusApplication()

    try:
        app.initialize()

        assert app.health.network_online is False
        assert app.health.runtime_mode == RuntimeMode.OFFLINE
        assert app.health.runtime_reason == "Modo offline forçado pela configuração"
    finally:
        app.shutdown()

def test_application_initialize_online(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = True
        latency_ms = None
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()

    try:
        app.initialize()

        assert app.health.network_online is True
        assert app.health.runtime_mode == RuntimeMode.ONLINE
        assert app.health.runtime_reason == "Conectividade externa disponível"
    finally:
        app.shutdown()


def test_application_initialize_online_events(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = True
        latency_ms = None
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.NETWORK_ONLINE,
        lambda event: events.append(event),
    )

    app.event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        event_types = [
            event.event_type
            for event in events
        ]

        assert EventType.NETWORK_ONLINE in event_types
        assert EventType.RUNTIME_MODE_CHANGED in event_types
    finally:
        app.shutdown()


def test_application_initialize_offline_events(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = False
        latency_ms = None
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.NETWORK_OFFLINE,
        lambda event: events.append(event),
    )

    app.event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        event_types = [
            event.event_type
            for event in events
        ]

        assert EventType.NETWORK_OFFLINE in event_types
        assert EventType.RUNTIME_MODE_CHANGED in event_types

        assert app.health.network_online is False
        assert app.health.runtime_mode == RuntimeMode.OFFLINE
        assert app.health.runtime_reason == (
            "Conectividade externa indisponível"
        )
    finally:
        app.shutdown()

def test_application_initialize_forced_offline_events(monkeypatch):
    class FakeSettings:
        offline_mode = True
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        event_types = [
            event.event_type
            for event in events
        ]

        assert EventType.RUNTIME_MODE_CHANGED in event_types

        assert app.health.network_online is False
        assert app.health.runtime_mode == RuntimeMode.OFFLINE
        assert app.health.runtime_reason == (
            "Modo offline forçado pela configuração"
        )
    finally:
        app.shutdown()

def test_application_forced_offline_event_data(monkeypatch):
    class FakeSettings:
        offline_mode = True
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        assert len(events) == 1

        event = events[0]

        assert event.event_type == EventType.RUNTIME_MODE_CHANGED
        assert event.data["mode"] == RuntimeMode.OFFLINE.value
        assert event.data["reason"] == (
            "Modo offline forçado pela configuração"
        )

    finally:
        app.shutdown()

def test_application_runtime_health_consistency(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = True
        latency_ms = 18.0
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()

    try:
        app.initialize()

        health = app.status()

        assert health.network_online is True
        assert health.runtime_mode == RuntimeMode.ONLINE
        assert health.runtime_reason == (
            "Conectividade externa disponível"
        )

        assert health.ready is True

    finally:
        app.shutdown()

def test_application_offline_health_consistency(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = False
        latency_ms = None
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()

    try:
        app.initialize()

        health = app.status()

        assert health.network_online is False
        assert health.runtime_mode == RuntimeMode.OFFLINE
        assert health.runtime_reason == (
            "Conectividade externa indisponível"
        )

        assert health.ready is True

    finally:
        app.shutdown()
def test_application_online_event_data(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = True
        latency_ms = 18.0
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.NETWORK_ONLINE,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        assert len(events) == 1

        event = events[0]

        assert event.event_type == EventType.NETWORK_ONLINE
        assert event.data["endpoint"] == "https://example.com"
        assert event.data["latency_ms"] == 18.0

    finally:
        app.shutdown()


def test_application_offline_event_data(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = False
        latency_ms = None
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.NETWORK_OFFLINE,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        assert len(events) == 1

        event = events[0]

        assert event.event_type == EventType.NETWORK_OFFLINE
        assert event.data["endpoint"] == "https://example.com"
        assert event.data["latency_ms"] is None

    finally:
        app.shutdown()


def test_application_runtime_mode_changed_online_data(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = True
        latency_ms = 18.0
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        assert len(events) == 1

        event = events[0]

        assert event.event_type == EventType.RUNTIME_MODE_CHANGED
        assert event.data["mode"] == RuntimeMode.ONLINE.value
        assert event.data["reason"] == (
            "Conectividade externa disponível"
        )

    finally:
        app.shutdown()


def test_application_runtime_mode_changed_offline_data(monkeypatch):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 2

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    class FakeStatus:
        online = False
        latency_ms = None
        endpoint = "https://example.com"

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: FakeStatus(),
    )

    app = NexusApplication()
    events = []

    app.event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    try:
        app.initialize()

        assert len(events) == 1

        event = events[0]

        assert event.event_type == EventType.RUNTIME_MODE_CHANGED
        assert event.data["mode"] == RuntimeMode.OFFLINE.value
        assert event.data["reason"] == (
            "Conectividade externa indisponível"
        )

    finally:
        app.shutdown()
