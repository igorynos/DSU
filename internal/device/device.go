package device

import (
	"encoding/binary"
	"encoding/hex"
	"errors"
	"net"
	"strconv"
	"strings"
	"time"
)

const SummarySize = 128

var Models = map[byte]string{0: "UNKNOWN", 1: "CP-18", 2: "POS", 3: "AP-PRO", 4: "TW-2020"}
var BootModes = map[byte]string{0: "BOOTLOADER", 1: "MAIN"}

type Device struct {
	Model      string    `json:"model"`
	BootMode   string    `json:"boot_mode"`
	Serial     string    `json:"serial"`
	MAC        string    `json:"mac"`
	Firmware   string    `json:"firmware"`
	Bootloader string    `json:"bootloader"`
	PCB        string    `json:"pcb"`
	Name       string    `json:"name"`
	IP         net.IP    `json:"ip"`
	Mask       net.IP    `json:"mask"`
	Gateway    net.IP    `json:"gateway"`
	Host       net.IP    `json:"host"`
	Port       uint16    `json:"port"`
	Comment    string    `json:"comment"`
	LastSeen   time.Time `json:"last_seen"`
}

func ParseSummary(b []byte) (Device, error) {
	if len(b) != SummarySize {
		return Device{}, errors.New("summary must be 128 bytes")
	}
	d := Device{Model: Models[b[0]], BootMode: BootModes[b[1]], Serial: reverseHex(b[2:18]), MAC: net.HardwareAddr(b[18:24]).String(), Firmware: version(b[24:26]), Bootloader: version(b[26:28]), PCB: version(b[28:30]), Name: text(b[30:46]), IP: net.IPv4(b[46], b[47], b[48], b[49]), Mask: net.IPv4(b[50], b[51], b[52], b[53]), Gateway: net.IPv4(b[54], b[55], b[56], b[57]), Host: net.IPv4(b[58], b[59], b[60], b[61]), Port: binary.LittleEndian.Uint16(b[62:64]), Comment: text(b[64:128]), LastSeen: time.Now().UTC()}
	return d, nil
}
func (d Device) PrimarySettings() []byte {
	b := make([]byte, 98)
	copyText(b[:16], d.Name)
	copy(b[16:20], d.IP.To4())
	copy(b[20:24], d.Mask.To4())
	copy(b[24:28], d.Gateway.To4())
	copy(b[28:32], d.Host.To4())
	binary.LittleEndian.PutUint16(b[32:34], d.Port)
	copyText(b[34:], d.Comment)
	return b
}
func (d Device) Key() string {
	if d.Serial != "" {
		return d.Serial
	}
	return net.JoinHostPort(d.IP.String(), strconv.Itoa(int(d.Port)))
}
func reverseHex(b []byte) string {
	v := append([]byte(nil), b...)
	for i, j := 0, len(v)-1; i < j; i, j = i+1, j-1 {
		v[i], v[j] = v[j], v[i]
	}
	if allZero(v) {
		return ""
	}
	return strings.ToUpper(hex.EncodeToString(v))
}
func version(b []byte) string {
	if allZero(b) {
		return ""
	}
	return strconv.Itoa(int(b[1])) + "." + strconv.Itoa(int(b[0]))
}
func text(b []byte) string          { return strings.TrimRight(string(b), "\x00 ") }
func copyText(dst []byte, s string) { copy(dst, []byte(s)) }
func allZero(b []byte) bool {
	for _, v := range b {
		if v != 0 {
			return false
		}
	}
	return true
}
