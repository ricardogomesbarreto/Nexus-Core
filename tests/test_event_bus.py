from nexus.events import EventBus, EventType


def test_event_bus_publish():
    bus = EventBus()

    received_events = []

    def handler(event):
        received_events.append(event)

    bus.subscribe(
        EventType.TEXT_COMMAND,
        handler,
    )

    event = bus.publish(
        EventType.TEXT_COMMAND,
        {"text": "Olá Nexus"},
    )

    assert event.event_type == EventType.TEXT_COMMAND
    assert event.data["text"] == "Olá Nexus"

    assert len(received_events) == 1
    assert received_events[0] == event


def test_event_bus_unsubscribe():
    bus = EventBus()

    received_events = []

    def handler(event):
        received_events.append(event)

    bus.subscribe(
        EventType.TEXT_COMMAND,
        handler,
    )

    bus.unsubscribe(
        EventType.TEXT_COMMAND,
        handler,
    )

    bus.publish(
        EventType.TEXT_COMMAND,
        {"text": "Teste"},
    )

    assert len(received_events) == 0


def test_event_bus_multiple_handlers():
    bus = EventBus()

    results = []

    def handler_one(event):
        results.append("one")

    def handler_two(event):
        results.append("two")

    bus.subscribe(
        EventType.TASK_STARTED,
        handler_one,
    )

    bus.subscribe(
        EventType.TASK_STARTED,
        handler_two,
    )

    bus.publish(
        EventType.TASK_STARTED,
        {"task": "teste"},
    )

    assert results == ["one", "two"]


def test_event_types_exist():
    assert EventType.SYSTEM_START
    assert EventType.SYSTEM_STOP
    assert EventType.VOICE_COMMAND
    assert EventType.VISION_RESULT
    assert EventType.SECURITY_REQUEST
    assert EventType.DEVICE_CONNECTED
