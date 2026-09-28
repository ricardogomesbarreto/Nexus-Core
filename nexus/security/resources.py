from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class SensitiveResource:
    """Caminho do host que uma ferramenta precisa acessar."""

    name: str
    path: str | Path

    def __post_init__(self) -> None:
        if not isinstance(self.name, str) or not self.name.strip():
            raise ValueError("Nome do recurso sensível inválido")

        if not isinstance(self.path, (str, Path)):
            raise TypeError("Caminho do recurso sensível inválido")

        if not str(self.path).strip():
            raise ValueError("Caminho do recurso sensível vazio")
