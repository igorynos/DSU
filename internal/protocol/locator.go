package protocol

import (
	"encoding/hex"
	"errors"
	"fmt"
	"github.com/igorynos/DSU/internal/device"
	"net"
	"time"
)

const Password = "12345678"

type Command byte

const (
	Request              Command = 0x01
	SetPrimary           Command = 0x02
	ReadSettings         Command = 0x03
	ExecuteEL            Command = 0x04
	ReadMemoryProperties Command = 0x05
	ReadMemoryDump       Command = 0x06
	GetMap               Command = 0x07
	GetLog               Command = 0x08
	ClearLog             Command = 0x09
	SetUser              Command = 0x0A
	GetUser              Command = 0x0B
)

type Packet struct {
	Serial  string
	Version byte
	Command Command
	Payload []byte
}

func Encode(cmd Command, serial string, payload []byte) ([]byte, error) {
	if len(payload) > 255 {
		return nil, errors.New("payload too large")
	}
	sn := make([]byte, 16)
	if serial != "" {
		v, e := hex.DecodeString(serial)
		if e != nil || len(v) != 16 {
			return nil, errors.New("serial must be 32 hex characters")
		}
		for i := range v {
			sn[i] = v[len(v)-1-i]
		}
	} else {
		for i := range sn {
			sn[i] = 0xff
		}
	}
	b := append([]byte(Password), sn...)
	b = append(b, 1, byte(cmd), byte(len(payload)))
	b = append(b, payload...)
	b = append(b, checksum(b))
	return b, nil
}
func Decode(b []byte) (Packet, error) {
	if len(b) < 28 || string(b[:8]) != Password {
		return Packet{}, errors.New("invalid locator header")
	}
	n := int(b[26])
	if len(b) != 28+n {
		return Packet{}, fmt.Errorf("invalid packet length %d", len(b))
	}
	if checksum(b[:len(b)-1]) != b[len(b)-1] {
		return Packet{}, errors.New("invalid checksum")
	}
	sn := append([]byte(nil), b[8:24]...)
	for i, j := 0, len(sn)-1; i < j; i, j = i+1, j-1 {
		sn[i], sn[j] = sn[j], sn[i]
	}
	return Packet{Serial: hex.EncodeToString(sn), Version: b[24], Command: Command(b[25]), Payload: append([]byte(nil), b[27:len(b)-1]...)}, nil
}
func checksum(b []byte) byte {
	var sum byte
	for _, v := range b {
		sum -= v
	}
	return sum
}

type Client struct {
	Port    int
	Timeout time.Duration
	Retries int
}

func (c Client) Broadcast(cmd Command, serial string, payload []byte) ([]Packet, error) {
	if c.Port == 0 {
		c.Port = 1770
	}
	if c.Timeout == 0 {
		c.Timeout = 500 * time.Millisecond
	}
	b, e := Encode(cmd, serial, payload)
	if e != nil {
		return nil, e
	}
	conn, e := net.ListenUDP("udp4", &net.UDPAddr{IP: net.IPv4zero, Port: 0})
	if e != nil {
		return nil, e
	}
	defer conn.Close()
	conn.SetWriteBuffer(64 << 10)
	if _, e = conn.WriteToUDP(b, &net.UDPAddr{IP: net.IPv4bcast, Port: c.Port}); e != nil {
		return nil, e
	}
	deadline := time.Now().Add(c.Timeout)
	var out []Packet
	buf := make([]byte, 2048)
	for {
		conn.SetReadDeadline(deadline)
		n, _, err := conn.ReadFromUDP(buf)
		if ne, ok := err.(net.Error); ok && ne.Timeout() {
			return out, nil
		}
		if err != nil {
			return nil, err
		}
		p, err := Decode(buf[:n])
		if err == nil {
			out = append(out, p)
		}
	}
}
func (c Client) Discover() ([]device.Device, error) {
	packets, e := c.Broadcast(Request, "", nil)
	if e != nil {
		return nil, e
	}
	var out []device.Device
	for _, p := range packets {
		d, e := device.ParseSummary(p.Payload)
		if e == nil {
			out = append(out, d)
		}
	}
	return out, nil
}
func (c Client) SendWithRetry(cmd Command, serial string, payload []byte) (Packet, error) {
	tries := c.Retries
	if tries == 0 {
		tries = 3
	}
	for i := 0; i < tries; i++ {
		packets, e := c.Broadcast(cmd, serial, payload)
		if e != nil {
			return Packet{}, e
		}
		for _, p := range packets {
			if p.Command == cmd {
				return p, nil
			}
		}
	}
	return Packet{}, errors.New("device response timeout")
}
