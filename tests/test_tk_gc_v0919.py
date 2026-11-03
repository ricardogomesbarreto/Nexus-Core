"""Tk garbage collection belongs to the main UI thread."""
import gc
from types import SimpleNamespace

from nexus.desktop.tk_gc import guard_tk_root


def test_root_guard_collects_on_ui_and_restores_previous_gc_state():
    class FakeRoot:
        def __init__(self): self.callbacks = []
        def bind(self, event, callback, add=None):
            assert event == "<Destroy>"
            self.destroy_callback = callback
        def after(self, delay, callback):
            assert delay == 2000
            self.callbacks.append(callback)
    root = FakeRoot()
    before = gc.isenabled()
    try:
        guard_tk_root(root)
        guard_tk_root(root)
        assert not gc.isenabled()
        assert len(root.callbacks) == 1
        root.callbacks.pop()()
        assert len(root.callbacks) == 1
    finally:
        root.destroy_callback(SimpleNamespace(widget=root))
    assert gc.isenabled() is before
