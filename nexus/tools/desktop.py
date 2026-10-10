"""Structured, SecurityGate-mediated desktop actions.

Tool contracts are authoritative. Desktop navigation and typing can affect
GUI state, are MEDIUM risk, and require explicit confirmation per action.
No arbitrary mouse positions, key combos, URL visits or commands.
"""
from nexus.security import RiskLevel
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ToolContract, ValueKind
from nexus.automation.x11 import DesktopAutomationError, X11DesktopBackend


class DesktopWindowInfoTool(NexusTool):
    name = "desktop_window_info"
    description = (
        "Consulta ID, título, PID e classe da janela ativa Linux X11; "
        "não captura pixels nem opera controles."
    )
    risk_level = RiskLevel.LOW
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        outputs=(
            FieldSpec("window_id", ValueKind.INTEGER),
            FieldSpec("window_title", ValueKind.STRING),
            FieldSpec("window_pid", ValueKind.INTEGER),
            FieldSpec("window_class", ValueKind.STRING),
        ),
    )

    def __init__(self, backend=None):
        self.backend = backend if backend is not None else X11DesktopBackend()

    def sensitive_resources(self, **kwargs):
        return ()

    def execute(self, **kwargs):
        try:
            ident, title, pid, window_class = self.backend.active_window()
            return ToolResult(True, self.name, data={
                "window_id": ident, "window_title": title,
                "window_pid": pid, "window_class": window_class,
            })
        except DesktopAutomationError as exc:
            return ToolResult(False, self.name, error=str(exc),
                              error_code="X11_UNAVAILABLE")



class DesktopNavigateTool(NexusTool):
    """One whitelisted key action to a specific X11 window per approval."""

    name = "desktop_navigate"
    description = (
        "Navega na janela X11 identificada com UMA tecla predefinida: "
        "next_field, previous_field, page_up ou page_down. "
        "Requer autorização humana por operação; não envia Enter ou atalhos."
    )
    risk_level = RiskLevel.MEDIUM
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(
            FieldSpec("window_id", ValueKind.INTEGER),
            FieldSpec("window_title", ValueKind.STRING, nonempty=True),
            FieldSpec("window_pid", ValueKind.INTEGER),
            FieldSpec("window_class", ValueKind.STRING, nonempty=True),
            FieldSpec("action", ValueKind.STRING, nonempty=True),
        ),
        outputs=(
            FieldSpec("window_id", ValueKind.INTEGER),
            FieldSpec("action", ValueKind.STRING),
        ),
    )

    def __init__(self, backend=None):
        self.backend = backend if backend is not None else X11DesktopBackend()

    def sensitive_resources(self, **kwargs):
        X11DesktopBackend.validate_id(kwargs["window_id"])
        X11DesktopBackend.validate_title(kwargs["window_title"])
        X11DesktopBackend.validate_pid(kwargs["window_pid"])
        X11DesktopBackend.validate_class(kwargs["window_class"])
        X11DesktopBackend.validate_navigation(kwargs["action"])
        return ()

    def execute(self, *, window_id: int, window_title: str,
                window_pid: int, window_class: str, action: str):
        try:
            completed = self.backend.navigate(
                window_id=window_id, window_title=window_title,
                window_pid=window_pid, window_class=window_class, action=action,
            )
            return ToolResult(True, self.name, data={
                "window_id": window_id, "action": completed,
            })
        except DesktopAutomationError as exc:
            return ToolResult(
                False, self.name, error=str(exc), error_code="DESKTOP_DENIED"
            )

class DesktopTypeTextTool(NexusTool):
    name = "desktop_type_text"
    description = (
        "Digita texto curto na janela X11 identificada por ID/título/PID/classe, "
        "sem Enter, após confirmação humana por ação; não executa comandos."
    )
    risk_level = RiskLevel.MEDIUM
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(
            FieldSpec("window_id", ValueKind.INTEGER),
            FieldSpec("window_title", ValueKind.STRING, nonempty=True),
            FieldSpec("window_pid", ValueKind.INTEGER),
            FieldSpec("window_class", ValueKind.STRING, nonempty=True),
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
        X11DesktopBackend.validate_pid(kwargs["window_pid"])
        X11DesktopBackend.validate_class(kwargs["window_class"])
        X11DesktopBackend.validate_text(kwargs["text"])
        return ()

    def execute(self, *, window_id: int, window_title: str,
                window_pid: int, window_class: str, text: str):
        try:
            count = self.backend.type_text(
                window_id=window_id, window_title=window_title,
                window_pid=window_pid, window_class=window_class, text=text,
            )
            return ToolResult(True, self.name, data={
                "window_id": window_id,
                "sent_characters": count,
            })
        except DesktopAutomationError as exc:
            return ToolResult(False, self.name, error=str(exc),
                              error_code="DESKTOP_DENIED")
