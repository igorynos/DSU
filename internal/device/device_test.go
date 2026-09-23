package device

import (
	"testing"
)

func TestParseResponse(t *testing.T) {
	b := []byte{192, 168, 1, 10, 0x06, 0xef, 0, 1, 2, 3, 4, 5, 'C', 'P', '-', '1', '8'}
	d, err := ParseResponse(b)
	if err != nil {
		t.Fatal(err)
	}
	if d.Name != "CP-18" || d.Port != 1775 || d.IP.String() != "192.168.1.10" {
		t.Fatalf("unexpected device: %#v", d)
	}
}
