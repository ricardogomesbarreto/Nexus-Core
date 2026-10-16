"""Open a small, fixed set of desktop applications after user confirmation."""

import os
import subprocess

from nexus.security import RiskLevel
from nexus.tools.base import NexusTool, ToolResult
from nexus.tools.contracts import FieldSpec, ToolContract, ValueKind


class LaunchApplicationTool(NexusTool):
    name = "launch_application"
    description = "Abre navegador, gerenciador de arquivos ou terminal sem executar comandos."
    risk_level = RiskLevel.MEDIUM
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(FieldSpec("application", ValueKind.STRING, nonempty=True),),
        outputs=(FieldSpec("application", ValueKind.STRING),),
    )

    # Never accept an executable name or arguments supplied by the model.
    APPLICATIONS = {
        "browser": ("firefox", "chromium", "chromium-browser"),
        "files": ("nautilus", "thunar", "dolphin"),
        "terminal": ("gnome-terminal", "konsole", "xfce4-terminal"),
    }
    SYSTEM_BIN_DIRS = ("/usr/bin", "/bin", "/snap/bin")
    ENVIRONMENT = (
        "HOME", "USER", "LOGNAME", "PATH", "LANG", "LC_ALL", "LC_CTYPE",
        "DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR", "XDG_SESSION_TYPE",
        "XDG_CURRENT_DESKTOP", "DBUS_SESSION_BUS_ADDRESS", "XAUTHORITY",
    )

    def sensitive_resources(self, **kwargs):
        # This tool selects a built-in application; it never reads user paths.
        return ()

    def execute(self, application: str, **kwargs) -> ToolResult:
        if application not in self.APPLICATIONS:
            return ToolResult(False, self.name, error="Aplicativo não permitido. Escolha browser, files ou terminal.")
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return ToolResult(False, self.name, error="Sessão gráfica Linux indisponível.")
        binary = next(
            (candidate for name in self.APPLICATIONS[application]
             for directory in self.SYSTEM_BIN_DIRS
             if os.path.isfile(candidate := os.path.join(directory, name))
             and os.access(candidate, os.X_OK)),
            None,
        )
        if binary is None:
            return ToolResult(False, self.name, error="Nenhum aplicativo compatível foi encontrado.")
        try:
            subprocess.Popen(
                [binary], stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, close_fds=True, start_new_session=True,
                env={key: os.environ[key] for key in self.ENVIRONMENT if key in os.environ},
            )
        except OSError as exc:
            return ToolResult(False, self.name, error=f"Não foi possível abrir o aplicativo: {type(exc).__name__}.")
        return ToolResult(True, self.name, data={"application": application})
