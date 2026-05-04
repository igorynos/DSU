"""Tracks in-flight firmware flash operations for the badge + per-row progress."""

from __future__ import annotations

import logging
import threading
from collections.abc import Callable

_LOG = logging.getLogger(__name__)


class FlashState:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._items: dict[str, tuple[int, int]] = {}  # key -> (current, total)
        self._listeners: list[Callable[[], None]] = []

    @property
    def count(self) -> int:
        with self._lock:
            return len(self._items)

    def active_keys(self) -> list[str]:
        with self._lock:
            return list(self._items.keys())

    def is_flashing(self, key: str) -> bool:
        with self._lock:
            return key in self._items

    def progress(self, key: str) -> tuple[int, int]:
        with self._lock:
            return self._items.get(key, (0, 0))

    def percent(self, key: str) -> int:
        cur, tot = self.progress(key)
        if tot <= 0:
            return 0
        return min(100, int(cur * 100 / tot))

    def start(self, key: str, total: int) -> None:
        with self._lock:
            self._items[key] = (0, total)
        self._notify()

    def update(self, key: str, current: int) -> None:
        with self._lock:
            if key not in self._items:
                return
            _, tot = self._items[key]
            self._items[key] = (current, tot)
        self._notify()

    def finish(self, key: str) -> None:
        with self._lock:
            self._items.pop(key, None)
        self._notify()

    def subscribe(self, fn: Callable[[], None]) -> None:
        with self._lock:
            self._listeners.append(fn)

    def _notify(self) -> None:
        for fn in list(self._listeners):
            try:
                fn()
            except Exception:
                _LOG.exception("FlashState listener raised")
