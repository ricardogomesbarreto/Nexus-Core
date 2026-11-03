"""Collect Tk cycles on pytest's main thread, never on a background worker."""
import gc
import os

import pytest


@pytest.fixture(autouse=True)
def collect_graphical_cycles_on_main_thread():
    if not os.environ.get("DISPLAY"):
        yield
        return
    enabled = gc.isenabled()
    gc.disable()
    try:
        yield
    finally:
        gc.collect()
        if enabled:
            gc.enable()
