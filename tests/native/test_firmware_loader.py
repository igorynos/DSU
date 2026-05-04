import dsu_native


def test_module_constants():
    assert dsu_native.HEADER_SIZE == 20
    assert dsu_native.BLOCK_SIZE == 32
    assert dsu_native.CMD_FW_INFO == 0x03
    assert dsu_native.CMD_FW_PACK == 0x04


def test_loader_invalid_when_file_missing(tmp_path):
    fw = dsu_native.FirmwareLoader(str(tmp_path / "nonexistent.fw"))
    assert fw.is_valid() is False
    assert fw.next_packet() is None
    assert fw.progress() == 100


def test_loader_invalid_for_short_file(tmp_path):
    p = tmp_path / "short.fw"
    p.write_bytes(b"\x00" * 5)
    fw = dsu_native.FirmwareLoader(str(p))
    assert fw.is_valid() is False


def test_header_fields(make_fw_file):
    path = make_fw_file(
        payload=b"\x00" * 32,
        crypt_mode=1, device_header=2,
        fw_ver=(1, 2),       # → "2.1"
        pcb_ver=(3, 4),      # → "4.3"
        btldr_ver=(5, 6),    # → "6.5"
        offset=0x10000,
        check_sum=0xDEADBEEF,
    )
    fw = dsu_native.FirmwareLoader(str(path))
    assert fw.is_valid()
    h = fw.header
    assert h.crypt_mode == 1
    assert h.device_header == 2
    assert h.fw_ver == "2.1"
    assert h.pcb_ver == "4.3"
    assert h.btldr_ver == "6.5"
    assert h.offset == 0x10000
    assert h.fw_len == 8           # 32 bytes / 4
    assert h.check_sum == 0xDEADBEEF
    assert len(h.raw) == 20
    assert fw.size() == 32


def test_packet_iteration(make_fw_file):
    payload = bytes(range(64))      # 64 bytes = 16 words
    path = make_fw_file(payload=payload)
    fw = dsu_native.FirmwareLoader(str(path))

    packets = []
    while True:
        pkt = fw.next_packet()
        if pkt is None:
            break
        packets.append(pkt)

    assert len(packets) == 3        # FW_INFO + 2× FW_PACK

    cmd0, data0 = packets[0]
    assert cmd0 == dsu_native.CMD_FW_INFO
    assert len(data0) == 20

    cmd1, data1 = packets[1]
    assert cmd1 == dsu_native.CMD_FW_PACK
    assert data1[:2] == b"\x00\x00"
    assert data1[2:] == payload[:32]

    cmd2, data2 = packets[2]
    assert cmd2 == dsu_native.CMD_FW_PACK
    assert data2[:2] == b"\x08\x00"      # word offset 8 (32 bytes / 4)
    assert data2[2:] == payload[32:64]

    assert fw.progress() == 100


def test_short_trailing_block(make_fw_file):
    payload = bytes(range(40))      # 40 bytes = 10 words
    path = make_fw_file(payload=payload)
    fw = dsu_native.FirmwareLoader(str(path))

    pkts = [fw.next_packet() for _ in range(4)]
    assert pkts[0][0] == dsu_native.CMD_FW_INFO
    assert pkts[1][0] == dsu_native.CMD_FW_PACK
    assert len(pkts[1][1]) == 2 + 32
    assert pkts[2][0] == dsu_native.CMD_FW_PACK
    assert len(pkts[2][1]) == 2 + 8
    assert pkts[2][1][:2] == b"\x08\x00"
    assert pkts[3] is None


def test_reset_rewinds(make_fw_file):
    path = make_fw_file(payload=b"\x00" * 32)
    fw = dsu_native.FirmwareLoader(str(path))
    fw.next_packet()
    fw.next_packet()
    assert fw.next_packet() is None
    fw.reset()
    cmd, _ = fw.next_packet()
    assert cmd == dsu_native.CMD_FW_INFO
