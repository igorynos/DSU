# DSU — Device Setup Utility

[![Go](https://img.shields.io/badge/Go-1.23-00ADD8?logo=go)](https://go.dev/) [![CI](https://github.com/igorynos/DSU/actions/workflows/ci.yml/badge.svg)](https://github.com/igorynos/DSU/actions/workflows/ci.yml)

Go implementation of a network discovery, configuration, and firmware utility for CP-18, POS, AP-PRO, and TW-2020 access-control devices. This repository succeeds [DSU-python](https://github.com/igorynos/DSU-python).

## Features

- Exact 128-byte device-summary decoder
- Locator packet encoder/decoder with serial addressing and checksum validation
- UDP broadcast discovery on port 1770
- Primary network settings: name, IP, mask, gateway, host, port, and comment
- ELUDP commands for restart and boot-mode switching
- Firmware header validation, checksum verification, chunking, retries, and upload progress
- Concurrency-safe device registry with add/update/remove events and watchdog pruning
- Bounded command timeouts and three-attempt retry policy

## Layout

```text
cmd/dsu             CLI application
internal/device     device model and binary summary codec
internal/protocol   Locator and ELUDP transports
internal/firmware   firmware validation and chunk generation
internal/registry   concurrent device registry and watchdog events
configs             configuration example
```

## Usage

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

UDP broadcast may require firewall configuration, host networking, or elevated network capabilities. Firmware updates should first be verified against a non-production controller model.

## Protocol safety

Malformed headers, lengths, checksums, serial numbers, firmware sizes, and firmware checksums are rejected before commands are executed. Network operations have explicit deadlines and retry limits; no command waits indefinitely.
