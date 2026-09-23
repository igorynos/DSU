package firmware

import "testing"

func TestChunks(t *testing.T) {
	v := Image{Data: make([]byte, 300)}.Chunks(128)
	if len(v) != 3 || len(v[0]) != 132 || len(v[2]) != 48 {
		t.Fatalf("bad chunks %#v", v)
	}
}
