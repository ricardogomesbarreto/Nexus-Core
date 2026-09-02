from nexus.config.settings import settings
from nexus.core.application import NexusApplication


def main():
    app = NexusApplication()

    app.initialize()

    health = app.status()

    print()
    print("╔══════════════════════════════════════════════╗")
    print("║                 N E X U S                    ║")
    print(f"║                 v{settings.version:<19}║")
    print("╠══════════════════════════════════════════════╣")

    print(
        f"║ Core             {'✓ ONLINE' if health.core else '✗ ERROR':<22}║"
    )

    print(
        f"║ Configuration    {'✓ READY' if health.configuration else '✗ ERROR':<22}║"
    )

    print(
        f"║ Database         {'✓ READY' if health.database else '✗ ERROR':<22}║"
    )

    print(
        f"║ Logger           {'✓ READY' if health.logger else '✗ ERROR':<22}║"
    )

    print(
        f"║ EventBus         {'✓ READY' if health.event_bus else '✗ ERROR':<22}║"
    )

    print(
        f"║ SecurityGate     {'✓ READY' if health.security_gate else '✗ ERROR':<22}║"
    )

    print(
        f"║ ToolRegistry     {'✓ READY' if health.tool_registry else '✗ ERROR':<22}║"
    )

    print(
        f"║ Terminal Sandbox {'✓ READY' if health.terminal_sandbox else '✗ ERROR':<22}║"
    )

    print("╠══════════════════════════════════════════════╣")

    print(
        f"║ Health Monitor   {'✓ READY' if health.ready else '✗ ERROR':<22}║"
    )

    print("╠══════════════════════════════════════════════╣")
    print(f"║ Node: {settings.node_name:<35}║")
    print("║ Mode: OFFLINE                                ║")
    print("╚══════════════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
