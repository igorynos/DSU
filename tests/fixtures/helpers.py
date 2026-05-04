"""Helpers for tests — not exercised by production code."""

from dsu.domain.events import EventBus
from dsu.domain.models import Device
from dsu.domain.registry import DeviceRegistry


def make_device(serial: str = "", ip: str = "10.0.0.1", port: int = 1775) -> Device:
    """Build a synthetic Device with optional serial."""
    dev = Device.from_address(ip, port)
    dev.s_num = serial
    return dev


def populated_registry(*serials: str) -> tuple[DeviceRegistry, EventBus]:
    """Registry pre-populated with N devices keyed by serial."""
    bus = EventBus()
    reg = DeviceRegistry(bus)
    for i, s in enumerate(serials):
        reg.add(make_device(serial=s, ip=f"10.0.0.{100 + i}"))
    return reg, bus
