"""Auto-clicker: clicks at current mouse position at a configurable rate."""
import threading
import time
from core.operator import click_current


class AutoClicker:
    def __init__(self, interval: float = 0.5):
        self._interval = interval
        self._stop_event = threading.Event()
        self._thread = None
        self._running = False

    def start(self):
        if self._running:
            return
        self._running = True
        self._stop_event.clear()
        self._thread = threading.Thread(target=self._loop, daemon=True)
        self._thread.start()

    def stop(self):
        if not self._running:
            return
        self._running = False
        self._stop_event.set()

    def is_running(self) -> bool:
        return self._running

    def _loop(self):
        while not self._stop_event.is_set():
            click_current()
            self._stop_event.wait(self._interval)
