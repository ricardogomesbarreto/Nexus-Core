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
    actions.add_argument(
        "--platform-check", action="store_true",
        help="diagnóstico passivo Ubuntu/Linux, sem alterar o sistema",
    )
    actions.add_argument(
        "--ubuntu-doctor", action="store_true",
        help="verifica PostgreSQL e Ollama somente no loopback local, sem alterações",
    )
    actions.add_argument(
        "--voice-check", action="store_true",
        help="diagnostica dependências locais de voz sem gravar áudio",
    )
    actions.add_argument("--desktop-check", action="store_true",
                         help="diagnostica suporte X11/xdotool sem interagir com janelas")
    actions.add_argument("--devices-check", action="store_true",
                         help="mostra o contrato de dispositivos sem buscar hardware")
    actions.add_argument("--devices-preview-stdin", action="store_true",
                         help="valida manifesto JSON de dispositivos por entrada padrão (sem conexão)")
    actions.add_argument("--vision-check", action="store_true",
                         help="diagnostica dependências de visão sem capturar nada")
    actions.add_argument("--vision-image", metavar="PATH",
                         help="analisa imagem PNG/JPEG/WEBP autorizada no HOME")
    actions.add_argument("--vision-screen", action="store_true",
                         help="captura e analisa uma única imagem de tela")
    actions.add_argument("--vision-camera", type=int, metavar="INDEX",
                         help="captura um único quadro da câmera 0 a 9")
    parser.add_argument("--vision-question", metavar="TEXT",
                        help="pergunta para o modelo visual local")
    parser.add_argument("--vision-model", default="gemma3:4b",
                        help="nome do modelo visual Ollama já instalado")
    actions.add_argument("--memory-add", metavar="TEXT", help="salva explicitamente uma memória local")
    actions.add_argument("--memory-add-stdin", action="store_true", help="salva texto lido da entrada padrão, sem argumento visível")
    actions.add_argument("--memory-list", action="store_true", help="lista memórias não expiradas")
    actions.add_argument("--memory-search", metavar="TEXT", help="procura memórias locais")
    actions.add_argument("--memory-delete", metavar="ID", type=int, help="exclui memória por identificador")
    actions.add_argument("--memory-clear", action="store_true", help="exclui todas as memórias com confirmação")
    actions.add_argument("--memory-status", action="store_true", help="resumo sem conteúdo da memória")
    actions.add_argument("--knowledge-import", metavar="PATH", help="indexa .txt/.md autorizado (somente HOME)")
    actions.add_argument("--knowledge-list", action="store_true", help="lista documentos indexados")
    actions.add_argument("--knowledge-search", metavar="TEXT", help="pesquisa trechos de documentos")
    actions.add_argument("--knowledge-delete", metavar="ID", type=int, help="remove documento e trechos indexados")
    actions.add_argument("--knowledge-context", metavar="TEXT", help="recupera trechos de conhecimento explicitamente")
    parser.add_argument("--knowledge-limit", type=int, default=5, help="resultados: 1 a 20")
    parser.add_argument("--knowledge-with-memory", action="store_true",
                        help="inclui memórias explícitas em --knowledge-context")
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
    knowledge_actions = (
        args.knowledge_import is not None, args.knowledge_list,
        args.knowledge_search is not None, args.knowledge_delete is not None,
        args.knowledge_context is not None,
    )
    if sum(knowledge_actions) > 1 or (has_memory_action and any(knowledge_actions)):
        parser.error("Ações de memória e conhecimento devem ser executadas separadamente")
    if args.knowledge_with_memory and args.knowledge_context is None:
        parser.error("--knowledge-with-memory exige --knowledge-context")
    if not 1 <= args.knowledge_limit <= 20:
        parser.error("--knowledge-limit deve estar entre 1 e 20")
    if args.knowledge_limit != 5 and not any(knowledge_actions):
        parser.error("--knowledge-limit exige ação de conhecimento")
    if args.ubuntu_doctor:
        if (has_memory_action or any(knowledge_actions)
                or args.knowledge_with_memory or args.vision_question is not None
                or args.vision_model != "gemma3:4b" or args.workspace is not None
                or args.memory_confirm or args.memory_days != 90
                or args.knowledge_limit != 5):
            parser.error("--ubuntu-doctor deve ser executado isoladamente")
        from nexus.platforms import ubuntu_doctor
        print(json.dumps(ubuntu_doctor(), ensure_ascii=False))
        return
    if args.platform_check:
        if (has_memory_action or any(knowledge_actions)
                or args.knowledge_with_memory or args.vision_question is not None
                or args.vision_model != "gemma3:4b" or args.workspace is not None
                or args.memory_confirm or args.memory_days != 90
                or args.knowledge_limit != 5):
            parser.error("--platform-check é diagnóstico isolado e não aceita outras opções")
        from nexus.platforms import platform_capabilities
        print(json.dumps(platform_capabilities(), ensure_ascii=False))
        return
    if args.desktop_check:
        if (has_memory_action or any(knowledge_actions)
                or args.knowledge_with_memory or args.vision_question is not None
                or args.vision_model != "gemma3:4b"):
            parser.error("--desktop-check não aceita opções de memória, conhecimento ou visão")
        from nexus.automation import desktop_capabilities
        print(json.dumps(desktop_capabilities(), ensure_ascii=False))
        return
    if args.devices_check or args.devices_preview_stdin:
        if (has_memory_action or any(knowledge_actions) or args.knowledge_with_memory
                or args.vision_question is not None or args.vision_model != "gemma3:4b"
                or args.knowledge_limit != 5 or args.memory_days != 90
                or args.memory_confirm or args.workspace is not None):
            parser.error("Dispositivos não podem ser combinados com outras ações")
        from nexus.devices import (
            DeviceContractError, device_capabilities,
            parse_manifest, preview_manifest,
        )
        if args.devices_check:
            print(json.dumps(device_capabilities(), ensure_ascii=False))
            return
        # Bounded input; never log or echo the untrusted manifest.
        from nexus.devices.contracts import MAX_MANIFEST_BYTES
        raw = sys.stdin.read(MAX_MANIFEST_BYTES + 1)
        try:
            data = preview_manifest(parse_manifest(raw))
        except DeviceContractError as exc:
            parser.error(str(exc))
        print(json.dumps(data, ensure_ascii=False))
        return
    vision_actions = (
        args.vision_check, args.vision_image is not None,
        args.vision_screen, args.vision_camera is not None,
    )
    if any(vision_actions) and (has_memory_action or any(knowledge_actions)
                                or args.knowledge_with_memory):
        parser.error("Visão não pode ser combinada com memória ou conhecimento")
    if not any(vision_actions) and (
        args.vision_question is not None or args.vision_model != "gemma3:4b"
    ):
        parser.error("--vision-question e --vision-model exigem fonte visual")
    if args.vision_check and (
        args.vision_question is not None or args.vision_model != "gemma3:4b"
    ):
        parser.error("--vision-check não aceita pergunta ou modelo")
    if any(vision_actions):
        from nexus.vision.cli import execute_vision
        code = execute_vision(args)
        if code:
            raise SystemExit(code)
        return
    if args.voice_check:
        if has_memory_action or any(knowledge_actions) or args.knowledge_with_memory:
            parser.error("--voice-check não pode ser combinado com memória ou conhecimento")
        from nexus.voice.diagnostics import inspect_voice
        print(json.dumps(inspect_voice(), ensure_ascii=False))
        return
    if has_memory_action:
        from nexus.memory.cli import execute_memory_command
        code = execute_memory_command(args)
        if code:
            raise SystemExit(code)
        return
    if any(knowledge_actions):
        from nexus.knowledge.cli import execute_knowledge_command
        code = execute_knowledge_command(args)
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
