from nexus.events import EventType


def test_network_events():
    assert EventType.NETWORK_ONLINE == "network.online"
    assert EventType.NETWORK_OFFLINE == "network.offline"


def test_runtime_mode_changed_event():
    assert EventType.RUNTIME_MODE_CHANGED == "runtime.mode_changed"
