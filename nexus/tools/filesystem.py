from pathlib import Path

from nexus.security import RiskLevel, SensitiveResource
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ResourceSpec, ToolContract, ValueKind


class ListDirectoryTool(NexusTool):
    """
    Lista o conteúdo de um diretório.
    """

    name = "list_directory"

    description = (
        "Lista arquivos e diretórios "
        "de um caminho especificado."
    )

    risk_level = RiskLevel.SAFE

    contract = ToolContract(
        name=name,
        description=description,
        permission=risk_level,
        inputs=(
            FieldSpec(
                "path", ValueKind.STRING,
                required=False, default=".", nonempty=True,
            ),
        ),
        resources=(ResourceSpec("directory", "path"),),
        outputs=(
            FieldSpec("path", ValueKind.STRING),
            FieldSpec(
                "items", ValueKind.ARRAY,
                item_fields=(
                    FieldSpec("name", ValueKind.STRING),
                    FieldSpec("type", ValueKind.STRING),
                ),
            ),
        ),
    )

    def sensitive_resources(
        self,
        **kwargs,
    ) -> tuple[SensitiveResource, ...]:
        return (
            SensitiveResource("directory", kwargs.get("path", ".")),
        )

    def execute(
        self,
        path: str = ".",
        **kwargs,
    ) -> ToolResult:

        try:
            directory = Path(path).expanduser().resolve()

            if not directory.exists():
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="Diretório não encontrado.",
                )

            if not directory.is_dir():
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="O caminho não é um diretório.",
                )

            items = []

            for item in sorted(
                directory.iterdir(),
                key=lambda x: x.name.lower(),
            ):
                items.append(
                    {
                        "name": item.name,
                        "type": (
                            "directory"
                            if item.is_dir()
                            else "file"
                        ),
                    }
                )

            return ToolResult(
                success=True,
                tool_name=self.name,
                data={
                    "path": str(directory),
                    "items": items,
                },
            )

        except PermissionError:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="Permissão negada.",
            )

        except OSError as error:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=str(error),
            )


class ReadFileTool(NexusTool):
    """
    Lê o conteúdo de um arquivo de texto.

    O acesso ao caminho é controlado pelo SecurityGate
    antes da execução da ferramenta.
    """

    name = "read_file"

    description = (
        "Lê o conteúdo de um arquivo de texto "
        "em uma área autorizada."
    )

    risk_level = RiskLevel.SAFE

    contract = ToolContract(
        name=name,
        description=description,
        permission=risk_level,
        inputs=(FieldSpec("path", ValueKind.STRING, nonempty=True),),
        resources=(ResourceSpec("file", "path"),),
        outputs=(
            FieldSpec("path", ValueKind.STRING),
            FieldSpec("size", ValueKind.INTEGER),
            FieldSpec("content", ValueKind.STRING),
        ),
    )

    MAX_FILE_SIZE = 1024 * 1024

    def sensitive_resources(
        self,
        **kwargs,
    ) -> tuple[SensitiveResource, ...]:
        return (
            SensitiveResource("file", kwargs["path"]),
        )

    def execute(
        self,
        path: str,
        **kwargs,
    ) -> ToolResult:

        try:
            file_path = Path(path).expanduser().resolve()

            if not file_path.exists():
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="Arquivo não encontrado.",
                )

            if not file_path.is_file():
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error="O caminho não é um arquivo.",
                )

            file_size = file_path.stat().st_size

            if file_size > self.MAX_FILE_SIZE:
                return ToolResult(
                    success=False,
                    tool_name=self.name,
                    error=(
                        "Arquivo excede o limite máximo "
                        "de leitura de 1 MB."
                    ),
                )

            content = file_path.read_text(
                encoding="utf-8"
            )

            return ToolResult(
                success=True,
                tool_name=self.name,
                data={
                    "path": str(file_path),
                    "size": file_size,
                    "content": content,
                },
            )

        except UnicodeDecodeError:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=(
                    "O arquivo não parece ser um "
                    "arquivo de texto UTF-8."
                ),
            )

        except PermissionError:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="Permissão negada.",
            )

        except OSError as error:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error=str(error),
            )
