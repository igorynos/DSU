package main

import (
	"encoding/binary"
	"encoding/json"
	"flag"
	"fmt"
	"github.com/igorynos/DSU/internal/device"
	"github.com/igorynos/DSU/internal/firmware"
	"github.com/igorynos/DSU/internal/protocol"
	"log"
	"net"
	"os"
	"time"
)

func main() {
	flag.Usage = func() { fmt.Fprintln(os.Stderr, "usage: dsu <discover|set|reboot|bootloader|main|flash> [options]") }
	flag.Parse()
	if flag.NArg() == 0 {
		flag.Usage()
		os.Exit(2)
	}
	switch flag.Arg(0) {
	case "discover":
		discover()
	case "set":
		set()
	case "reboot":
		el(protocol.Restart)
	case "bootloader":
		el(protocol.RunBootloader)
	case "main":
		el(protocol.RunMain)
	case "flash":
		flash()
	default:
		flag.Usage()
		os.Exit(2)
	}
}
func discover() {
	c := protocol.Client{Port: 1770, Timeout: 800 * time.Millisecond}
	list, e := c.Discover()
	fatal(e)
	enc := json.NewEncoder(os.Stdout)
	enc.SetIndent("", "  ")
	enc.Encode(list)
}
func set() {
	fs := flag.NewFlagSet("set", flag.ExitOnError)
	serial := fs.String("serial", "", "device serial")
	name := fs.String("name", "", "device name")
	ip := fs.String("ip", "", "IPv4 address")
	mask := fs.String("mask", "255.255.255.0", "network mask")
	gateway := fs.String("gateway", "0.0.0.0", "gateway")
	host := fs.String("host", "0.0.0.0", "host")
	port := fs.Int("port", 1775, "ELUDP port")
	comment := fs.String("comment", "", "comment")
	fs.Parse(flag.Args()[1:])
	d := device.Device{Name: *name, IP: net.ParseIP(*ip), Mask: net.ParseIP(*mask), Gateway: net.ParseIP(*gateway), Host: net.ParseIP(*host), Port: uint16(*port), Comment: *comment}
	if d.IP == nil {
		log.Fatal("valid --ip required")
	}
	_, e := (protocol.Client{Port: 1770, Timeout: time.Second, Retries: 3}).SendWithRetry(protocol.SetPrimary, *serial, d.PrimarySettings())
	fatal(e)
	fmt.Println("settings applied")
}
func el(cmd protocol.ELCommand) {
	fs := flag.NewFlagSet("command", flag.ExitOnError)
	addr := fs.String("addr", "", "device ip:port")
	fs.Parse(flag.Args()[1:])
	a, e := net.ResolveUDPAddr("udp4", *addr)
	fatal(e)
	_, e = (protocol.ELClient{}).Send(a, cmd, nil)
	fatal(e)
	fmt.Println("command completed")
}
func flash() {
	fs := flag.NewFlagSet("flash", flag.ExitOnError)
	addr := fs.String("addr", "", "device ip:port")
	path := fs.String("file", "", "firmware file")
	fs.Parse(flag.Args()[1:])
	a, e := net.ResolveUDPAddr("udp4", *addr)
	fatal(e)
	image, e := firmware.Open(*path)
	fatal(e)
	info := make([]byte, 10)
	binary.LittleEndian.PutUint16(info[:2], image.Version)
	binary.LittleEndian.PutUint32(info[2:6], uint32(len(image.Data)))
	binary.LittleEndian.PutUint32(info[6:10], image.Checksum)
	client := protocol.ELClient{Timeout: 2 * time.Second, Retries: 3}
	_, e = client.Send(a, protocol.FirmwareInfo, info)
	fatal(e)
	for i, chunk := range image.Chunks(128) {
		_, e = client.Send(a, protocol.FirmwareChunk, chunk)
		fatal(e)
		fmt.Printf("\r%d%%", 100*(i+1)/len(image.Chunks(128)))
	}
	fmt.Println("\nfirmware uploaded")
}
func fatal(e error) {
	if e != nil {
		log.Fatal(e)
	}
}
