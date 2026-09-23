# DSU — Device Setup Utility

[![Go](https://img.shields.io/badge/Go-1.23-00ADD8?logo=go)](https://go.dev/) [![CI](https://github.com/igorynos/DSU/actions/workflows/ci.yml/badge.svg)](https://github.com/igorynos/DSU/actions/workflows/ci.yml)

Network discovery and configuration utility for embedded access-control devices. DSU finds controllers over UDP broadcast, decodes binary responses, and exposes device data through a small command-line application.

This is the Go successor to [DSU-python](https://github.com/igorynos/DSU-python).

## Why this project

DSU demonstrates work with binary protocols and real network hardware rather than a conventional JSON API. Protocol decoding is isolated from transport and presentation, making new controller families easier to add.

## Implemented

- IPv4 UDP broadcast discovery
- Bounded scans with context cancellation
- Binary packet decoding into typed device models
- Device IP, port, MAC, name, and last-seen metadata
- JSON output for scripts and diagnostics
- Protocol-level unit tests and container build

## Architecture

```text
cmd/dsu              CLI entry point
internal/discovery   UDP transport and scan lifecycle
internal/device      Protocol models and binary decoder
```

## Quick start

```bash
go test ./...
go run ./cmd/dsu
```

Broadcast traffic may require host networking or additional permissions inside a container.

## Roadmap

- Full CP-18, POS, AP-PRO, and TW-2020 protocol coverage
- Device configuration and reboot commands
- Reliable chunked firmware transfer
- Device registry and offline watchdog
- Desktop UI adapter
