class EventType:
    """
    Catálogo oficial de eventos do Nexus.
    """

    SYSTEM_START = "system.start"
    SYSTEM_STOP = "system.stop"

    TEXT_COMMAND = "command.text"
    VOICE_COMMAND = "command.voice"

    TASK_STARTED = "task.started"
    TASK_COMPLETED = "task.completed"
    TASK_FAILED = "task.failed"

    SCREEN_CAPTURED = "screen.captured"
    VISION_RESULT = "vision.result"

    MEMORY_CREATED = "memory.created"
    MEMORY_RECALLED = "memory.recalled"

    SECURITY_REQUEST = "security.request"
    SECURITY_APPROVED = "security.approved"
    SECURITY_DENIED = "security.denied"

    DEVICE_CONNECTED = "device.connected"
    DEVICE_DISCONNECTED = "device.disconnected"

    NETWORK_ONLINE = "network.online"
    NETWORK_OFFLINE = "network.offline"
    RUNTIME_MODE_CHANGED = "runtime.mode_changed"
