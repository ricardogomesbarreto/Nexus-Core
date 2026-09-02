from nexus.security import SecurityGate
from nexus.tools import (
    ListDirectoryTool,
    SystemInfoTool,
    ToolExecutor,
    ToolRegistry,
)


def main():
    registry = ToolRegistry()

    registry.register(
        SystemInfoTool()
    )

    registry.register(
        ListDirectoryTool()
    )

    security_gate = SecurityGate()

    executor = ToolExecutor(
        registry=registry,
        security_gate=security_gate,
    )

    print()
    print("TOOLS DISPONÍVEIS")
    print("=" * 50)

    for tool in registry.list_tools():
        print(f"✓ {tool}")

    print()
    print("SYSTEM INFO")
    print("=" * 50)

    result = executor.execute(
        "system_info"
    )

    if result.success:
        print(result.data)
    else:
        print(result.error)

    print()
    print("DIRETÓRIO")
    print("=" * 50)

    result = executor.execute(
        "list_directory",
        path=".",
    )

    if result.success:

        for item in result.data["items"]:
            print(
                f"{item['type']:10} "
                f"{item['name']}"
            )

    else:
        print(result.error)


if __name__ == "__main__":
    main()
