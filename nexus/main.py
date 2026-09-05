from nexus.config.settings import settings
from nexus.core.application import NexusApplication


WIDTH = 46


def status_line(label, status):
    return f"║ {label:<17} {status:<25}║"


def main():
    app = NexusApplication()

    app.initialize()

    try:
        health = app.status()
        runtime_snapshot = health.runtime_snapshot()

        runtime_mode = runtime_snapshot.runtime_mode.value

        network_status = (
            "✓ ONLINE"
            if runtime_snapshot.network_online
            else "✗ OFFLINE"
        )

        print()
        print("╔" + "═" * WIDTH + "╗")
        print("║" + " N E X U S ".center(WIDTH) + "║")
        print("║" + f"v{settings.version}".center(WIDTH) + "║")
        print("╠" + "═" * WIDTH + "╣")

        print(
            status_line(
                "Core",
                "✓ ONLINE" if health.core else "✗ ERROR",
            )
        )

        print(
            status_line(
                "Configuration",
                "✓ READY" if health.configuration else "✗ ERROR",
            )
        )

        print(
            status_line(
                "Database",
                "✓ READY" if health.database else "✗ ERROR",
            )
        )

        print(
            status_line(
                "Logger",
                "✓ READY" if health.logger else "✗ ERROR",
            )
        )

        print(
            status_line(
                "EventBus",
                "✓ READY" if health.event_bus else "✗ ERROR",
            )
        )

        print(
            status_line(
                "SecurityGate",
                "✓ READY" if health.security_gate else "✗ ERROR",
            )
        )

        print(
            status_line(
                "ToolRegistry",
                "✓ READY" if health.tool_registry else "✗ ERROR",
            )
        )

        print(
            status_line(
                "Terminal Sandbox",
                "✓ READY"
                if health.terminal_sandbox
                else "✗ ERROR",
            )
        )

        print("╠" + "═" * WIDTH + "╣")

        print(
            status_line(
                "Health Monitor",
                "✓ READY" if health.ready else "✗ ERROR",
            )
        )

        print("╠" + "═" * WIDTH + "╣")

        print(
            status_line(
                "Node",
                settings.node_name,
            )
        )

        print(
            status_line(
                "Network",
                network_status,
            )
        )

        print(
            status_line(
                "Mode",
                runtime_mode,
            )
        )

        print("╚" + "═" * WIDTH + "╝")
        print()

    finally:
        app.shutdown()


if __name__ == "__main__":
    main()
