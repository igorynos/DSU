from dsu.domain.codec import (
    str_from_bytes, str_to_bytes, ip_from_bytes, ip_to_bytes,
)


def test_str_from_bytes_strips_at_first_null():
    assert str_from_bytes(b"hello\x00world") == "hello"


def test_str_from_bytes_handles_no_null():
    assert str_from_bytes(b"hi") == "hi"


def test_str_from_bytes_decodes_cp1251():
    # 'Привет' in cp1251
    raw = "Привет".encode("cp1251") + b"\x00\x00"
    assert str_from_bytes(raw) == "Привет"


def test_str_from_bytes_invalid_input_returns_empty():
    assert str_from_bytes(None) == ""
    assert str_from_bytes(123) == ""


def test_str_to_bytes_pads_with_zeros():
    assert str_to_bytes("hi", 5) == b"hi\x00\x00\x00"


def test_str_to_bytes_truncates_overlong():
    assert str_to_bytes("toolong", 4) == b"tool"


def test_str_to_bytes_encodes_cp1251():
    assert str_to_bytes("Привет", 8) == "Привет".encode("cp1251") + b"\x00\x00"


def test_ip_from_bytes_formats_dotted_quad():
    assert ip_from_bytes(b"\xc0\xa8\x00\x01") == "192.168.0.1"


def test_ip_from_bytes_invalid_returns_zero():
    assert ip_from_bytes(b"\x01\x02") == "0.0.0.0"
    assert ip_from_bytes(None) == "0.0.0.0"


def test_ip_to_bytes_round_trip():
    assert ip_to_bytes("192.168.0.1") == b"\xc0\xa8\x00\x01"


def test_ip_to_bytes_invalid_returns_four_zeros():
    assert ip_to_bytes("not an ip") == b"\x00\x00\x00\x00"
    assert ip_to_bytes(None) == b"\x00\x00\x00\x00"
