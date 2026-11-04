"""Keep cyclic Tk object finalizers on the desktop UI thread.

Tk objects cannot safely be finalized by unrelated background workers. While
the main window exists, disable automatic cyclic collections and perform
bounded periodic collections from Tk's event loop instead.
"""
from __future__ import annotations

import gc
from threading import current_thread, main_thread

_roots = 0
_restore_enabled = False


def _sweep(root):
    if not getattr(root, "_nexus_tk_gc_active", False):
        return
    gc.collect()
    try:
        root.after(2000, lambda: _sweep(root))
    except Exception:
        pass


def _release(event):
    global _roots
    root = event.widget
    if not getattr(root, "_nexus_tk_gc_active", False):
        return
    root._nexus_tk_gc_active = False
    _roots -= 1
    if _roots == 0 and _restore_enabled:
        gc.enable()


def guard_tk_root(root) -> None:
    global _roots, _restore_enabled
    if current_thread() is not main_thread():
        raise RuntimeError("A interface Tk deve ser criada na thread principal.")
    if getattr(root, "_nexus_tk_gc_active", False):
        return
    if _roots == 0:
        _restore_enabled = gc.isenabled()
        gc.collect()
        gc.disable()
    _roots += 1
    root._nexus_tk_gc_active = True
    root.bind("<Destroy>", _release, add="+")
    root.after(2000, lambda: _sweep(root))
