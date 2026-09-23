package device

import (
	"encoding/binary"
	"errors"
	"net"
	"strings"
	"time"
)

type Device struct {
	Name     string           `json:"name"`
	IP       net.IP           `json:"ip"`
	Port     uint16           `json:"port"`
	Model    string           `json:"model"`
	MAC      net.HardwareAddr `json:"mac"`
	LastSeen time.Time        `json:"last_seen"`
}

func ParseResponse(b []byte) (Device, error) {
	if len(b) < 13 {
		return Device{}, errors.New("short discovery response")
	}
	ip := net.IPv4(b[0], b[1], b[2], b[3])
	port := binary.BigEndian.Uint16(b[4:6])
	mac := net.HardwareAddr(append([]byte(nil), b[6:12]...))
	name := strings.TrimRight(string(b[12:]), "\x00 ")
	if name == "" {
		return Device{}, errors.New("empty device name")
	}
	return Device{Name: name, IP: ip, Port: port, MAC: mac, LastSeen: time.Now().UTC()}, nil
}
