import threading

import pytest

from nexus.core.connectivity import ConnectivityStatus
from nexus.core.connectivity_monitor import ConnectivityMonitor
from nexus.core.runtime import RuntimeMode
from nexus.core.runtime_state import RuntimeStateController
from nexus.events import EventBus, EventType
from nexus.monitoring.health import HealthStatus


class StaticConnectivityManager:
    def __init__(self, status):
        self.status = status
        self.calls = 0

    def check(self):
        self.calls += 1
        return self.status


class ExplodingConnectivityManager:
    def __init__(self):
        self.calls = 0

    def check(self):
        self.calls += 1
        raise OSError("simulated connectivity failure")


class RecordingLogger:
    def __init__(self):
        self.exceptions = []

    def exception(self, message, *args):
        self.exceptions.append((message, args))


def build_monitor(
    *,
    status,
    runtime_state=None,
    health=None,
    event_bus=None,
    interval=10.0,
    logger=None,
):
    manager = StaticConnectivityManager(status)

    runtime_state = (
        runtime_state
        if runtime_state is not None
        else RuntimeStateController()
    )

    health = (
        health
        if health is not None
        else HealthStatus()
    )

    event_bus = (
        event_bus
        if event_bus is not None
        else EventBus()
    )

    monitor = ConnectivityMonitor(
        connectivity_manager=manager,
        runtime_state=runtime_state,
        event_bus=event_bus,
        health=health,
        interval=interval,
        logger=logger,
    )

    return monitor, manager, runtime_state, health, event_bus


def test_monitor_rejects_non_positive_interval():
    with pytest.raises(ValueError):
        build_monitor(
            status=ConnectivityStatus(),
            interval=0,
        )

    with pytest.raises(ValueError):
        build_monitor(
            status=ConnectivityStatus(),
            interval=-1,
        )


def test_check_once_same_offline_state_does_not_publish_events():
    runtime_state = RuntimeStateController(
        initial_mode=RuntimeMode.OFFLINE,
        initial_reason="Conectividade externa indisponível",
    )

    event_bus = EventBus()
    events = []

    event_bus.subscribe(
        EventType.NETWORK_OFFLINE,
        lambda event: events.append(event),
    )

    event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    monitor, manager, runtime_state, health, _ = build_monitor(
        status=ConnectivityStatus(
            online=False,
            endpoint="https://example.com",
        ),
        runtime_state=runtime_state,
        event_bus=event_bus,
    )

    changed = monitor.check_once()

    assert changed is False
    assert manager.calls == 1

    assert runtime_state.mode == RuntimeMode.OFFLINE
    assert runtime_state.reason == (
        "Conectividade externa indisponível"
    )
    assert runtime_state.changed_at is None

    assert health.network_online is False
    assert health.runtime_mode == RuntimeMode.OFFLINE

    assert events == []


def test_check_once_offline_to_online_updates_state_and_publishes_events():
    event_bus = EventBus()
    events = []

    event_bus.subscribe(
        EventType.NETWORK_ONLINE,
        lambda event: events.append(event),
    )

    event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    monitor, _, runtime_state, health, _ = build_monitor(
        status=ConnectivityStatus(
            online=True,
            latency_ms=12.5,
            endpoint="https://example.com",
        ),
        event_bus=event_bus,
    )

    changed = monitor.check_once()

    assert changed is True

    assert runtime_state.mode == RuntimeMode.ONLINE
    assert runtime_state.reason == (
        "Conectividade externa disponível"
    )
    assert runtime_state.changed_at is not None

    assert health.network_online is True
    assert health.runtime_mode == RuntimeMode.ONLINE
    assert health.runtime_reason == (
        "Conectividade externa disponível"
    )

    assert [
        event.event_type
        for event in events
    ] == [
        EventType.NETWORK_ONLINE,
        EventType.RUNTIME_MODE_CHANGED,
    ]

    assert events[0].data == {
        "endpoint": "https://example.com",
        "latency_ms": 12.5,
    }

    assert events[1].data == {
        "mode": RuntimeMode.ONLINE.value,
        "reason": "Conectividade externa disponível",
    }


