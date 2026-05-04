"""Per-device controller — owns watchdog timers and packet dispatch."""

from __future__ import annotations

import threading

from dsu.domain.events import DevLstEvent, EventBus
from dsu.domain.models import Device

WATCHDOG_TIMEOUT = 10  # seconds


class DeviceController:
    """Bridges a Device to the network layer (locator/eludp).

    The Device dataclass holds only data. Anything that requires sockets,
    threads, or timers lives here.
    """

    def __init__(
        self,
        registry,             # DeviceRegistry — kept loose to avoid a cycle
        events: EventBus,
        locator,              # Locator
        el_udp,               # ElUDP
    ) -> None:
        self._registry = registry
        self._events = events
        self._locator = locator
        self._el_udp = el_udp
        self._watchdogs: dict[str, threading.Timer] = {}

        events.bind(self._on_append, DevLstEvent.APPEND_DEV)
        events.bind(self._on_poll_or_update,
                    [DevLstEvent.POLL_RESPONSE, DevLstEvent.UPDATE_DEV,
                     DevLstEvent.CMD_RESPONSE])
        events.bind(self._on_remove, DevLstEvent.REMOVE_DEV)

    def send_locator(self, dev: Device, cmd, data: bytes = b"") -> None:
        self._locator.send_pack(cmd, data, dev)

    def send_eludp(self, dev: Device, pack: bytes) -> None:
        self._el_udp.send_pack(dev, pack)

    def shutdown(self) -> None:
        for timer in self._watchdogs.values():
            timer.cancel()
        self._watchdogs.clear()

    # --- watchdog --------------------------------------------------------

    def _on_append(self, _event, *, dev: Device, **_kwargs) -> None:
        self._restart_watchdog(dev)

    def _on_poll_or_update(self, _event, *, dev: Device, **_kwargs) -> None:
        self._restart_watchdog(dev)

    def _on_remove(self, _event, *, dev: Device, **_kwargs) -> None:
        timer = self._watchdogs.pop(self._key(dev), None)
        if timer is not None:
            timer.cancel()

    def _restart_watchdog(self, dev: Device) -> None:
        key = self._key(dev)
        existing = self._watchdogs.pop(key, None)
        if existing is not None:
            existing.cancel()
        timer = threading.Timer(WATCHDOG_TIMEOUT, self._on_timeout, args=(dev,))
        timer.name = f"watchdog:{key}"
        timer.daemon = True
        timer.start()
        self._watchdogs[key] = timer

    def _on_timeout(self, dev: Device) -> None:
        self._events.emit(DevLstEvent.CON_FAIL, dev=dev)
        self._registry.remove(dev)

    @staticmethod
    def _key(dev: Device) -> str:
        return dev.s_num or f"{dev.ip}:{dev.port}"
