"""Professional local-first Tk presentation tokens (no remote fonts/assets).

These are purely visual styles; tool permissions, audio and resource behavior
remain entirely in the existing desktop controller and SecurityGate.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Palette:
    wine: str = "#722F37"
    wine_hover: str = "#8f3d4b"
    header: str = "#241c24"
    canvas: str = "#f5f1f3"
    paper: str = "#ffffff"
    card_border: str = "#e5d9df"
    ink: str = "#30252c"
    muted: str = "#675761"
    surface: str = "#f3ebef"
    user_surface: str = "#f8eef2"


COLORS = Palette()
FONT_MIN = 10
FONT_MAX = 16
DEFAULT_FONT = 11


def configure_presentation(style) -> None:
    """Install additive styles; keep legacy names, logo and #722F37 intact."""
    style.configure("Nexus.Card.TFrame", background=COLORS.paper)
    style.configure("Nexus.Soft.TFrame", background=COLORS.surface)
    style.configure("Nexus.CardTitle.TLabel", background=COLORS.paper,
                    foreground=COLORS.ink, font=("Sans", 11, "bold"))
    style.configure("Nexus.CardHint.TLabel", background=COLORS.paper,
                    foreground=COLORS.muted, font=("Sans", 9))
    style.configure("Nexus.Counter.TLabel", background=COLORS.canvas,
                    foreground=COLORS.muted, font=("Sans", 9))
    style.configure("Nexus.CounterOver.TLabel", background=COLORS.canvas,
                    foreground=COLORS.wine, font=("Sans", 9, "bold"))
    style.configure("Nexus.LiveReady.TLabel", background=COLORS.surface,
                    foreground="#33594a", font=("Sans", 9, "bold"),
                    padding=(11, 8))
    style.configure("Nexus.LiveBusy.TLabel", background=COLORS.surface,
                    foreground=COLORS.wine, font=("Sans", 9, "bold"),
                    padding=(11, 8))
    style.configure("Nexus.LiveClosing.TLabel", background=COLORS.surface,
                    foreground=COLORS.muted, font=("Sans", 9, "bold"),
                    padding=(11, 8))
    style.configure("Nexus.Inline.TButton", background=COLORS.paper,
                    foreground=COLORS.wine, font=("Sans", 9),
                    padding=(7, 3), borderwidth=0)
    style.map("Nexus.Inline.TButton",
              background=[("active", COLORS.user_surface),
                          ("pressed", COLORS.card_border)],
              foreground=[("disabled", COLORS.muted)])


def message_size(current: int, change: int) -> int:
    """Bounded font zoom that cannot damage layout or overflow preferences."""
    return max(FONT_MIN, min(FONT_MAX, current + change))


def composer_count(characters: int, *, limit: int = 4000) -> tuple[str, str]:
    """Only local text length is displayed; text is never logged or stored."""
    value = max(0, characters)
    style = ("Nexus.CounterOver.TLabel" if value > limit
             else "Nexus.Counter.TLabel")
    return f"{value} / {limit} caracteres", style


def activity_state(*, busy: bool, closing: bool) -> tuple[str, str]:
    """State is from the UI controller, not an assertion about hardware."""
    if closing:
        return "● ENCERRANDO", "Nexus.LiveClosing.TLabel"
    if busy:
        return "● PROCESSANDO", "Nexus.LiveBusy.TLabel"
    return "● PRONTO", "Nexus.LiveReady.TLabel"
