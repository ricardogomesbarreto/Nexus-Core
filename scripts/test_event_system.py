from nexus.events import EventBus, EventType


def on_voice_command(event):
    print()
    print("EVENTO RECEBIDO")
    print(f"Tipo: {event.event_type}")
    print(f"Dados: {event.data}")
    print(f"Horário: {event.timestamp}")
    print()


bus = EventBus()

bus.subscribe(
    EventType.VOICE_COMMAND,
    on_voice_command,
)

print("Publicando evento...")

bus.publish(
    EventType.VOICE_COMMAND,
    {
        "text": "Nexus, abra o navegador",
        "confidence": 0.97,
    },
)
