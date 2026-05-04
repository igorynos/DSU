"""Application wiring — replaces import-time globals from the old loader.py."""

from __future__ import annotations

import threading
from dataclasses import dataclass

from dsu.config.settings import AppConfig, seed_registry_from_ini
from dsu.domain.events import EventBus
from dsu.domain.registry import DeviceRegistry
from dsu.net.controller import DeviceController
from dsu.net.eludp import ElUDP
from dsu.net.locator import Locator


@dataclass
class Application:
    config: AppConfig
    events: EventBus
    registry: DeviceRegistry
    locator: Locator
    el_udp: ElUDP
    controller: DeviceController
    locator_thread: threading.Thread

    def start(self) -> None:
        seed_registry_from_ini(self.registry, self.config.devices_ini_path)
        if not self.locator_thread.is_alive():
            self.locator_thread.start()

    def shutdown(self) -> None:
        self.locator.shutdown()
        self.controller.shutdown()
        if self.locator_thread.is_alive():
            self.locator_thread.join(timeout=2)

    def __enter__(self) -> "Application":
        self.start()
        return self

    def __exit__(self, *exc) -> None:
        self.shutdown()


def create_app(config: AppConfig | None = None) -> Application:
    config = config or AppConfig.from_default()
    events = EventBus()
    registry = DeviceRegistry(events)
    locator = Locator(registry, events)
    el_udp = ElUDP()
    controller = DeviceController(registry, events, locator, el_udp)
    locator_thread = threading.Thread(
        target=locator.run, name="locator", daemon=True
    )
    return Application(config, events, registry, locator, el_udp,
                       controller, locator_thread)
