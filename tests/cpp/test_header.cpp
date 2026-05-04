#include <catch2/catch_test_macros.hpp>

#include <array>

#include "dsu_native/api.hpp"

TEST_CASE("parse_header rejects short input") {
    std::array<std::uint8_t, 10> short_input{};
    auto h = dsu::parse_header(short_input.data(), short_input.size());
    REQUIRE_FALSE(h.has_value());
}

TEST_CASE("parse_header parses known fields") {
    std::array<std::uint8_t, dsu::HEADER_SIZE> bytes = {
        // crypt_mode, device_header
        0x01, 0x02,
        // fw_ver lo, hi  → "2.1"
        0x01, 0x02,
        // pcb_ver lo, hi  → "4.3"
        0x03, 0x04,
        // btldr_ver lo, hi  → "6.5"
        0x05, 0x06,
        // offset (uint32 LE) = 0x00010000
        0x00, 0x00, 0x01, 0x00,
        // fw_len (uint16 LE) = 32 (words)
        0x20, 0x00,
        // reserved_2
        0x00, 0x00,
        // check_sum (uint32 LE) = 0xDEADBEEF
        0xEF, 0xBE, 0xAD, 0xDE,
    };
    auto h = dsu::parse_header(bytes.data(), bytes.size());
    REQUIRE(h.has_value());
    REQUIRE(h->crypt_mode == 0x01);
    REQUIRE(h->device_header == 0x02);
    REQUIRE(h->fw_ver == "2.1");
    REQUIRE(h->pcb_ver == "4.3");
    REQUIRE(h->btldr_ver == "6.5");
    REQUIRE(h->offset == 0x00010000u);
    REQUIRE(h->fw_len == 32u);
    REQUIRE(h->check_sum == 0xDEADBEEFu);
    REQUIRE(h->raw == bytes);
}
