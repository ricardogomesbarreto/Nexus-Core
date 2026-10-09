"""Small, opt-in X11 automation adapter (no shell, clipboard or screenshots).

This is intentionally *not* unrestricted computer control. One requested
text insertion per approved ToolExecutor call into an exactly identified,
currently active X11 window; Wayland/XWayland sessions fail closed.
"""
import os
import re
import shutil
import subprocess


class DesktopAutomationError(RuntimeError):
    """Desktop automation failure without raw subprocess output."""


class X11DesktopBackend:
    MAX_TITLE = 200
    MAX_TEXT = 300
    MAX_WINDOW_ID = 2**32 - 1
    MAX_QUERY_BYTES = 4096
    COMMAND_TIMEOUT = 5
    TYPE_TIMEOUT = 12

    def __init__(self, binary: str | None = None):
        self._binary = binary

    def _command(self) -> str:
        if os.environ.get("WAYLAND_DISPLAY") or (
            os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        ):
            raise DesktopAutomationError(
                "Automação de teclado disponível somente em uma sessão X11."
            )
        if not os.environ.get("DISPLAY"):
            raise DesktopAutomationError("Não há display X11 configurado.")
        binary = self._binary if self._binary is not None else shutil.which("xdotool")
        if not binary:
            raise DesktopAutomationError("Instale xdotool para automação X11.")
        return binary

    @classmethod
    def validate_id(cls, value) -> int:
        if type(value) is not int or not 1 <= value <= cls.MAX_WINDOW_ID:
            raise DesktopAutomationError("Identificador X11 inválido.")
        return value

    @classmethod
    def validate_title(cls, title) -> str:
        if (
            type(title) is not str or not title.strip()
            or len(title) > cls.MAX_TITLE
            or not all(ch.isprintable() for ch in title)
        ):
            raise DesktopAutomationError("Título de janela X11 inválido.")
        return title

    @classmethod
    def validate_text(cls, content) -> str:
        if (
            type(content) is not str or not content.strip()
            or len(content) > cls.MAX_TEXT
            or not all(ch.isprintable() for ch in content)
        ):
            raise DesktopAutomationError(
                "Texto inválido: máximo de 300 caracteres imprimíveis, sem Enter."
            )
        return content

    def _query(self, *args: str) -> str:
        cmd = [self._command(), *args]
        try:
            result = subprocess.run(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
                stderr=subprocess.DEVNULL, timeout=self.COMMAND_TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DesktopAutomationError("Consulta X11 local falhou.") from exc
        if result.returncode != 0 or len(result.stdout) > self.MAX_QUERY_BYTES:
            raise DesktopAutomationError("Consulta X11 local indisponível.")
        try:
            return result.stdout.decode("utf-8", errors="strict").rstrip("\r\n")
        except UnicodeDecodeError as exc:
            raise DesktopAutomationError("Título de janela X11 inválido.") from exc

    def active_window(self) -> tuple[int, str]:
        raw = self._query("getactivewindow")
        if not re.fullmatch(r"[0-9]{1,10}", raw):
            raise DesktopAutomationError("Identificador de janela X11 inválido.")
        ident = self.validate_id(int(raw))
        title = self.validate_title(self._query("getwindowname", str(ident)))
        return ident, title

    def type_text(self, *, window_id: int, window_title: str, text: str) -> int:
        ident = self.validate_id(window_id)
        title = self.validate_title(window_title)
        value = self.validate_text(text)
        # SecurityGate already obtained explicit user approval; independently
        # recheck the *same target* after that dialog has closed.
        current_id, current_title = self.active_window()
        if (current_id, current_title) != (ident, title):
            raise DesktopAutomationError(
                "A janela ativa mudou após a autorização. Nenhum texto digitado."
            )
        # Fixed window ID prevents a focus change from redirecting keystrokes
        # to another application. No shell, newline or keyboard shortcuts.
        cmd = [self._command(), "type", "--window", str(ident),
               "--clearmodifiers", "--delay", "2", "--", value]
        try:
            result = subprocess.run(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=self.TYPE_TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DesktopAutomationError(
                "Não foi possível concluir a digitação X11; verifique a janela."
            ) from exc
        if result.returncode != 0:
            raise DesktopAutomationError(
                "Digitação X11 falhou ou foi parcialmente executada."
            )
        return len(value)


def desktop_capabilities() -> dict:
    """Read-only readiness report; does not connect to X11 or press keys."""
    return {
        "platform": "Linux X11 only",
        "session_x11": bool(os.environ.get("DISPLAY"))
            and not bool(os.environ.get("WAYLAND_DISPLAY"))
            and os.environ.get("XDG_SESSION_TYPE", "").lower() != "wayland",
        "xdotool": bool(shutil.which("xdotool")),
        "effects": "read window title or type single approved text",
        "camera_access": False,
        "screenshot_access": False,
        "wayland_supported": False,
    }
