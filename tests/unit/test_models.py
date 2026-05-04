from dsu.domain.models import (
    Device, DevModel, DevBootMode, LOCATOR_PAYLOAD_SIZE,
)


def _build_payload(
    *,
    type_=1, boot_mode=1,
    s_num=b"\x01" * 16,
    mac=b"\xaa\xbb\xcc\xdd\xee\xff",
    fw=b"\x03\x02",          # little-endian → "2.3"
    btldr=b"\x01\x00",       # "0.1"
    pcb=b"\x05\x04",         # "4.5"
    name=b"Reader\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00",
    ip=b"\xc0\xa8\x00\x10",
    mask=b"\xff\xff\xff\x00",
    gw=b"\xc0\xa8\x00\x01",
    host=b"\xc0\xa8\x00\x02",
    port=b"\xef\x06",        # 1775
    comment=b"\x00" * 64,
) -> bytes:
    pl = (bytes([type_, boot_mode]) + s_num + mac + fw + btldr + pcb
          + name + ip + mask + gw + host + port + comment)
    assert len(pl) == LOCATOR_PAYLOAD_SIZE
    return pl


def test_payload_size_constant():
    assert LOCATOR_PAYLOAD_SIZE == 128


def test_parses_known_fields():
    dev = Device.from_locator_payload(_build_payload())
    assert dev.model == DevModel[1]            # "CP-18"
    assert dev.boot_mode == DevBootMode[1]     # "ОСН."
    assert dev.s_num == ("\x01" * 16).encode("latin-1").hex()
    assert dev.mac == "aa:bb:cc:dd:ee:ff"
    assert dev.fw == "2.3"
    assert dev.btldr == "0.1"
    assert dev.pcb == "4.5"
    assert dev.name == "Reader"
    assert dev.ip == "192.168.0.16"
    assert dev.mask == "255.255.255.0"
    assert dev.gateway == "192.168.0.1"
    assert dev.host == "192.168.0.2"
    assert dev.port == 1775
    assert dev.comment == ""


def test_unknown_model_falls_back_to_default():
    dev = Device.from_locator_payload(_build_payload(type_=99))
    assert dev.model == DevModel[0]            # "НЕИЗВ."


def test_zero_serial_renders_empty():
    dev = Device.from_locator_payload(_build_payload(s_num=b"\x00" * 16))
    assert dev.s_num == ""


def test_zero_mac_renders_empty():
    dev = Device.from_locator_payload(_build_payload(mac=b"\x00" * 6))
    assert dev.mac == ""


def test_short_payload_yields_blank_device():
    dev = Device.from_locator_payload(b"\x00" * 10)
    assert dev.s_num == ""
    assert dev.ip == "0.0.0.0"
    assert dev.port == 0


def test_from_addr_constructor_skips_payload_parsing():
    dev = Device.from_address("10.0.0.5", 1775)
    assert dev.ip == "10.0.0.5"
    assert dev.port == 1775
    assert dev.s_num == ""
    assert dev.addr == ("10.0.0.5", 1775)


def test_equality_by_serial_number():
    a = Device.from_locator_payload(_build_payload())
    b = Device.from_locator_payload(_build_payload(ip=b"\x0a\x00\x00\x01"))  # different IP
    assert a == b   # same s_num


def test_equality_by_address_when_serial_blank():
    a = Device.from_address("10.0.0.5", 1775)
    b = Device.from_address("10.0.0.5", 1775)
    c = Device.from_address("10.0.0.6", 1775)
    assert a == b
    assert a != c


def test_to_dict_returns_copy():
    dev = Device.from_locator_payload(_build_payload())
    d1 = dev.to_dict()
    d1["name"] = "MUTATED"
    assert dev.to_dict()["name"] == "Reader"


def test_primary_settings_array_round_trip():
    dev = Device.from_locator_payload(_build_payload())
    arr = dev.primary_settings_array()
    # Layout: name(16) + ip(4) + mask(4) + gw(4) + host(4) + port(2) + comment(64) = 98
    assert len(arr) == 98
    assert arr[:6] == b"Reader"
    assert arr[16:20] == b"\xc0\xa8\x00\x10"


def test_primary_settings_array_overrides():
    dev = Device.from_locator_payload(_build_payload())
    arr = dev.primary_settings_array({"port": 2000, "name": "X"})
    assert arr[:1] == b"X"
    assert arr[16 + 4 + 4 + 4 + 4:16 + 4 + 4 + 4 + 4 + 2] == (2000).to_bytes(2, "little")
