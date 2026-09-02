from nexus.config.settings import settings
from nexus.core.application import NexusApplication


def main():
    app = NexusApplication()

    app.initialize()

    health = app.status()

    print()
    print("╔══════════════════════════════════════╗")
    print("║              N E X U S               ║")
    print(f"║              v{settings.version}                  ║")
    print("╠══════════════════════════════════════╣")

    print(
        f"║ Core             {'✓ ONLINE' if health.core else '✗ ERROR':<18}║"
    )

    print(
        f"║ Configuration    {'✓ READY' if health.configuration else '✗ ERROR':<18}║"
    )

    print(
        f"║ Database         {'✓ READY' if health.database else '✗ ERROR':<18}║"
    )

    print(
        f"║ Logger           {'✓ READY' if health.logger else '✗ ERROR':<18}║"
    )

    print(
        f"║ Health Monitor   {'✓ READY' if health.ready else '✗ ERROR':<18}║"
    )

    print("╠══════════════════════════════════════╣")
    print(f"║ Node: {settings.node_name:<28}║")
    print(
        f"║ Mode: {'OFFLINE':<29}║"
    )
    print("╚══════════════════════════════════════╝")
    print()


if __name__ == "__main__":
    main()
