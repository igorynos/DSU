"""Pure data classes for devices discovered on the network."""

from __future__ import annotations

import struct
from dataclasses import dataclass, replace

from dsu.domain.codec import (
    ip_from_bytes, ip_to_bytes, str_from_bytes, str_to_bytes,
)

LOCATOR_PAYLOAD_SIZE = 128

# Layout of Locator_Summary (see locator wire-format docs in original devices.py):
#   B           type
#   B           boot_mode
#   16s         s_num                 (little-endian, displayed reversed)
#   6s          mac
#   2s          fw                    (little-endian uint16, rendered "hi.lo")
#   2s          btldr
#   2s          pcb
#   16s         name
#   4s          ip
#   4s          mask
#   4s          gateway
#   4s          host
#   <H          port (uint16 LE)
#   64s         comment
_LAYOUT = struct.Struct("<BB16s6s2s2s2s16s4s4s4s4sH64s")
assert _LAYOUT.size == LOCATOR_PAYLOAD_SIZE

DevModel: dict[int, str] = {
    0: "НЕИЗВ.",
    1: "CP-18",
    2: "POS",
    3: "AP-PRO",
    4: "TW-2020",
}

DevBootMode: dict[int, str] = {
    0: "ЗАГР.",
    1: "ОСН.",
}


def _hex_le(raw: bytes) -> str:
    """Empty when all-zero, otherwise hex of the byte-reversed value."""
    if raw == bytes(len(raw)):
        return ""
    return raw[::-1].hex()


def _ver_le(raw: bytes) -> str:
    """Two-byte little-endian version → 'hi.lo' (e.g. b'\\x03\\x02' → '2.3'). Empty if zero."""
    if raw == bytes(len(raw)):
        return ""
    return f"{raw[1]}.{raw[0]}"


def _mac(raw: bytes) -> str:
    if raw == bytes(len(raw)):
        return ""
    return raw.hex(sep=":")


@dataclass
class Device:
    model: str = "НЕИЗВ."
    boot_mode: str = ""
    s_num: str = ""
    mac: str = ""
    fw: str = ""
    btldr: str = ""
    pcb: str = ""
    name: str = ""
    ip: str = "0.0.0.0"
    mask: str = "0.0.0.0"
    gateway: str = "0.0.0.0"
    host: str = "0.0.0.0"
    port: int = 0
    comment: str = ""

    @property
    def addr(self) -> tuple[str, int]:
        return self.ip, self.port

    @classmethod
    def from_locator_payload(cls, data: bytes) -> "Device":
        if len(data) != LOCATOR_PAYLOAD_SIZE:
            return cls()
        (type_, boot, s_num, mac, fw, btldr, pcb, name,
         ip, mask, gw, host, port, comment) = _LAYOUT.unpack(data)
        return cls(
            model=DevModel.get(type_, DevModel[0]),
            boot_mode=DevBootMode.get(boot, ""),
            s_num=_hex_le(s_num),
            mac=_mac(mac),
            fw=_ver_le(fw),
            btldr=_ver_le(btldr),
            pcb=_ver_le(pcb),
            name=str_from_bytes(name),
            ip=ip_from_bytes(ip),
            mask=ip_from_bytes(mask),
            gateway=ip_from_bytes(gw),
            host=ip_from_bytes(host),
            port=port,
            comment=str_from_bytes(comment),
        )

    @classmethod
    def from_address(cls, ip: str, port: int) -> "Device":
        return cls(ip=ip, port=port)

    def to_dict(self) -> dict:
        return {
            "model": self.model, "boot_mode": self.boot_mode,
            "s_num": self.s_num, "mac": self.mac,
            "fw": self.fw, "btldr": self.btldr, "pcb": self.pcb,
            "name": self.name, "ip": self.ip, "mask": self.mask,
            "gateway": self.gateway, "host": self.host,
            "port": self.port, "comment": self.comment,
        }

    def replace(self, **changes) -> "Device":
        return replace(self, **changes)

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, Device):
            return NotImplemented
        if self.s_num and other.s_num:
            return self.s_num == other.s_num
        return self.addr == other.addr

    def __hash__(self) -> int:
        return hash(self.s_num or self.addr)

    def __str__(self) -> str:
        return (f'"{self.name}" s/n={self.s_num}, '
                f'IP={self.ip}, port={self.port}, MAC={self.mac}')

    def primary_settings_array(self, overrides: dict | None = None) -> bytes:
        """Bytes of the primary-settings command payload (98 bytes)."""
        o = overrides or {}
        return b"".join([
            str_to_bytes(o.get("name", self.name), 16),
            ip_to_bytes(o.get("ip", self.ip)),
            ip_to_bytes(o.get("mask", self.mask)),
            ip_to_bytes(o.get("gateway", self.gateway)),
            ip_to_bytes(o.get("host", self.host)),
            int(o.get("port", self.port)).to_bytes(2, "little"),
            str_to_bytes(o.get("comment", self.comment), 64),
        ])
