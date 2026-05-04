"""Python-facing wrapper around the dsu_native FirmwareLoader.

The native module returns (cmd, data) tuples. To preserve the call shape
that `eludp.py` expects (a generator yielding `bytes(cmd) + data`), we
wrap the iterator here.
"""

from __future__ import annotations

from collections.abc import Iterator
from pathlib import Path

import dsu_native


class Firmware:
    def __init__(self, path: str | Path) -> None:
        self._fw = dsu_native.FirmwareLoader(str(path))

    @property
    def is_valid(self) -> bool:
        return self._fw.is_valid()

    @property
    def header(self):
        if not self._fw.is_valid():
            return None
        return self._fw.header

    @property
    def size(self) -> int:
        return self._fw.size()

    def progress(self) -> int:
        return self._fw.progress()

    def reset(self) -> None:
        self._fw.reset()

    def __iter__(self) -> Iterator[bytes]:
        self._fw.reset()
        return self

    def __next__(self) -> bytes:
        pkt = self._fw.next_packet()
        if pkt is None:
            raise StopIteration
        cmd, data = pkt
        return bytes([cmd]) + data

    def __call__(self):
        """Compatibility shim: original code used `fw()` as a generator."""
        return iter(self)
