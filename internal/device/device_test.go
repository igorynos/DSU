package device

import (
	"encoding/binary"
	"testing"
)

func TestParseSummary(t *testing.T) {
	b := make([]byte, 128)
	b[0] = 1
	b[1] = 1
	for i := 0; i < 16; i++ {
		b[2+i] = byte(i + 1)
	}
	copy(b[18:24], []byte{0, 1, 2, 3, 4, 5})
	b[24] = 3
	b[25] = 2
	copy(b[30:46], []byte("Controller"))
	copy(b[46:50], []byte{192, 168, 1, 10})
	binary.LittleEndian.PutUint16(b[62:64], 1775)
	d, e := ParseSummary(b)
	if e != nil {
		t.Fatal(e)
	}
	if d.Model != "CP-18" || d.Port != 1775 || d.IP.String() != "192.168.1.10" || d.Firmware != "2.3" {
		t.Fatalf("unexpected %#v", d)
	}
	if len(d.PrimarySettings()) != 98 {
		t.Fatal("settings size")
	}
}
