import subprocess
from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.tools.base import NexusTool, ToolResult


class TerminalSandboxTool(NexusTool):
    """
    Executa comandos dentro de um container Docker isolado.

    O container:
    - não possui acesso à rede;
    - utiliza filesystem somente leitura;
    - possui /tmp temporário;
    - possui limites de CPU e memória;
    - possui limite de processos;
    - não recebe novos privilégios;
    - remove-se automaticamente após a execução.
    """

    name = "terminal_sandbox"

    description = (
        "Executa um comando de terminal dentro de um "
        "sandbox Docker isolado."
    )

    risk_level = RiskLevel.MEDIUM

    IMAGE = "ubuntu:24.04"

    MEMORY_LIMIT = "256m"
    CPU_LIMIT = "0.5"
    PIDS_LIMIT = "64"

    TIMEOUT_SECONDS = 30
    MAX_OUTPUT_SIZE = 64 * 1024

    def sensitive_resources(
        self,
        **kwargs,
    ) -> tuple[SensitiveResource, ...]:
        workspace = kwargs.get("workspace")
        if workspace is None:
            return ()
        return (SensitiveResource("workspace", workspace),)

    def execute(
        self,
        command: str,
        workspace: str | None = None,
        **kwargs,
    ) -> ToolResult:

        if not isinstance(command, str) or not command.strip():
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="Comando não informado.",
            )

        workspace_path = None

        if workspace is not None:

            try:
                workspace_path = (
                    Path(workspace)
                    .expanduser()
                    .resolve()
                )

            except OSError as error:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error=f"Workspace inválido: {error}",
                )

            if not workspace_path.exists():
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="Workspace não encontrado.",
                )

            if not workspace_path.is_dir():
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="Workspace não é um diretório.",
                )

        docker_command = [
            "docker",
            "run",
            "--rm",
            "--network",
            "none",
            "--memory",
            self.MEMORY_LIMIT,
            "--cpus",
            self.CPU_LIMIT,
            "--pids-limit",
            self.PIDS_LIMIT,
            "--read-only",
            "--tmpfs",
            "/tmp:rw,noexec,nosuid,size=64m",
            "--security-opt",
            "no-new-privileges",
            "--cap-drop",
            "ALL",
            "--user",
            "1000:1000",
        ]

        if workspace_path is not None:
            docker_command.extend(
                [
                    "--mount",
                    (
                        "type=bind,"
                        f"src={workspace_path},"
                        "dst=/workspace,"
                        "readonly"
                    ),
                    "--workdir",
                    "/workspace",
                ]
            )

        docker_command.extend(
            [
                self.IMAGE,
                "/bin/bash",
                "-c",
                command,
            ]
        )

        try:
            process = subprocess.run(
                docker_command,
                capture_output=True,
                text=True,
                timeout=self.TIMEOUT_SECONDS,
                check=False,
            )

        except FileNotFoundError:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="Docker não encontrado no sistema.",
            )

        except subprocess.TimeoutExpired:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=(
                    "Execução interrompida: "
                    "tempo limite de 30 segundos excedido."
                ),
            )

        except OSError as error:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=str(error),
            )

        stdout = process.stdout or ""
        stderr = process.stderr or ""

        output = stdout[: self.MAX_OUTPUT_SIZE]

        if len(stdout) > self.MAX_OUTPUT_SIZE:
            output += "\n[SAÍDA TRUNCADA]"

        error_output = stderr[: self.MAX_OUTPUT_SIZE]

        data = {
            "command": command,
            "exit_code": process.returncode,
            "stdout": output,
            "stderr": error_output,
            "workspace": (
                str(workspace_path)
                if workspace_path is not None
                else None
            ),
        }

        if process.returncode != 0:
            return ToolResult(
                success=False,
                tool_name=self.name,
                data=data,
                error=(
                    f"Comando terminou com código "
                    f"{process.returncode}."
                ),
            )

        return ToolResult(
            success=True,
            tool_name=self.name,
            data=data,
        )
