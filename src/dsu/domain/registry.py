"""Thread-safe registry of discovered devices."""

from __future__ import annotations

import threading
from collections.abc import Iterator

from dsu.domain.events import DevLstEvent, EventBus
from dsu.domain.models import Device


class DeviceRegistry:
    def __init__(self, events: EventBus) -> None:
        self._events = events
        self._devices: list[Device] = []
        self._lock = threading.Lock()

    def __len__(self) -> int:
        with self._lock:
            return len(self._devices)

    def __iter__(self) -> Iterator[Device]:
        with self._lock:
            snapshot = list(self._devices)
        return iter(snapshot)

    def find_by_serial(self, s_num: str) -> Device | None:
        with self._lock:
            for d in self._devices:
                if d.s_num and d.s_num == s_num:
                    return d
        return None

    def find_by_address(self, addr: tuple[str, int]) -> Device | None:
        with self._lock:
            for d in self._devices:
                if d.addr == addr:
                    return d
        return None

    def add(self, dev: Device) -> None:
        if not isinstance(dev, Device):
            return
        with self._lock:
            existing = self._locate_locked(dev)
            if existing is None:
                self._devices.append(dev)
                self._events.emit(DevLstEvent.APPEND_DEV, dev=dev)
                return

            # Already present: poll response, plus update if anything changed.
            self._events.emit(DevLstEvent.POLL_RESPONSE, dev=existing)
            if existing.to_dict() != dev.to_dict():
                idx = self._devices.index(existing)
                self._devices[idx] = dev
                self._events.emit(DevLstEvent.UPDATE_DEV, dev=dev)

    def remove(self, dev: Device) -> None:
        with self._lock:
            existing = self._locate_locked(dev)
            if existing is None:
                return
            self._devices.remove(existing)
        self._events.emit(DevLstEvent.REMOVE_DEV, dev=existing)

    def clear(self) -> None:
        with self._lock:
            self._devices.clear()

    def _locate_locked(self, dev: Device) -> Device | None:
        for d in self._devices:
            if d.s_num and dev.s_num and d.s_num == dev.s_num:
                return d
            if not dev.s_num and d.addr == dev.addr:
                return d
        return None
