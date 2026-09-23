package protocol

import (
	"errors"
	"net"
	"time"
)

type ELCommand byte

const (
	SetAddress    ELCommand = 0x01
	Restart       ELCommand = 0x02
	FirmwareInfo  ELCommand = 0x03
	FirmwareChunk ELCommand = 0x04
	RunMain       ELCommand = 0x05
	RunBootloader ELCommand = 0x06
)

type ELClient struct {
	Timeout time.Duration
	Retries int
}

func (c ELClient) Send(addr *net.UDPAddr, cmd ELCommand, payload []byte) ([]byte, error) {
	if c.Timeout == 0 {
		c.Timeout = time.Second
	}
	if c.Retries == 0 {
		c.Retries = 3
	}
	conn, e := net.ListenUDP("udp4", nil)
	if e != nil {
		return nil, e
	}
	defer conn.Close()
	pack := append([]byte{byte(cmd)}, payload...)
	buf := make([]byte, 2048)
	for i := 0; i < c.Retries; i++ {
		if _, e = conn.WriteToUDP(pack, addr); e != nil {
			return nil, e
		}
		conn.SetReadDeadline(time.Now().Add(c.Timeout))
		n, from, e := conn.ReadFromUDP(buf)
		if e == nil && from.IP.Equal(addr.IP) {
			return append([]byte(nil), buf[:n]...), nil
		}
		if ne, ok := e.(net.Error); !ok || !ne.Timeout() {
			return nil, e
		}
	}
	return nil, errors.New("ELUDP response timeout")
}
