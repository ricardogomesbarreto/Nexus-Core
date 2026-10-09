"""Small, opt-in X11 automation adapter (no shell, clipboard or screenshots).

This is intentionally *not* unrestricted computer control. One requested
text insertion per approved ToolExecutor call into an exactly identified X11 window; Wayland/XWayland sessions fail closed.
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
    NAVIGATION_KEYS = {
        "next_field": "Tab",
        "previous_field": "ISO_Left_Tab",
        "page_up": "Prior",
        "page_down": "Next",
    }

    @classmethod
    def validate_navigation(cls, action: str) -> str:
        """An explicit allowlist, not an arbitrary xdotool keysym."""
        if type(action) is not str or action not in cls.NAVIGATION_KEYS:
            raise DesktopAutomationError(
                "Navegação inválida: use next_field, previous_field, "
                "page_up ou page_down."
            )
        return action


    def __init__(self, binary: str | None = None):
        self._binary = binary

    def _command(self) -> str:
        if os.environ.get("WAYLAND_DISPLAY") or (
            os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
        ):
            raise DesktopAutomationError(
                "Automação de teclado disponível somente em uma sessão X11."
            )
        display = os.environ.get("DISPLAY", "")
        if not re.fullmatch(r"(?::|unix:)[0-9]+(?:\.[0-9]+)?", display):
            raise DesktopAutomationError(
                "A automação exige uma sessão gráfica X11 local."
            )
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

    def navigate(self, *, window_id: int, window_title: str,
                 action: str) -> str:
        """Send exactly one fixed navigation key to the consented X11 window.

        No Enter, arrows, shortcuts, arbitrary key symbols or repetition.
        """
        ident = self.validate_id(window_id)
        title = self.validate_title(window_title)
        action = self.validate_navigation(action)
        # Revalidate after a potentially long user confirmation dialog,
        # just like type_text; no dependency on temporarily changed focus.
        if self.validate_title(self._query("getwindowname", str(ident))) != title:
            raise DesktopAutomationError(
                "A janela de destino mudou após a autorização. Nenhuma tecla enviada."
            )
        cmd = [
            self._command(), "key", "--window", str(ident),
            "--clearmodifiers", "--", self.NAVIGATION_KEYS[action],
        ]
        try:
            result = subprocess.run(
                cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL, timeout=self.COMMAND_TIMEOUT,
                check=False,
            )
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise DesktopAutomationError(
                "Não foi possível concluir a navegação X11; verifique a janela."
            ) from exc
        if result.returncode != 0:
            raise DesktopAutomationError(
                "Navegação X11 falhou ou foi parcialmente executada."
            )
        return action

    def type_text(self, *, window_id: int, window_title: str, text: str) -> int:
        ident = self.validate_id(window_id)
        title = self.validate_title(window_title)
        value = self.validate_text(text)
        # Approval dialogs often shift focus to Nexus itself. The user instead
        # explicitly approved an *exact window ID and title*, so revalidate
        # those after consent without relying on the now-changed active focus.
        current_title = self.validate_title(
            self._query("getwindowname", str(ident))
        )
        if current_title != title:
            raise DesktopAutomationError(
                "A janela de destino mudou após a autorização. Nenhum texto digitado."
            )
        # Fixed window ID prevents unrelated focus changes from redirecting
        # keystrokes. Some X11 apps intentionally ignore XSendEvent typing.
        # No shell, newline, keyboard shortcut or mouse action.
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
    """Read-only readiness report; does not connect to X11 or press keys.

    The reason is ordered by the same fail-closed checks used by _command.
    A ready result only describes prerequisites, not a tested target window.
    """
    wayland = bool(os.environ.get("WAYLAND_DISPLAY")) or (
        os.environ.get("XDG_SESSION_TYPE", "").lower() == "wayland"
    )
    local_display = bool(re.fullmatch(
        r"(?::|unix:)[0-9]+(?:\.[0-9]+)?", os.environ.get("DISPLAY", "")
    ))
    xdotool = bool(shutil.which("xdotool"))
    session_x11 = local_display and not wayland
    reason = (
        "WAYLAND_SESSION" if wayland else
        "LOCAL_X11_DISPLAY_REQUIRED" if not local_display else
        "XDOTOOL_MISSING" if not xdotool else "READY"
    )
    return {
        "platform": "Linux X11 only",
        "session_x11": session_x11,
        "xdotool": xdotool,
        "ready": session_x11 and xdotool,
        "reason": reason,
        "navigation_actions": list(X11DesktopBackend.NAVIGATION_KEYS),
        "typing_max_characters": X11DesktopBackend.MAX_TEXT,
        "confirmation_per_action": True,
        "effects": "read window title, type approved text or send one allowlisted navigation key",
        "camera_access": False,
        "screenshot_access": False,
        "wayland_supported": False,
    }
