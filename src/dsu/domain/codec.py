"""Byte/string conversions for the locator wire protocol (cp1251)."""

from __future__ import annotations

import socket


def str_from_bytes(ba: object) -> str:
    if not isinstance(ba, (bytes, bytearray)):
        return ""
    nul = ba.find(0)
    chunk = ba[:nul] if nul >= 0 else ba
    return chunk.decode("cp1251")


def str_to_bytes(value: str, length: int) -> bytes:
    encoded = value[:length].encode("cp1251")
    return encoded + bytes(length - len(encoded))


def ip_from_bytes(ba: object) -> str:
    if not isinstance(ba, (bytes, bytearray)) or len(ba) != 4:
        return "0.0.0.0"
    return ".".join(str(b) for b in ba)


def ip_to_bytes(ip: object) -> bytes:
    if not isinstance(ip, str):
        return bytes(4)
    try:
        socket.inet_aton(ip)
        return bytes(int(p) for p in ip.split("."))
    except (socket.error, ValueError):
        return bytes(4)
