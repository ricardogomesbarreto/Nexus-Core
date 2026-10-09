"""Structured, SecurityGate-mediated desktop actions.

Tool contracts are authoritative. Only desktop_type_text can affect the GUI;
its MEDIUM risk always requires a fresh human confirmation under default
policy. No arbitrary mouse positions, key combos, URL visits or commands.
"""
from nexus.security import RiskLevel
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ToolContract, ValueKind
from nexus.automation.x11 import DesktopAutomationError, X11DesktopBackend


class DesktopWindowInfoTool(NexusTool):
    name = "desktop_window_info"
    description = (
        "Consulta apenas identificador e título da janela ativa Linux X11; "
        "não captura pixels nem opera controles."
    )
    risk_level = RiskLevel.LOW
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        outputs=(
            FieldSpec("window_id", ValueKind.INTEGER),
            FieldSpec("window_title", ValueKind.STRING),
        ),
    )

    def __init__(self, backend=None):
        self.backend = backend if backend is not None else X11DesktopBackend()

    def sensitive_resources(self, **kwargs):
        return ()

    def execute(self, **kwargs):
        try:
            ident, title = self.backend.active_window()
            return ToolResult(True, self.name, data={
                "window_id": ident, "window_title": title,
            })
        except DesktopAutomationError as exc:
            return ToolResult(False, self.name, error=str(exc),
                              error_code="X11_UNAVAILABLE")


class DesktopTypeTextTool(NexusTool):
    name = "desktop_type_text"
    description = (
        "Digita texto curto na janela X11 explicitamente identificada e ativa, "
        "sem Enter, após confirmação humana por ação; não executa comandos."
    )
    risk_level = RiskLevel.MEDIUM
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(
            FieldSpec("window_id", ValueKind.INTEGER),
            FieldSpec("window_title", ValueKind.STRING, nonempty=True),
            FieldSpec("text", ValueKind.STRING, nonempty=True),
        ),
        outputs=(
            FieldSpec("window_id", ValueKind.INTEGER),
            FieldSpec("sent_characters", ValueKind.INTEGER),
        ),
    )

    def __init__(self, backend=None):
        self.backend = backend if backend is not None else X11DesktopBackend()

    def sensitive_resources(self, **kwargs):
        # Reject malformed targets and content before requesting user consent.
        # X11 IDs are not filesystem paths; runtime checks happen again after
        # confirmation, before xdotool receives any keystrokes.
        X11DesktopBackend.validate_id(kwargs["window_id"])
        X11DesktopBackend.validate_title(kwargs["window_title"])
        X11DesktopBackend.validate_text(kwargs["text"])
        return ()

    def execute(self, *, window_id: int, window_title: str, text: str):
        try:
            count = self.backend.type_text(
                window_id=window_id, window_title=window_title, text=text,
            )
            return ToolResult(True, self.name, data={
                "window_id": window_id,
                "sent_characters": count,
            })
        except DesktopAutomationError as exc:
            return ToolResult(False, self.name, error=str(exc),
                              error_code="DESKTOP_DENIED")