def test_check_once_online_to_offline_updates_state_and_publishes_events():
    runtime_state = RuntimeStateController(
        initial_mode=RuntimeMode.ONLINE,
        initial_reason="Conectividade externa disponível",
    )

    health = HealthStatus()
    health.network_online = True
    health.runtime_mode = RuntimeMode.ONLINE
    health.runtime_reason = (
        "Conectividade externa disponível"
    )

    event_bus = EventBus()
    events = []

    event_bus.subscribe(
        EventType.NETWORK_OFFLINE,
        lambda event: events.append(event),
    )

    event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    monitor, _, runtime_state, health, _ = build_monitor(
        status=ConnectivityStatus(
            online=False,
            endpoint="https://example.com",
        ),
        runtime_state=runtime_state,
        health=health,
        event_bus=event_bus,
    )

    changed = monitor.check_once()

    assert changed is True

    assert runtime_state.mode == RuntimeMode.OFFLINE
    assert runtime_state.reason == (
        "Conectividade externa indisponível"
    )
    assert runtime_state.changed_at is not None

    assert health.network_online is False
    assert health.runtime_mode == RuntimeMode.OFFLINE
    assert health.runtime_reason == (
        "Conectividade externa indisponível"
    )

    assert [
        event.event_type
        for event in events
    ] == [
        EventType.NETWORK_OFFLINE,
        EventType.RUNTIME_MODE_CHANGED,
    ]

    assert events[0].data == {
        "endpoint": "https://example.com",
        "latency_ms": None,
    }

    assert events[1].data == {
        "mode": RuntimeMode.OFFLINE.value,
        "reason": "Conectividade externa indisponível",
    }


def test_check_once_same_online_state_does_not_publish_events():
    runtime_state = RuntimeStateController(
        initial_mode=RuntimeMode.ONLINE,
        initial_reason="Conectividade externa disponível",
    )

    health = HealthStatus()
    health.network_online = True
    health.runtime_mode = RuntimeMode.ONLINE
    health.runtime_reason = (
        "Conectividade externa disponível"
    )

    event_bus = EventBus()
    events = []

    event_bus.subscribe(
        EventType.NETWORK_ONLINE,
        lambda event: events.append(event),
    )

    event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    monitor, _, runtime_state, health, _ = build_monitor(
        status=ConnectivityStatus(
            online=True,
            latency_ms=7.0,
            endpoint="https://example.com",
        ),
        runtime_state=runtime_state,
        health=health,
        event_bus=event_bus,
    )

    changed = monitor.check_once()

    assert changed is False

    assert runtime_state.mode == RuntimeMode.ONLINE
    assert runtime_state.changed_at is None

    assert health.network_online is True
    assert health.runtime_mode == RuntimeMode.ONLINE

    assert events == []


def test_check_once_isolates_unexpected_connectivity_exception():
    manager = ExplodingConnectivityManager()
    runtime_state = RuntimeStateController()
    health = HealthStatus()
    event_bus = EventBus()
    logger = RecordingLogger()

    events = []

    event_bus.subscribe(
        EventType.NETWORK_OFFLINE,
        lambda event: events.append(event),
    )

    event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: events.append(event),
    )

    monitor = ConnectivityMonitor(
        connectivity_manager=manager,
        runtime_state=runtime_state,
        event_bus=event_bus,
        health=health,
        interval=10.0,
        logger=logger,
    )

    changed = monitor.check_once()

    assert changed is False
    assert manager.calls == 1

    assert runtime_state.mode == RuntimeMode.OFFLINE
    assert runtime_state.reason is None
    assert runtime_state.changed_at is None

    assert events == []

    assert len(logger.exceptions) == 1


def test_start_creates_named_daemon_worker_and_stop_is_graceful():
    monitor, _, _, _, _ = build_monitor(
        status=ConnectivityStatus(
            online=False,
            endpoint="https://example.com",
        ),
        interval=60.0,
    )

    monitor.start()

    try:
        workers = [
            thread
            for thread in threading.enumerate()
            if thread.name == "Nexus-ConnectivityMonitor"
        ]

        assert len(workers) == 1
        assert workers[0].daemon is True
        assert workers[0].is_alive() is True
        assert monitor.is_running is True
    finally:
        monitor.stop()

    assert monitor.is_running is False

    workers = [
        thread
        for thread in threading.enumerate()
        if thread.name == "Nexus-ConnectivityMonitor"
        and thread.is_alive()
    ]

    assert workers == []


def test_start_is_idempotent():
    monitor, _, _, _, _ = build_monitor(
        status=ConnectivityStatus(
            online=False,
            endpoint="https://example.com",
        ),
        interval=60.0,
    )

    monitor.start()

    try:
        monitor.start()

        workers = [
            thread
            for thread in threading.enumerate()
            if thread.name == "Nexus-ConnectivityMonitor"
            and thread.is_alive()
        ]

        assert len(workers) == 1
    finally:
        monitor.stop()


def test_stop_before_start_and_repeated_stop_are_safe():
    monitor, _, _, _, _ = build_monitor(
        status=ConnectivityStatus(
            online=False,
            endpoint="https://example.com",
        ),
    )

    monitor.stop()
    monitor.stop()

    assert monitor.is_running is False


