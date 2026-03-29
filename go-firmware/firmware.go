package main

import (
	"encoding/binary"
	"encoding/json"
	"fmt"
	"io"
	"os"
)

const (
	BlockSize     = 32
	HeaderSize    = 20
	FW_INFO_CMD   = 0x03
	FW_PACK_CMD   = 0x04
	RUN_BTLDR_CMD = 0x06
	RUN_MAIN_CMD  = 0x05
)

// FirmwareHeader представляет заголовок файла прошивки
type FirmwareHeader struct {
	CryptMode     uint8  `json:"crypt_mode"`
	DeviceHeader  uint8  `json:"device_header"`
	FwVer         string `json:"fw_ver"`
	PcbVer        string `json:"pcb_ver"`
	BtldrVer      string `json:"btldr_ver"`
	Offset        uint32 `json:"offset"`
	FwLen         uint16 `json:"fw_len"`
	CheckSum      uint32 `json:"check_sum"`
}

// Firmware представляет файл прошивки
type Firmware struct {
	Header     *FirmwareHeader
	Data       []byte
	headerRaw  []byte
}

// Packet представляет пакет данных для отправки
type Packet struct {
	Cmd  byte   `json:"cmd"`
	Data []byte `json:"data"`
}

// NewFirmware создает новый объект прошивки из файла
func NewFirmware(filename string) (*Firmware, error) {
	file, err := os.Open(filename)
	if err != nil {
		return nil, fmt.Errorf("failed to open file: %w", err)
	}
	defer file.Close()

	fw := &Firmware{}

	// Читаем заголовок
	fw.headerRaw = make([]byte, HeaderSize)
	if _, err := io.ReadFull(file, fw.headerRaw); err != nil {
		return nil, fmt.Errorf("failed to read header: %w", err)
	}

	// Парсим заголовок
	fw.Header = &FirmwareHeader{
		CryptMode:    fw.headerRaw[0],
		DeviceHeader: fw.headerRaw[1],
		FwVer:        fmt.Sprintf("%d.%d", fw.headerRaw[3], fw.headerRaw[2]),
		PcbVer:       fmt.Sprintf("%d.%d", fw.headerRaw[7], fw.headerRaw[6]),
		BtldrVer:     fmt.Sprintf("%d.%d", fw.headerRaw[9], fw.headerRaw[8]),
		Offset:       binary.LittleEndian.Uint32(fw.headerRaw[10:14]),
		FwLen:        binary.LittleEndian.Uint16(fw.headerRaw[14:16]),
		CheckSum:     binary.LittleEndian.Uint32(fw.headerRaw[16:20]),
	}

	// Читаем данные прошивки
	dataLen := int(fw.Header.FwLen) * 4
	fw.Data = make([]byte, dataLen)
	if _, err := io.ReadFull(file, fw.Data); err != nil {
		return nil, fmt.Errorf("failed to read firmware data: %w", err)
	}

	return fw, nil
}

// GeneratePackets генерирует все пакеты для прошивки
func (fw *Firmware) GeneratePackets() []Packet {
	if fw.Header == nil {
		return nil
	}

	packets := make([]Packet, 0)

	// Первый пакет - заголовок
	headerPacket := Packet{
		Cmd:  FW_INFO_CMD,
		Data: fw.headerRaw,
	}
	packets = append(packets, headerPacket)

	// Пакеты с данными
	fwLen := int(fw.Header.FwLen) * 4
	fwIndex := 0

	for fwIndex < fwLen {
		blockSize := BlockSize
		if fwLen-fwIndex < BlockSize {
			blockSize = fwLen - fwIndex
		}

		// Создаем пакет: CMD (1 byte) + Index (2 bytes) + Data (blockSize bytes)
		packetData := make([]byte, 2+blockSize)

		// Индекс в 32-битных словах (fw_index / 4)
		indexWords := uint16(fwIndex / 4)
		binary.LittleEndian.PutUint16(packetData[0:2], indexWords)

		// Копируем данные
		copy(packetData[2:], fw.Data[fwIndex:fwIndex+blockSize])

		packet := Packet{
			Cmd:  FW_PACK_CMD,
			Data: packetData,
		}
		packets = append(packets, packet)

		fwIndex += BlockSize
	}

	return packets
}

// ProgressCallback вызывается для отслеживания прогресса
type ProgressCallback func(percent int)

// GeneratePacketsWithProgress генерирует пакеты с отслеживанием прогресса
func (fw *Firmware) GeneratePacketsWithProgress(callback ProgressCallback) []Packet {
	packets := fw.GeneratePackets()

	if callback != nil {
		totalPackets := len(packets)
		for i := range packets {
			percent := (i * 100) / totalPackets
			callback(percent)
		}
		callback(100)
	}

	return packets
}

// ToJSON сериализует пакеты в JSON
func PacketsToJSON(packets []Packet) (string, error) {
	data, err := json.Marshal(packets)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintf(os.Stderr, "Usage: %s <firmware.fw> [--json]\n", os.Args[0])
		os.Exit(1)
	}

	filename := os.Args[1]
	outputJSON := len(os.Args) > 2 && os.Args[2] == "--json"

	fw, err := NewFirmware(filename)
	if err != nil {
		fmt.Fprintf(os.Stderr, "Error: %v\n", err)
		os.Exit(1)
	}

	if outputJSON {
		// Вывод в JSON формате для Python
		packets := fw.GeneratePackets()

		output := map[string]interface{}{
			"header":       fw.Header,
			"packet_count": len(packets),
			"packets":      packets,
		}

		jsonData, _ := json.MarshalIndent(output, "", "  ")
		fmt.Println(string(jsonData))
	} else {
		// Вывод информации о прошивке
		fmt.Printf("Firmware Information:\n")
		fmt.Printf("  FW Version:     %s\n", fw.Header.FwVer)
		fmt.Printf("  PCB Version:    %s\n", fw.Header.PcbVer)
		fmt.Printf("  Bootloader:     %s\n", fw.Header.BtldrVer)
		fmt.Printf("  Crypt Mode:     %d\n", fw.Header.CryptMode)
		fmt.Printf("  Data Length:    %d words (%d bytes)\n", fw.Header.FwLen, fw.Header.FwLen*4)
		fmt.Printf("  Offset:         0x%08X\n", fw.Header.Offset)
		fmt.Printf("  Checksum:       0x%08X\n", fw.Header.CheckSum)

		packets := fw.GeneratePackets()
		fmt.Printf("\nTotal packets:    %d\n", len(packets))
		fmt.Printf("  Header packet:  1\n")
		fmt.Printf("  Data packets:   %d\n", len(packets)-1)
	}
}
