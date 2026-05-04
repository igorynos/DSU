from dsu.ui._helpers import (
    format_status_text,
    format_serial_short,
    matches_filter,
)


def test_format_status_text():
    assert format_status_text(True) == "online"
    assert format_status_text(False) == "offline"


def test_format_serial_short_long_serial_truncates():
    long = "0102030405060708090a0b0c0d0e0f10"
    assert format_serial_short(long) == "01020304050607…"


def test_format_serial_short_empty_passes_through():
    assert format_serial_short("") == ""


def test_matches_filter_matches_name_case_insensitive():
    class D:
        name = "Reader-1"
        ip = "192.168.0.16"
        s_num = "abcdef"
    assert matches_filter(D(), "reader") is True


def test_matches_filter_matches_ip_substring():
    class D:
        name = "X"
        ip = "192.168.0.16"
        s_num = ""
    assert matches_filter(D(), "192.168") is True


def test_matches_filter_matches_serial_substring():
    class D:
        name = "X"
        ip = "1.1.1.1"
        s_num = "abcdef"
    assert matches_filter(D(), "cdef") is True


def test_matches_filter_no_match():
    class D:
        name = "X"
        ip = "1.1.1.1"
        s_num = "ab"
    assert matches_filter(D(), "zz") is False


def test_matches_filter_empty_query_matches_all():
    class D:
        name = "X"; ip = ""; s_num = ""
    assert matches_filter(D(), "") is True
    assert matches_filter(D(), "   ") is True
