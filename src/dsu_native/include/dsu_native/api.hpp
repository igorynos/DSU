#pragma once

#include <array>
#include <cstddef>
#include <cstdint>
#include <optional>
#include <string>
#include <vector>

namespace dsu {

constexpr std::size_t HEADER_SIZE  = 20;
constexpr std::size_t BLOCK_SIZE   = 32;   // bytes per FW_PACK payload
constexpr std::uint8_t CMD_FW_INFO = 0x03;
constexpr std::uint8_t CMD_FW_PACK = 0x04;

struct FirmwareHeader {
    std::uint8_t  crypt_mode;
    std::uint8_t  device_header;
    std::string   fw_ver;       // formatted "hi.lo"
    std::string   pcb_ver;
    std::string   btldr_ver;
    std::uint32_t offset;       // memory offset from header field at byte 8
    std::uint16_t fw_len;       // length in 32-bit words
    std::uint32_t check_sum;
    std::array<std::uint8_t, HEADER_SIZE> raw;  // raw 20 bytes, used in FW_INFO packet
};

/// Parse a 20-byte header. Returns nullopt if input is too short.
std::optional<FirmwareHeader> parse_header(const std::uint8_t* data, std::size_t len);

}  // namespace dsu
