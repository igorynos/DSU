#include "dsu_native/api.hpp"

#include <algorithm>

namespace dsu {

PacketIterator::PacketIterator(FirmwareHeader header,
                               std::vector<std::uint8_t> payload)
    : header_(std::move(header)),
      payload_(std::move(payload)),
      byte_offset_(0),
      info_emitted_(false) {}

void PacketIterator::reset() {
    byte_offset_  = 0;
    info_emitted_ = false;
}

int PacketIterator::progress() const {
    const std::size_t total = static_cast<std::size_t>(header_.fw_len) * 4;
    if (total == 0) return 100;
    if (byte_offset_ >= total) return 100;
    return static_cast<int>((byte_offset_ * 100) / total);
}

std::optional<Packet> PacketIterator::next() {
    if (!info_emitted_) {
        info_emitted_ = true;
        Packet pkt;
        pkt.cmd = CMD_FW_INFO;
        pkt.data.assign(header_.raw.begin(), header_.raw.end());
        return pkt;
    }

    const std::size_t total = static_cast<std::size_t>(header_.fw_len) * 4;
    if (byte_offset_ >= total || byte_offset_ >= payload_.size()) {
        return std::nullopt;
    }

    const std::size_t remaining =
        std::min(total, payload_.size()) - byte_offset_;
    const std::size_t block = std::min<std::size_t>(BLOCK_SIZE, remaining);

    Packet pkt;
    pkt.cmd = CMD_FW_PACK;
    pkt.data.reserve(2 + block);

    const std::uint16_t word_offset =
        static_cast<std::uint16_t>(byte_offset_ / 4);
    pkt.data.push_back(static_cast<std::uint8_t>(word_offset & 0xFF));
    pkt.data.push_back(static_cast<std::uint8_t>((word_offset >> 8) & 0xFF));
    pkt.data.insert(pkt.data.end(),
                    payload_.begin() + byte_offset_,
                    payload_.begin() + byte_offset_ + block);

    byte_offset_ += BLOCK_SIZE;   // matches Qt: offset += FW_BUFF_SIZE / 4 (in words)
    return pkt;
}

}  // namespace dsu
