package protocol

import (
	"bytes"
	"testing"
)

func TestPacketRoundTrip(t *testing.T) {
	serial := "00112233445566778899aabbccddeeff"
	b, e := Encode(SetPrimary, serial, []byte{1, 2, 3})
	if e != nil {
		t.Fatal(e)
	}
	p, e := Decode(b)
	if e != nil {
		t.Fatal(e)
	}
	if p.Serial != serial || p.Command != SetPrimary || !bytes.Equal(p.Payload, []byte{1, 2, 3}) {
		t.Fatalf("bad packet %#v", p)
	}
}