def test_stop_raises_timeout_error_if_worker_does_not_terminate():
    entered_check = threading.Event()
    release_check = threading.Event()

    monitor, _, _, _, _ = build_monitor(
        status=ConnectivityStatus(
            online=False,
            endpoint="https://example.com",
        ),
        interval=0.01,
    )

    def blocking_check_once():
        entered_check.set()
        release_check.wait()
        return False

    monitor.check_once = blocking_check_once

    monitor.start()

    assert entered_check.wait(timeout=1.0) is True

    try:
        with pytest.raises(TimeoutError):
            monitor.stop(timeout=0.0)

        assert monitor.is_running is True
    finally:
        release_check.set()
        monitor.stop(timeout=1.0)

    assert monitor.is_running is False


def test_worker_survives_unexpected_cycle_exception():
    monitor, _, _, _, _ = build_monitor(
        status=ConnectivityStatus(
            online=False,
            endpoint="https://example.com",
        ),
        interval=0.01,
    )

    second_cycle_completed = threading.Event()
    calls = 0

    def flaky_check_once():
        nonlocal calls

        calls += 1

        if calls == 1:
            raise RuntimeError(
                "simulated unexpected monitor cycle failure"
            )

        second_cycle_completed.set()
        return False

    monitor.check_once = flaky_check_once

    monitor.start()

    try:
        assert second_cycle_completed.wait(timeout=1.0) is True
        assert calls >= 2
        assert monitor.is_running is True
    finally:
        monitor.stop(timeout=1.0)

    assert monitor.is_running is False






def test_transition_attempts_runtime_event_if_network_subscriber_fails():
    event_bus = EventBus()
    network_events = []
    runtime_events = []

    def failing_network_handler(event):
        network_events.append(event)
        raise RuntimeError(
            "simulated network subscriber failure"
        )

    event_bus.subscribe(
        EventType.NETWORK_ONLINE,
        failing_network_handler,
    )

    event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        lambda event: runtime_events.append(event),
    )

    monitor, _, runtime_state, health, _ = build_monitor(
        status=ConnectivityStatus(
            online=True,
            endpoint="https://example.com",
        ),
        event_bus=event_bus,
    )

    with pytest.raises(
        RuntimeError,
        match="simulated network subscriber failure",
    ):
        monitor.check_once()

    assert len(network_events) == 1

    assert [
        event.event_type
        for event in runtime_events
    ] == [
        EventType.RUNTIME_MODE_CHANGED,
    ]

    assert runtime_state.mode == RuntimeMode.ONLINE

    snapshot = health.runtime_snapshot()

    assert snapshot.network_online is True
    assert snapshot.runtime_mode == RuntimeMode.ONLINE
    assert snapshot.runtime_reason == (
        "Conectividade externa disponível"
    )


def test_worker_survives_network_subscriber_failure_and_continues():
    class SequenceConnectivityManager:
        def __init__(self):
            self.calls = 0

        def check(self):
            self.calls += 1

            if self.calls == 1:
                return ConnectivityStatus(
                    online=True,
                    endpoint="https://example.com",
                )

            return ConnectivityStatus(
                online=False,
                endpoint="https://example.com",
            )

    manager = SequenceConnectivityManager()
    runtime_state = RuntimeStateController()
    health = HealthStatus()
    event_bus = EventBus()

    offline_transition_seen = threading.Event()
    runtime_events = []

    def failing_online_handler(event):
        raise RuntimeError(
            "simulated network subscriber failure"
        )

    def record_runtime_event(event):
        runtime_events.append(event)

        if event.data["mode"] == RuntimeMode.OFFLINE.value:
            offline_transition_seen.set()

    event_bus.subscribe(
        EventType.NETWORK_ONLINE,
        failing_online_handler,
    )

    event_bus.subscribe(
        EventType.RUNTIME_MODE_CHANGED,
        record_runtime_event,
    )

    monitor = ConnectivityMonitor(
        connectivity_manager=manager,
        runtime_state=runtime_state,
        event_bus=event_bus,
        health=health,
        interval=0.01,
    )

    monitor.start()

    try:
        assert offline_transition_seen.wait(timeout=1.0) is True
        assert monitor.is_running is True
    finally:
        monitor.stop(timeout=1.0)

    assert manager.calls >= 2
    assert monitor.is_running is False

    assert [
        event.data["mode"]
        for event in runtime_events
    ][:2] == [
        RuntimeMode.ONLINE.value,
        RuntimeMode.OFFLINE.value,
    ]

    snapshot = runtime_state.snapshot()

    assert snapshot.mode == RuntimeMode.OFFLINE

    health_snapshot = health.runtime_snapshot()

    assert health_snapshot.network_online is False
    assert health_snapshot.runtime_mode == RuntimeMode.OFFLINE
