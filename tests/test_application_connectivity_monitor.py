import pytest

from nexus.core.application import NexusApplication
from nexus.core.connectivity import ConnectivityManager
from nexus.core.runtime import RuntimeMode
from nexus.events import EventType


class OnlineStatus:
    online = True
    latency_ms = 10.0
    endpoint = "https://example.com"


class OfflineStatus:
    online = False
    latency_ms = None
    endpoint = "https://example.com"


def test_application_connectivity_monitor_is_none_before_initialize():
    app = NexusApplication()

    try:
        assert app.connectivity_monitor is None
    finally:
        app.database.close()


def test_application_forced_offline_does_not_start_connectivity_monitor(
    monkeypatch,
):
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

    try:
        app.initialize()

        assert app.connectivity_monitor is None
    finally:
        app.shutdown()


def test_application_online_starts_connectivity_monitor(
    monkeypatch,
):
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

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: OnlineStatus(),
    )

    app = NexusApplication()

    try:
        app.initialize()

        assert app.connectivity_monitor is not None
        assert app.connectivity_monitor.interval == 60.0
        assert app.connectivity_monitor.is_running is True
    finally:
        app.shutdown()


def test_application_initial_offline_starts_connectivity_monitor(
    monkeypatch,
):
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

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: OfflineStatus(),
    )

    app = NexusApplication()

    try:
        app.initialize()

        assert app.connectivity_monitor is not None
        assert app.connectivity_monitor.interval == 60.0
        assert app.connectivity_monitor.is_running is True
    finally:
        app.shutdown()



def test_application_monitor_detects_offline_to_online_transition(
    monkeypatch,
):
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

    statuses = iter(
        [
            OfflineStatus(),
            OnlineStatus(),
            OnlineStatus(),
        ]
    )

    app = NexusApplication()

    monkeypatch.setattr(
        app.connectivity_manager,
        "check",
        lambda: next(statuses),
    )

    events = []

    app.event_bus.subscribe(
        EventType.NETWORK_OFFLINE,
        lambda event: events.append(event),
    )
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

        assert app.runtime_state.mode == RuntimeMode.OFFLINE

        assert [
            event.event_type
            for event in events
        ] == [
            EventType.NETWORK_OFFLINE,
            EventType.RUNTIME_MODE_CHANGED,
        ]

        first_changed = app.connectivity_monitor.check_once()

        assert first_changed is True
        assert app.runtime_state.mode == RuntimeMode.DEGRADED
        assert app.runtime_state.reason == (
            "Conectividade externa detectada; aguardando confirmação"
        )

        first_health = app.health.runtime_snapshot()

        assert first_health.network_online is True
        assert first_health.runtime_mode == RuntimeMode.DEGRADED

        assert [
            event.event_type
            for event in events
        ] == [
            EventType.NETWORK_OFFLINE,
            EventType.RUNTIME_MODE_CHANGED,
            EventType.NETWORK_ONLINE,
            EventType.RUNTIME_MODE_CHANGED,
        ]

        assert events[-1].data["mode"] == (
            RuntimeMode.DEGRADED.value
        )

        second_changed = app.connectivity_monitor.check_once()

        assert second_changed is True
        assert app.runtime_state.mode == RuntimeMode.ONLINE
        assert app.runtime_state.reason == (
            "Conectividade externa disponível"
        )

        second_health = app.health.runtime_snapshot()

        assert second_health.network_online is True
        assert second_health.runtime_mode == RuntimeMode.ONLINE
        assert second_health.runtime_reason == (
            "Conectividade externa disponível"
        )

        assert [
            event.event_type
            for event in events
        ] == [
            EventType.NETWORK_OFFLINE,
            EventType.RUNTIME_MODE_CHANGED,
            EventType.NETWORK_ONLINE,
            EventType.RUNTIME_MODE_CHANGED,
            EventType.RUNTIME_MODE_CHANGED,
        ]

        assert events[-1].data["mode"] == (
            RuntimeMode.ONLINE.value
        )
    finally:
        app.shutdown()


