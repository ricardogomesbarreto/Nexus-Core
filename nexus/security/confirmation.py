import sys
from pathlib import Path
from typing import Protocol, TextIO

from nexus.security.security_gate import SecurityRequest


class ConfirmationHandler(Protocol):
    """Obtém autorização humana para uma operação já avaliada pelo gate."""

    def confirm(self, request: SecurityRequest) -> bool:
        ...


class ConsoleConfirmation:
    """Confirma uma operação no terminal local; ausência de TTY nega."""

    def __init__(
        self,
        input_stream: TextIO | None = None,
        output_stream: TextIO | None = None,
    ) -> None:
        self.input_stream = input_stream or sys.stdin
        self.output_stream = output_stream or sys.stderr

    @staticmethod
    def _display(value: str | Path) -> str:
        # Escapa quebras de linha e códigos de controle antes de imprimir
        # conteúdo fornecido pelo chamador no terminal do usuário.
        return "".join(
            char if char.isprintable() else f"\\u{ord(char):04x}"
            for char in str(value)
        )

    def confirm(self, request: SecurityRequest) -> bool:
        if not self.input_stream.isatty() or not self.output_stream.isatty():
            return False

        self.output_stream.write(
            "\nNexus Core: autorização necessária\n"
            f"Ferramenta: {self._display(request.tool_name or 'unknown')}\n"
            f"Operação: {self._display(request.description)}\n"
            f"Risco: {request.risk_level.name}\n"
        )
        for resource in request.resources:
            self.output_stream.write(
                f"Recurso {self._display(resource.name)}: "
                f"{self._display(resource.path)}\n"
            )

        if isinstance(request.data, dict):
            command = request.data.get("command")
            if isinstance(command, str):
                self.output_stream.write(
                    f"Comando: {self._display(command)}\n"
                )

        self.output_stream.write("Autorizar esta execução? Digite sim: ")
        self.output_stream.flush()
        return self.input_stream.readline().strip().casefold() == "sim"
