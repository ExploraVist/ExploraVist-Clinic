# cancel_flag.py
"""Thread‑safe cancellation token shared across modules."""
import threading

class CancelFlag:
    def __init__(self):
        self._event = threading.Event()
        # When True, long‑running tasks should exit ASAP.
        self.monitoring_enabled = False

    # ---- public API -------------------------------------------------------
    def set(self):
        if self.monitoring_enabled:
            self._event.set()

    def clear(self):
        self._event.clear()

    def is_set(self):
        return self._event.is_set()