def test_application_monitor_detects_online_to_offline_transition(
    monkeypatch,
):
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

    statuses = iter(
        [
            OnlineStatus(),
            OfflineStatus(),
            OfflineStatus(),
        ]
    )

    app = NexusApplication()

    monkeypatch.setattr(
        app.connectivity_manager,
        "check",
        lambda: next(statuses),
    )

    events = []

    app.event_bus.subscribe(
        EventType.NETWORK_ONLINE,
        lambda event: events.append(event),
    )
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

        assert app.runtime_state.mode == RuntimeMode.ONLINE

        assert [
            event.event_type
            for event in events
        ] == [
            EventType.NETWORK_ONLINE,
            EventType.RUNTIME_MODE_CHANGED,
        ]

        first_changed = app.connectivity_monitor.check_once()

        assert first_changed is True
        assert app.runtime_state.mode == RuntimeMode.DEGRADED
        assert app.runtime_state.reason == (
            "Perda de conectividade aguardando confirmação"
        )

        first_health = app.health.runtime_snapshot()

        assert first_health.network_online is False
        assert first_health.runtime_mode == RuntimeMode.DEGRADED

        assert [
            event.event_type
            for event in events
        ] == [
            EventType.NETWORK_ONLINE,
            EventType.RUNTIME_MODE_CHANGED,
            EventType.NETWORK_OFFLINE,
            EventType.RUNTIME_MODE_CHANGED,
        ]

        assert events[-1].data["mode"] == (
            RuntimeMode.DEGRADED.value
        )

        second_changed = app.connectivity_monitor.check_once()

        assert second_changed is True
        assert app.runtime_state.mode == RuntimeMode.OFFLINE
        assert app.runtime_state.reason == (
            "Conectividade externa indisponível"
        )

        second_health = app.health.runtime_snapshot()

        assert second_health.network_online is False
        assert second_health.runtime_mode == RuntimeMode.OFFLINE
        assert second_health.runtime_reason == (
            "Conectividade externa indisponível"
        )

        assert [
            event.event_type
            for event in events
        ] == [
            EventType.NETWORK_ONLINE,
            EventType.RUNTIME_MODE_CHANGED,
            EventType.NETWORK_OFFLINE,
            EventType.RUNTIME_MODE_CHANGED,
            EventType.RUNTIME_MODE_CHANGED,
        ]

        assert events[-1].data["mode"] == (
            RuntimeMode.OFFLINE.value
        )
    finally:
        app.shutdown()


def test_application_shutdown_stops_monitor_before_system_stop(
    monkeypatch,
):
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

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: OnlineStatus(),
    )

    app = NexusApplication()
    lifecycle = []

    app.initialize()

    original_stop = app.connectivity_monitor.stop

    def recording_stop(*args, **kwargs):
        lifecycle.append("monitor.stop")
        return original_stop(*args, **kwargs)

    app.connectivity_monitor.stop = recording_stop

    app.event_bus.subscribe(
        EventType.SYSTEM_STOP,
        lambda event: lifecycle.append("system.stop"),
    )

    app.shutdown()

    assert lifecycle == [
        "monitor.stop",
        "system.stop",
    ]

    assert app.connectivity_monitor.is_running is False



def test_application_shutdown_does_not_complete_if_monitor_stop_times_out(
    monkeypatch,
):
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

    monkeypatch.setattr(
        ConnectivityManager,
        "check",
        lambda self: OnlineStatus(),
    )

    app = NexusApplication()
    lifecycle = []

    app.initialize()

    original_monitor_stop = app.connectivity_monitor.stop
    original_close = app.database.close

    monkeypatch.setattr(
        app.connectivity_monitor,
        "stop",
        lambda: (_ for _ in ()).throw(
            TimeoutError("simulated monitor timeout")
        ),
    )

    app.event_bus.subscribe(
        EventType.SYSTEM_STOP,
        lambda event: lifecycle.append("system.stop"),
    )

    def recording_close():
        lifecycle.append("database.close")
        return original_close()

    monkeypatch.setattr(
        app.database,
        "close",
        recording_close,
    )

    try:
        with pytest.raises(
            TimeoutError,
            match="simulated monitor timeout",
        ):
            app.shutdown()

        assert lifecycle == []
        assert app.connectivity_monitor.is_running is True
    finally:
        # O shutdown simulado falhou propositalmente.
        # O teste deve, entretanto, liberar a worker real.
        original_monitor_stop(timeout=1.0)
        original_close()


def test_application_rejects_repeated_initialize(
    monkeypatch,
):
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

    try:
        app.initialize()

        with pytest.raises(
            RuntimeError,
            match="NexusApplication já foi inicializada",
        ):
            app.initialize()
    finally:
        app.shutdown()




def test_application_shutdown_is_idempotent(
    monkeypatch,
):
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
        EventType.SYSTEM_STOP,
        lambda event: events.append(event),
    )

    app.initialize()

    app.shutdown()
    app.shutdown()

    assert len(events) == 1
    assert events[0].event_type == EventType.SYSTEM_STOP


def test_application_passes_connectivity_confirmation_threshold(
    monkeypatch,
):
    class FakeSettings:
        offline_mode = False
        version = "0.2.0"
        node_name = "NEXUS-NODE-01"
        connectivity_monitor_interval = 60.0
        connectivity_confirmation_threshold = 3

    monkeypatch.setattr(
        "nexus.core.application.settings",
        FakeSettings(),
    )

    statuses = iter(
        [
            OfflineStatus(),
            OnlineStatus(),
            OnlineStatus(),
            OnlineStatus(),
        ]
    )

    app = NexusApplication()

    monkeypatch.setattr(
        app.connectivity_manager,
        "check",
        lambda: next(statuses),
    )

    try:
        app.initialize()

        assert app.runtime_state.mode == RuntimeMode.OFFLINE

        first_changed = app.connectivity_monitor.check_once()

        assert first_changed is True
        assert app.runtime_state.mode == RuntimeMode.DEGRADED

        second_changed = app.connectivity_monitor.check_once()

        assert second_changed is False
        assert app.runtime_state.mode == RuntimeMode.DEGRADED

        third_changed = app.connectivity_monitor.check_once()

        assert third_changed is True
        assert app.runtime_state.mode == RuntimeMode.ONLINE
    finally:
        app.shutdown()
