package firmware

import (
	"encoding/binary"
	"errors"
	"os"
)

const HeaderSize = 20

type Image struct {
	Version  uint16
	Data     []byte
	Checksum uint32
}

func Open(path string) (Image, error) {
	b, e := os.ReadFile(path)
	if e != nil {
		return Image{}, e
	}
	if len(b) < HeaderSize {
		return Image{}, errors.New("firmware file is too short")
	}
	size := int(binary.LittleEndian.Uint32(b[4:8]))
	if size != len(b)-HeaderSize {
		return Image{}, errors.New("firmware size mismatch")
	}
	expected := binary.LittleEndian.Uint32(b[8:12])
	var actual uint32
	for _, v := range b[HeaderSize:] {
		actual += uint32(v)
	}
	if actual != expected {
		return Image{}, errors.New("firmware checksum mismatch")
	}
	return Image{Version: binary.LittleEndian.Uint16(b[:2]), Data: b[HeaderSize:], Checksum: expected}, nil
}
func (i Image) Chunks(size int) [][]byte {
	if size <= 0 {
		size = 128
	}
	var out [][]byte
	for off := 0; off < len(i.Data); off += size {
		end := off + size
		if end > len(i.Data) {
			end = len(i.Data)
		}
		pack := make([]byte, 4+end-off)
		binary.LittleEndian.PutUint32(pack[:4], uint32(off))
		copy(pack[4:], i.Data[off:end])
		out = append(out, pack)
	}
	return out
}
