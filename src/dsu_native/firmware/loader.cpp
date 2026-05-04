#include "dsu_native/api.hpp"

#include <fstream>
#include <stdexcept>

namespace dsu {

FirmwareLoader::FirmwareLoader(const std::string& path) {
    std::ifstream file(path, std::ios::binary);
    if (!file) {
        return;
    }

    std::array<std::uint8_t, HEADER_SIZE> raw{};
    file.read(reinterpret_cast<char*>(raw.data()), HEADER_SIZE);
    if (file.gcount() != static_cast<std::streamsize>(HEADER_SIZE)) {
        return;
    }
    header_ = parse_header(raw.data(), raw.size());
    if (!header_) {
        return;
    }

    const std::size_t payload_bytes =
        static_cast<std::size_t>(header_->fw_len) * 4;
    payload_.resize(payload_bytes);
    file.read(reinterpret_cast<char*>(payload_.data()),
              static_cast<std::streamsize>(payload_bytes));
    if (file.gcount() != static_cast<std::streamsize>(payload_bytes)) {
        // Truncated payload: keep what we got but mark invalid by clearing header.
        payload_.clear();
        header_.reset();
        return;
    }

    iter_.emplace(*header_, payload_);
}

bool FirmwareLoader::is_valid() const noexcept {
    return header_.has_value();
}

const FirmwareHeader& FirmwareLoader::header() const {
    if (!header_) {
        throw std::runtime_error("FirmwareLoader: invalid firmware (no header)");
    }
    return *header_;
}

std::size_t FirmwareLoader::size() const noexcept {
    return payload_.size();
}

std::optional<Packet> FirmwareLoader::next_packet() {
    if (!iter_) return std::nullopt;
    return iter_->next();
}

void FirmwareLoader::reset() {
    if (iter_) iter_->reset();
}

int FirmwareLoader::progress() const {
    return iter_ ? iter_->progress() : 100;
}

}  // namespace dsu
