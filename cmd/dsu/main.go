package main

import (
	"context"
	"encoding/json"
	"github.com/igorynos/DSU/internal/discovery"
	"log"
	"os"
	"time"
)

func main() {
	s := discovery.Scanner{Request: []byte("DISCOVER"), Timeout: 2 * time.Second}
	devices, err := s.Scan(context.Background())
	if err != nil {
		log.Fatal(err)
	}
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	enc.Encode(devices)
}
