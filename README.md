# DSU — Device Setup Utility

[![Go](https://img.shields.io/badge/Go-1.23-00ADD8?logo=go)](https://go.dev/) [![CI](https://github.com/igorynos/DSU/actions/workflows/ci.yml/badge.svg)](https://github.com/igorynos/DSU/actions/workflows/ci.yml)

Go implementation of a network discovery, configuration, and firmware utility for CP-18, POS, AP-PRO, and TW-2020 access-control devices. This repository succeeds [DSU-python](https://github.com/igorynos/DSU-python).

## ✨ Features

- 🔎 **Network discovery:** Locates controllers through IPv4 UDP broadcast on port `1770`.
- 📦 **Binary protocol:** Encodes and validates Locator packets with serial addressing, length checks, and checksums.
- 🧩 **Device decoding:** Parses the complete 128-byte summary returned by supported controllers.
- ⚙️ **Configuration:** Updates name, IP, mask, gateway, host, ELUDP port, and device comment.
- 🔄 **Device control:** Supports restart and transitions between bootloader and main application modes.
- 💾 **Firmware delivery:** Validates firmware metadata and checksum before reliable chunked upload.
- 🗂️ **Live registry:** Maintains a concurrency-safe collection with add, update, remove, and watchdog events.
- 🛡️ **Bounded execution:** Every network operation has explicit timeouts and a three-attempt retry policy.

## 🎛️ Supported Controllers

| Model | Discovery | Configuration | Boot control | Firmware |
| :--- | :---: | :---: | :---: | :---: |
| CP-18 | ✅ | ✅ | ✅ | ✅ |
| POS | ✅ | ✅ | ✅ | ✅ |
| AP-PRO | ✅ | ✅ | ✅ | ✅ |
| TW-2020 | ✅ | ✅ | ✅ | ✅ |

## 🏗️ Project Layout

```text
cmd/dsu             CLI application
internal/device     device model and binary summary codec
internal/protocol   Locator and ELUDP transports
internal/firmware   firmware validation and chunk generation
internal/registry   concurrent device registry and watchdog events
configs             configuration example
```

## 🚀 Usage

```bash
make test
make build

go run ./cmd/dsu discover

go run ./cmd/dsu set \
  --serial 00112233445566778899AABBCCDDEEFF \
  --name Entrance \
  --ip 192.168.1.20 \
  --mask 255.255.255.0 \
  --gateway 192.168.1.1 \
  --port 1775

go run ./cmd/dsu reboot --addr 192.168.1.20:1775
go run ./cmd/dsu bootloader --addr 192.168.1.20:1775
go run ./cmd/dsu flash --addr 192.168.1.20:1775 --file controller.fw
go run ./cmd/dsu main --addr 192.168.1.20:1775
```

> ⚠️ UDP broadcast may require firewall configuration, host networking, or elevated network capabilities. Firmware updates should first be verified against a non-production controller.

## 🛡️ Protocol Safety

Malformed headers, lengths, checksums, serial numbers, firmware sizes, and firmware checksums are rejected before commands are executed. Network operations have explicit deadlines and retry limits; no command waits indefinitely.

## 🧪 Quality Checks

```bash
go test -race ./...
go vet ./...
go build ./...
docker build -t dsu .
```

GitHub Actions runs the test suite, race detector, static checks, and build for every push and pull request.

## 🐍 Previous Implementation

The original Python/C++ version is preserved in [DSU-python](https://github.com/igorynos/DSU-python) for history and behavior comparison.
