#include "dsu_native/api.hpp"

#include <array>
#include <cstring>
#include <sstream>

namespace dsu {

namespace {

std::string format_version(std::uint8_t lo, std::uint8_t hi) {
    std::ostringstream os;
    os << static_cast<int>(hi) << '.' << static_cast<int>(lo);
    return os.str();
}

std::uint16_t read_u16_le(const std::uint8_t* p) {
    return static_cast<std::uint16_t>(p[0] | (p[1] << 8));
}

std::uint32_t read_u32_le(const std::uint8_t* p) {
    return static_cast<std::uint32_t>(
        p[0] | (p[1] << 8) | (p[2] << 16) | (p[3] << 24));
}

}  // namespace

std::optional<FirmwareHeader> parse_header(const std::uint8_t* data, std::size_t len) {
    if (data == nullptr || len < HEADER_SIZE) {
        return std::nullopt;
    }
    FirmwareHeader h{};
    h.crypt_mode    = data[0];
    h.device_header = data[1];
    h.fw_ver        = format_version(data[2], data[3]);
    h.pcb_ver       = format_version(data[4], data[5]);
    h.btldr_ver     = format_version(data[6], data[7]);
    h.offset        = read_u32_le(data + 8);
    h.fw_len        = read_u16_le(data + 12);
    h.check_sum     = read_u32_le(data + 16);
    std::memcpy(h.raw.data(), data, HEADER_SIZE);
    return h;
}

}  // namespace dsu
