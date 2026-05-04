#include <catch2/catch_test_macros.hpp>

#include <array>
#include <vector>

#include "dsu_native/api.hpp"

namespace {

dsu::FirmwareHeader make_header(std::uint16_t fw_len_words) {
    std::array<std::uint8_t, dsu::HEADER_SIZE> bytes{};
    bytes[0]  = 0x01;                                  // crypt_mode
    bytes[1]  = 0x02;                                  // device_header
    bytes[12] = static_cast<std::uint8_t>(fw_len_words & 0xFF);
    bytes[13] = static_cast<std::uint8_t>(fw_len_words >> 8);
    auto h = dsu::parse_header(bytes.data(), bytes.size());
    REQUIRE(h.has_value());
    return *h;
}

std::vector<std::uint8_t> make_payload(std::size_t bytes) {
    std::vector<std::uint8_t> p(bytes);
    for (std::size_t i = 0; i < bytes; ++i) {
        p[i] = static_cast<std::uint8_t>(i & 0xFF);
    }
    return p;
}

}  // namespace

TEST_CASE("PacketIterator emits FW_INFO first") {
    auto header  = make_header(8);              // 8 words = 32 bytes payload
    auto payload = make_payload(32);
    dsu::PacketIterator it(header, payload);

    auto first = it.next();
    REQUIRE(first.has_value());
    REQUIRE(first->cmd == dsu::CMD_FW_INFO);
    REQUIRE(first->data.size() == dsu::HEADER_SIZE);
}

TEST_CASE("PacketIterator emits FW_PACK with 2-byte word offset prefix") {
    auto header  = make_header(8);              // 32 bytes
    auto payload = make_payload(32);
    dsu::PacketIterator it(header, payload);

    (void)it.next();                             // skip FW_INFO
    auto p = it.next();
    REQUIRE(p.has_value());
    REQUIRE(p->cmd == dsu::CMD_FW_PACK);
    REQUIRE(p->data.size() == 2 + 32);
    REQUIRE(p->data[0] == 0x00);                 // word offset = 0
    REQUIRE(p->data[1] == 0x00);
    REQUIRE(p->data[2] == 0x00);                 // first payload byte
    REQUIRE(p->data[33] == 0x1F);
}

TEST_CASE("PacketIterator splits into multiple FW_PACK blocks") {
    auto header  = make_header(16);              // 64 bytes payload
    auto payload = make_payload(64);
    dsu::PacketIterator it(header, payload);

    (void)it.next();                             // FW_INFO
    auto p1 = it.next();
    auto p2 = it.next();
    auto p3 = it.next();

    REQUIRE(p1.has_value());
    REQUIRE(p2.has_value());
    REQUIRE_FALSE(p3.has_value());

    // p1: word offset 0, bytes 0..31
    REQUIRE(p1->data[0] == 0x00);
    REQUIRE(p1->data[1] == 0x00);
    REQUIRE(p1->data.size() == 2 + 32);
    REQUIRE(p1->data[2 + 31] == 0x1F);

    // p2: word offset 8 (32 bytes / 4 = 8 words), bytes 32..63
    REQUIRE(p2->data[0] == 0x08);
    REQUIRE(p2->data[1] == 0x00);
    REQUIRE(p2->data.size() == 2 + 32);
    REQUIRE(p2->data[2] == 0x20);
    REQUIRE(p2->data[2 + 31] == 0x3F);
}

TEST_CASE("PacketIterator handles trailing short block") {
    auto header  = make_header(10);              // 40 bytes payload
    auto payload = make_payload(40);
    dsu::PacketIterator it(header, payload);

    (void)it.next();                             // FW_INFO
    auto p1 = it.next();
    auto p2 = it.next();
    auto p3 = it.next();

    REQUIRE(p1.has_value());
    REQUIRE(p1->data.size() == 2 + 32);

    REQUIRE(p2.has_value());
    REQUIRE(p2->data.size() == 2 + 8);           // last 8 bytes
    REQUIRE(p2->data[0] == 0x08);                // word offset 8

    REQUIRE_FALSE(p3.has_value());
}

TEST_CASE("PacketIterator reset rewinds") {
    auto header  = make_header(8);
    auto payload = make_payload(32);
    dsu::PacketIterator it(header, payload);

    (void)it.next();
    (void)it.next();
    REQUIRE_FALSE(it.next().has_value());

    it.reset();
    auto first = it.next();
    REQUIRE(first.has_value());
    REQUIRE(first->cmd == dsu::CMD_FW_INFO);
}
