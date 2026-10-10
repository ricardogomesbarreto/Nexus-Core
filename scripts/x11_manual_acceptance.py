"""Opt-in physical X11 smoke test, isolated to a disposable Tk window.

Run manually on the user's Linux X11 desktop:
    python -m scripts.x11_manual_acceptance

Nothing executes on import. No screenshots, files, networks, DB, microphone,
or input into an existing user window. Each synthetic key action needs explicit
terminal consent and targets a uniquely named window created by this process.
"""
import json
import os
import re
import secrets
import subprocess
import sys

from nexus.automation import DesktopAutomationError, X11DesktopBackend


TEXT = "NEXUS073TEST"
CONSENT = "AUTORIZO"


class AcceptanceError(RuntimeError):
    """Sanitized denial without leaking X11 subprocess output."""


def _ask_consent(operation: str, *, input_fn=input, stream=sys.stdin) -> bool:
    """Only terminal users may allow an individual test action."""
    if not stream.isatty():
        return False
    try:
        return input_fn(
            f"Para autorizar apenas {operation} na janela TEMPORÁRIA, "
            f"digite {CONSENT}: "
        ).strip() == CONSENT
    except (EOFError, KeyboardInterrupt):
        return False


def _test_window(backend: X11DesktopBackend, title: str) -> tuple[int, str]:
    """Resolve precisely one owned visible window, with strict X11 metadata."""
    binary = backend._command()
    try:
        result = subprocess.run(
            [binary, "search", "--onlyvisible", "--pid", str(os.getpid()),
             "--name", "^" + re.escape(title) + "$"],
            stdin=subprocess.DEVNULL, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, timeout=backend.COMMAND_TIMEOUT,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired) as exc:
        raise AcceptanceError("Busca da janela temporária falhou.") from exc
    if result.returncode != 0 or len(result.stdout) > backend.MAX_QUERY_BYTES:
        raise AcceptanceError("Janela temporária não encontrada.")
    try:
        ids = result.stdout.decode("ascii", errors="strict").splitlines()
        if len(ids) != 1 or not re.fullmatch(r"[0-9]{1,10}", ids[0]):
            raise AcceptanceError("A janela temporária deve ter um único ID.")
        ident = backend.validate_id(int(ids[0]))
        expected_title, pid, window_class = backend._identity(ident)
    except (UnicodeError, DesktopAutomationError) as exc:
        raise AcceptanceError("Metadados X11 da janela de teste inválidos.") from exc
    if expected_title != title or pid != os.getpid():
        raise AcceptanceError("A janela retornada não pertence ao teste.")
    return ident, window_class


def run() -> int:
    # Validate environment without opening a user application.
    backend = X11DesktopBackend()
    try:
        backend._command()
    except DesktopAutomationError:
        print("A homologação exige sessão Linux X11 local e xdotool.")
        return 2
    if not sys.stdin.isatty():
        print("Homologação recusada: execute diretamente em terminal interativo.")
        return 2

    # GUI is created only after the operator deliberately invokes this module.
    import tkinter as tk
    title = "NEXUS-CORE-X11-HOMOLOG-" + secrets.token_hex(6)
    try:
        root = tk.Tk(className="NexusCoreX11Homolog")
    except tk.TclError:
        print("Não foi possível criar a janela X11 de homologação.")
        return 2
    try:
        root.title(title)
        root.geometry("460x130")
        tk.Label(root, text="TESTE LOCAL DESCARTÁVEL — NEXUS CORE").pack(pady=5)
        first = tk.Entry(root)
        first.pack(fill="x", padx=20)
        second = tk.Entry(root)
        second.pack(fill="x", padx=20)
        first.focus_set()
        root.update()

        ident, window_class = _test_window(backend, title)
        # Revalidate a matching PID and class before ever prompting for action.
        backend._require_target(
            window_id=ident, window_title=title,
            window_pid=os.getpid(), window_class=window_class,
        )
        base = dict(
            window_id=ident, window_title=title,
            window_pid=os.getpid(), window_class=window_class,
        )
        results = {
            "scope": "linux_x11_own_temporary_window",
            "real_desktop_test": True,
            "identity": "verified",
            "mismatched_identity_denied": False,
            "typing": "not_attempted",
            "navigation": "not_attempted",
        }

        # An intentionally incorrect PID must fail without sending a keystroke.
        try:
            backend.type_text(**{**base, "window_pid": os.getpid() + 1}, text=TEXT)
        except DesktopAutomationError:
            results["mismatched_identity_denied"] = True

        print("Janela temporária criada. Não feche até concluir os testes.")
        print("Cada ação exige confirmação separada. Nenhuma janela existente será usada.")

        if _ask_consent("DIGITAÇÃO"):
            backend.type_text(**base, text=TEXT)
            root.update()
            results["typing"] = "passed" if first.get() == TEXT else "failed"
        else:
            results["typing"] = "refused"

        if _ask_consent("UMA TECLA TAB"):
            first.focus_set()
            root.update()
            backend.navigate(**base, action="next_field")
            root.update()
            results["navigation"] = (
                "passed" if root.focus_get() is second else "failed"
            )
        else:
            results["navigation"] = "refused"

        success = (
            results["mismatched_identity_denied"]
            and results["typing"] == "passed"
            and results["navigation"] == "passed"
        )
        results["passed"] = bool(success)
        print(json.dumps(results, ensure_ascii=False, sort_keys=True))
        return 0 if success else 1
    except (AcceptanceError, DesktopAutomationError, tk.TclError):
        print("Homologação interrompida ou recusada; nenhuma aprovação registrada.")
        return 2
    finally:
        try:
            root.destroy()
        except tk.TclError:
            pass


if __name__ == "__main__":
    raise SystemExit(run())
