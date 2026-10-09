import argparse
import json
import sys

from nexus.config.settings import settings
from nexus.core.application import NexusApplication
from nexus.database.database import Database
from nexus.database.factory import build_database_provider
from nexus.security import ConsoleConfirmation


WIDTH = 46


def status_line(label, status):
    return f"║ {label:<17} {status:<25}║"


def build_application(confirmation_handler=None) -> NexusApplication:
    provider = build_database_provider(settings)
    database = Database(provider)

    return NexusApplication(
        database=database,
        confirmation_handler=(
            confirmation_handler if confirmation_handler is not None
            else ConsoleConfirmation()
        ),
    )


def main(
    sandbox_command: str | None = None,
    workspace: str | None = None,
    agent_prompt: str | None = None,
):
    app = build_application()

    try:
        app.initialize()

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

        print(
            status_line(
                "Model Layer",
                "✓ READY"
                if health.model_layer
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

        if agent_prompt is not None:
            outcome = app.agent.run(agent_prompt)
            if outcome.content:
                print(outcome.content)
            if outcome.tool_result is not None:
                print(json.dumps(outcome.tool_result.as_dict(), ensure_ascii=False))
            if not outcome.success:
                print(outcome.error, file=sys.stderr)
                return 1

        if sandbox_command is not None:
            result = app.tool_executor.execute(
                "terminal_sandbox",
                command=sandbox_command,
                workspace=workspace,
            )
            if result.data:
                if result.data.get("stdout"):
                    print(result.data["stdout"], end="")
                if result.data.get("stderr"):
                    print(result.data["stderr"], end="", file=sys.stderr)
            if not result.success:
                print(result.error, file=sys.stderr)
                return 1

        return 0

    finally:
        app.shutdown()


def cli(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="nexus-core",
        description="Nexus Core — assistente local para Linux",
    )
    parser.add_argument(
        "--version",
        action="version",
        version=f"Nexus Core {settings.version}",
    )
    actions = parser.add_mutually_exclusive_group()
    actions.add_argument(
        "--sandbox-command",
        metavar="COMMAND",
        help="executa um comando isolado após confirmação humana",
    )
    actions.add_argument(
        "--agent-prompt",
        metavar="PROMPT",
        help="solicita uma resposta ou uma ação mediada pelo executor",
    )
    actions.add_argument(
        "--desktop", action="store_true",
        help="abre a janela de conversa nativa do Linux",
    )
    actions.add_argument(
        "--status", action="store_true",
        help="exibe o estado do núcleo no terminal",
    )
    actions.add_argument("--memory-add", metavar="TEXT", help="salva explicitamente uma memória local")
    actions.add_argument("--memory-add-stdin", action="store_true", help="salva texto lido da entrada padrão, sem argumento visível")
    actions.add_argument("--memory-list", action="store_true", help="lista memórias não expiradas")
    actions.add_argument("--memory-search", metavar="TEXT", help="procura memórias locais")
    actions.add_argument("--memory-delete", metavar="ID", type=int, help="exclui memória por identificador")
    actions.add_argument("--memory-clear", action="store_true", help="exclui todas as memórias com confirmação")
    actions.add_argument("--memory-status", action="store_true", help="resumo sem conteúdo da memória")
    parser.add_argument("--memory-days", type=int, default=90, help="retenção da nova memória: 1 a 365 dias")
    parser.add_argument("--memory-confirm", action="store_true", help="confirma exclusão total das memórias")
    parser.add_argument(
        "--workspace",
        help="diretório local montado como somente leitura no sandbox",
    )
    args = parser.parse_args(argv)
    if args.workspace is not None and args.sandbox_command is None:
        parser.error("--workspace exige --sandbox-command")
    has_memory_action = any((
        args.memory_add is not None, args.memory_add_stdin, args.memory_list, args.memory_search is not None,
        args.memory_delete is not None, args.memory_clear, args.memory_status,
    ))
    if args.memory_confirm and not args.memory_clear:
        parser.error("--memory-confirm exige --memory-clear")
    if not 1 <= args.memory_days <= 365 or (args.memory_days != 90 and args.memory_add is None and not args.memory_add_stdin):
        parser.error("--memory-days deve ser 1 a 365 e exige --memory-add")
    if has_memory_action:
        from nexus.memory.cli import execute_memory_command
        code = execute_memory_command(args)
        if code:
            raise SystemExit(code)
        return

    if args.desktop or (
        args.sandbox_command is None and args.agent_prompt is None and not args.status
    ):
        from nexus.desktop.window import launch_desktop
        result = launch_desktop()
        if result:
            raise SystemExit(result)
        return

    result = main(args.sandbox_command, args.workspace, args.agent_prompt)
    if result:
        raise SystemExit(result)


if __name__ == "__main__":
    cli()
