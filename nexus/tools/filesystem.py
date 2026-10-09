import os
from pathlib import Path

from nexus.security.paths import PathSecurity

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
    path_security = None  # injected by the executor, never supplied by the model

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
            policy = self.path_security or PathSecurity()
            with policy.open_directory(path) as (directory_fd, directory):
                with os.scandir(directory_fd) as entries:
                    items = [
                        {
                            "name": item.name,
                            "type": "directory" if item.is_dir(follow_symlinks=False) else "file",
                        }
                        for item in entries
                    ]
            items.sort(key=lambda entry: entry["name"].lower())
            return ToolResult(
                success=True, tool_name=self.name,
                data={"path": str(directory), "items": items},
            )
        except PermissionError:
            return ToolResult(
                success=False,
                tool_name=self.name,
                error="Permissão negada.",
            )

        except FileNotFoundError:
            return ToolResult(False, self.name, error="Diretório não encontrado.")
        except NotADirectoryError:
            return ToolResult(False, self.name, error="O caminho não é um diretório.")
        except OSError as error:
            return ToolResult(False, self.name, error=str(error))


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

    path_security = None  # bound to SecurityGate policy by ToolExecutor
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
            policy = self.path_security or PathSecurity()
            with policy.open_regular_file(path) as (fd, file_path):
                file_size = os.fstat(fd).st_size
                if file_size > self.MAX_FILE_SIZE:
                    return ToolResult(
                        False, self.name, error="Arquivo excede o limite máximo de leitura de 1 MB."
                    )
                content_bytes = bytearray()
                while len(content_bytes) <= self.MAX_FILE_SIZE:
                    chunk = os.read(fd, min(65536, self.MAX_FILE_SIZE + 1 - len(content_bytes)))
                    if not chunk:
                        break
                    content_bytes.extend(chunk)
                if len(content_bytes) > self.MAX_FILE_SIZE:
                    return ToolResult(
                        False, self.name, error="Arquivo excede o limite máximo de leitura de 1 MB."
                    )
                content = bytes(content_bytes).decode("utf-8")

            return ToolResult(
                success=True, tool_name=self.name,
                data={"path": str(file_path), "size": file_size, "content": content},
            )

        except UnicodeDecodeError:
            return ToolResult(False, self.name, error="O arquivo não parece ser um arquivo de texto UTF-8.")
        except PermissionError:
            return ToolResult(False, self.name, error="Permissão negada.")
        except FileNotFoundError:
            return ToolResult(False, self.name, error="Arquivo não encontrado.")
        except IsADirectoryError:
            return ToolResult(False, self.name, error="O caminho não é um arquivo.")
        except NotADirectoryError:
            return ToolResult(False, self.name, error="O caminho não é um arquivo.")
        except OSError as error:
            return ToolResult(False, self.name, error=str(error))


class FileMetadataTool(NexusTool):
    """Read metadata of one authorized regular file without reading its contents."""

    name = "file_metadata"
    description = "Consulta tamanho e data de modificação de um arquivo autorizado."
    risk_level = RiskLevel.SAFE
    path_security = None

    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("path", ValueKind.STRING, nonempty=True),),
        resources=(ResourceSpec("file", "path"),),
        outputs=(
            FieldSpec("path", ValueKind.STRING),
            FieldSpec("size", ValueKind.INTEGER),
            FieldSpec("modified_epoch", ValueKind.INTEGER),
        ),
    )

    def sensitive_resources(self, **kwargs) -> tuple[SensitiveResource, ...]:
        return (SensitiveResource("file", kwargs["path"]),)

    def execute(self, path: str, **kwargs) -> ToolResult:
        try:
            policy = self.path_security or PathSecurity()
            with policy.open_regular_file(path) as (fd, file_path):
                file_stat = os.fstat(fd)
                result = {
                    "path": str(file_path),
                    "size": file_stat.st_size,
                    "modified_epoch": int(file_stat.st_mtime),
                }
            return ToolResult(True, self.name, data=result)
        except (PermissionError, OSError) as exc:
            return ToolResult(False, self.name, error=f"Metadados indisponíveis: {type(exc).__name__}.")
