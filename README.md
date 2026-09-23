# DSU — Device Setup Utility

Go rewrite of [DSU-python](https://github.com/igorynos/DSU-python), a utility for discovering, configuring, and maintaining network controllers.

## Current migration

- UDP broadcast discovery client
- Binary response decoding into typed device models
- Context cancellation and bounded discovery timeout
- JSON CLI output
- Unit-tested protocol parsing and container build

```bash
go test ./...
go run ./cmd/dsu
```

Broadcast discovery may require host networking or elevated network permissions. The next stage ports the complete CP-18/POS/AP-PRO/TW-2020 protocol, configuration commands, firmware transfer, registry/watchdog, and desktop UI.
