"""Application configuration and seed-device loader."""

from __future__ import annotations

import configparser
from dataclasses import dataclass, field
from importlib import resources
from pathlib import Path

from dsu.domain.models import Device
from dsu.domain.registry import DeviceRegistry


@dataclass
class LocatorConfig:
    port: int = 1770
    poll_interval: float = 2.0


@dataclass
class ElUdpConfig:
    default_port: int = 1775


@dataclass
class AppConfig:
    locator: LocatorConfig = field(default_factory=LocatorConfig)
    el_udp: ElUdpConfig = field(default_factory=ElUdpConfig)
    devices_ini_path: Path | None = None  # None → use packaged defaults.ini

    @classmethod
    def from_default(cls) -> "AppConfig":
        return cls()


def seed_registry_from_ini(registry: DeviceRegistry, path: Path | None = None) -> int:
    """Populate the registry from an ELUDP-section ini. Returns count added."""
    parser = configparser.ConfigParser(delimiters=(":",))
    if path is None:
        text = resources.files("dsu.config").joinpath("defaults.ini").read_text()
        parser.read_string(text)
    else:
        if not path.exists():
            return 0
        parser.read(path)

    if not parser.has_section("ELUDP"):
        return 0

    added = 0
    for option in parser.options("ELUDP"):
        raw = parser.get("ELUDP", option)
        attrs = {}
        for chunk in raw.split(","):
            if "=" not in chunk:
                continue
            k, v = chunk.split("=", 1)
            attrs[k.strip()] = v.strip()
        if "ip" not in attrs:
            continue
        registry.add(Device.from_address(attrs["ip"], int(attrs.get("port", 1775))))
        added += 1
    return added
