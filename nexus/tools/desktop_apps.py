"""Open a bounded set of desktop applications on the local graphical session."""

import os
import re
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
        "files": ("nautilus", "thunar", "dolphin"),
        "terminal": ("gnome-terminal", "konsole", "xfce4-terminal"),
    }
    SYSTEM_BIN_DIRS = ("/usr/bin", "/bin", "/snap/bin")
    ENVIRONMENT = (
        "HOME", "USER", "LOGNAME", "PATH", "LANG", "LC_ALL", "LC_CTYPE",
        "DISPLAY", "WAYLAND_DISPLAY", "XDG_RUNTIME_DIR", "XDG_SESSION_TYPE",
        "XDG_CURRENT_DESKTOP", "XDG_CONFIG_HOME", "XDG_DATA_HOME",
        "XDG_DATA_DIRS", "DBUS_SESSION_BUS_ADDRESS", "XAUTHORITY",
    )

    def sensitive_resources(self, **kwargs):
        # This tool selects a built-in application; it never reads user paths.
        return ()

    def execute(self, application: str, **kwargs) -> ToolResult:
        if application not in self.APPLICATIONS:
            return ToolResult(False, self.name, error="Aplicativo não permitido. Escolha files ou terminal.")
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


class OpenDefaultBrowserTool(NexusTool):
    """Launch only the desktop's configured browser, without a URL or arguments.

    Opening the browser alone is a low-risk, explicit user request. Navigation,
    typing and reading its content remain separate operations with their own
    permissions. A missing default fails closed; never guess a browser binary.
    """

    name = "open_default_browser"
    description = "Abre somente o navegador padrão configurado no desktop, sem acessar um site."
    risk_level = RiskLevel.LOW
    contract = ToolContract(
        name=name, description=description, permission=risk_level,
        inputs=(), outputs=(FieldSpec("browser_id", ValueKind.STRING),),
    )
    # Desktop file IDs are data, never shell text or arbitrary executable paths.
    _DESKTOP_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}\.desktop\Z")

    def sensitive_resources(self, **kwargs):
        return ()

    @staticmethod
    def _system_binary(name: str) -> str | None:
        return next((path for directory in LaunchApplicationTool.SYSTEM_BIN_DIRS
                     if os.path.isfile(path := os.path.join(directory, name))
                     and os.access(path, os.X_OK)), None)

    def execute(self, **kwargs) -> ToolResult:
        if not (os.environ.get("DISPLAY") or os.environ.get("WAYLAND_DISPLAY")):
            return ToolResult(False, self.name, error="Sessão gráfica Linux indisponível.")
        settings = self._system_binary("xdg-settings")
        launcher = self._system_binary("gtk-launch")
        if not settings or not launcher:
            return ToolResult(False, self.name, error="Instale xdg-utils e libgtk-3-bin para abrir o navegador padrão.")
        environment = {key: os.environ[key] for key in LaunchApplicationTool.ENVIRONMENT
                       if key in os.environ}
        environment["PATH"] = os.pathsep.join(LaunchApplicationTool.SYSTEM_BIN_DIRS)
        try:
            selected = subprocess.run(
                [settings, "get", "default-web-browser"],
                stdin=subprocess.DEVNULL, capture_output=True, text=True,
                timeout=3, check=False, env=environment,
            )
            browser_id = selected.stdout.strip()
            if selected.returncode or not self._DESKTOP_ID.fullmatch(browser_id):
                return ToolResult(False, self.name, error="Navegador padrão não identificado no Ubuntu.")
            subprocess.Popen(
                [launcher, browser_id], stdin=subprocess.DEVNULL,
                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                close_fds=True, start_new_session=True, env=environment,
            )
        except (OSError, subprocess.TimeoutExpired):
            return ToolResult(False, self.name, error="Não foi possível consultar ou abrir o navegador padrão.")
        return ToolResult(True, self.name, data={"browser_id": browser_id})
