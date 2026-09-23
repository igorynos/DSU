package discovery

import (
	"context"
	"github.com/igorynos/DSU/internal/device"
	"net"
	"time"
)

type Scanner struct {
	Address string
	Request []byte
	Timeout time.Duration
}

func (s Scanner) Scan(ctx context.Context) ([]device.Device, error) {
	if s.Address == "" {
		s.Address = "255.255.255.255:1770"
	}
	if s.Timeout == 0 {
		s.Timeout = 2 * time.Second
	}
	addr, err := net.ResolveUDPAddr("udp4", s.Address)
	if err != nil {
		return nil, err
	}
	conn, err := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4zero, Port: 0})
	if err != nil {
		return nil, err
	}
	defer conn.Close()
	if err = conn.SetWriteBuffer(64 * 1024); err != nil {
		return nil, err
	}
	if _, err = conn.WriteToUDP(s.Request, addr); err != nil {
		return nil, err
	}
	deadline := time.Now().Add(s.Timeout)
	var result []device.Device
	buf := make([]byte, 2048)
	for {
		if err = conn.SetReadDeadline(deadline); err != nil {
			return nil, err
		}
		n, _, readErr := conn.ReadFromUDP(buf)
		if ne, ok := readErr.(net.Error); ok && ne.Timeout() {
			return result, nil
		}
		if readErr != nil {
			return nil, readErr
		}
		d, parseErr := device.ParseResponse(buf[:n])
		if parseErr == nil {
			result = append(result, d)
		}
		select {
		case <-ctx.Done():
			return result, ctx.Err()
		default:
		}
	}
}
