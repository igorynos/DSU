"""Builds synthetic .fw files for native-module tests."""

from __future__ import annotations

import struct
from pathlib import Path

import pytest


def make_fw_bytes(*, payload: bytes,
                  crypt_mode: int = 0,
                  device_header: int = 0,
                  fw_ver: tuple[int, int] = (1, 0),
                  pcb_ver: tuple[int, int] = (1, 0),
                  btldr_ver: tuple[int, int] = (1, 0),
                  offset: int = 0,
                  check_sum: int = 0) -> bytes:
    if len(payload) % 4 != 0:
        raise ValueError("payload must be multiple of 4 bytes (fw_len is in 32-bit words)")
    fw_len_words = len(payload) // 4
    header = struct.pack(
        "<BB BB BB BB I H 2s I",
        crypt_mode, device_header,
        fw_ver[0], fw_ver[1],
        pcb_ver[0], pcb_ver[1],
        btldr_ver[0], btldr_ver[1],
        offset,
        fw_len_words,
        b"\x00\x00",
        check_sum,
    )
    assert len(header) == 20, len(header)
    return header + payload


@pytest.fixture
def make_fw_file(tmp_path: Path):
    def _make(name: str = "test.fw", **kwargs) -> Path:
        path = tmp_path / name
        path.write_bytes(make_fw_bytes(**kwargs))
        return path
    return _make
