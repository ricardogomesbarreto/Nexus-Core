"""Real text turns in a disposable Tk, PostgreSQL and Ollama session."""
import time
import tkinter as tk
from pathlib import Path

from nexus.desktop.confirmation import DesktopConfirmation
from nexus.desktop.window import DesktopWindow
from nexus.main import build_application
from nexus.models.resource_budget import ResourceBudget


def main():
    budget = ResourceBudget.detect()
    assert budget.compact and budget.total_ram_mib < 4000, budget
    root = tk.Tk()
    confirmation = DesktopConfirmation()
    app = build_application(confirmation_handler=confirmation)
    try:
        app.initialize()
        window = DesktopWindow(root, app, confirmation, startup_voice=False)
        window.speech_enabled.set(False)
        prompts = ["Por que o céu parece azul?", "Como a chuva se forma?",
                   "Explique em detalhes como as nuvens se formam.",
                   "Por que as folhas costumam ser verdes?",
                   "Como o som se propaga?", "Como funciona um termômetro?",
                   "Por que vemos um arco-íris?", "Como uma planta absorve água?",
                   "O que causa as marés?", "Como se formam as ondas do mar?"]
        cancelled_turns = {2, 6}
        cpu_file = Path("/sys/fs/cgroup/cpu.stat")
        def cpu_seconds():
            stats = dict(line.split() for line in cpu_file.read_text().splitlines())
            return int(stats["usage_usec"]) / 1_000_000

        for i, prompt in enumerate(prompts):
            print(f"before_turn={i+1} available_mib={budget.available_now_mib()} "
                  f"cgroup_current={Path('/sys/fs/cgroup/memory.current').read_text().strip()}", flush=True)
            history = list(window.session.history)
            window.input.insert("1.0", prompt)
            start = time.monotonic()
            cpu_start = cpu_seconds()
            window._send()
            assert window._busy
            first = None
            max_tick = 0.0
            last = start
            while window._busy:
                root.update()
                now = time.monotonic()
                max_tick = max(max_tick, now - last)
                last = now
                if first is None and window._stream_start is not None:
                    first = now - start
                    if i in cancelled_turns:
                        window._cancel_current()
                assert now - start < 150, "Turn timed out"
                time.sleep(0.012)
            if i in cancelled_turns:
                assert first is not None and window.session.history == history
            else:
                assert window.session.history and window.session.history[-1][0] == prompt, window.transcript.get("1.0", "end")[-600:]
                assert window.session.history[-1][1].strip()
            assert first is not None, "No incremental preview appeared"
            assert len(window.session.history) <= window.session.MAX_TURNS
            print(f"turn={i+1} first_visible_s={first} total_s={now-start:.3f} "
                  f"max_ui_tick_s={max_tick:.3f} cpu_s={cpu_seconds()-cpu_start:.3f}", flush=True)
            assert max_tick < 2, "Desktop event loop stalled"
        closed = []
        root.bind("<Destroy>", lambda event: closed.append(True) if event.widget is root else None, add="+")
        window._close()
        end = time.monotonic() + 30
        while not closed and time.monotonic() < end:
            root.update()
            time.sleep(0.02)
        assert closed, "Desktop did not shut down"
    finally:
        confirmation.close()
        app.shutdown()


if __name__ == "__main__":
    main()
