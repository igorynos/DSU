#!/usr/bin/env python3
"""
Скрипт для сравнения производительности Python и Go версий модуля прошивки
"""

import time
import sys
from pathlib import Path


def benchmark_python(fw_file):
    """Тест Python версии"""
    from logic.firmware import Firmware

    start = time.time()

    # Загрузка файла
    fw = Firmware(fw_file)
    load_time = time.time() - start

    if fw.header is None:
        print("❌ Failed to load firmware (Python)")
        return None

    # Генерация пакетов
    start = time.time()
    packet_count = 0
    for packet in fw():
        packet_count += 1
    gen_time = time.time() - start

    total_time = load_time + gen_time

    return {
        "name": "Python",
        "load_time": load_time,
        "gen_time": gen_time,
        "total_time": total_time,
        "packet_count": packet_count,
        "header": fw.header
    }


def benchmark_go(fw_file):
    """Тест Go версии"""
    from logic.firmware_go import FirmwareGo

    start = time.time()

    # Загрузка файла
    fw = FirmwareGo(fw_file)
    load_time = time.time() - start

    if fw.header is None:
        print("❌ Failed to load firmware (Go)")
        return None

    # Генерация пакетов
    start = time.time()
    packet_count = 0
    for packet in fw():
        packet_count += 1
    gen_time = time.time() - start

    total_time = load_time + gen_time

    return {
        "name": "Go",
        "load_time": load_time,
        "gen_time": gen_time,
        "total_time": total_time,
        "packet_count": packet_count,
        "header": fw.header
    }


def print_results(python_result, go_result):
    """Вывод результатов"""
    print("\n" + "="*60)
    print("BENCHMARK RESULTS")
    print("="*60)

    if python_result:
        print(f"\n📦 Python Version:")
        print(f"  Load time:      {python_result['load_time']*1000:.2f} ms")
        print(f"  Generate time:  {python_result['gen_time']*1000:.2f} ms")
        print(f"  Total time:     {python_result['total_time']*1000:.2f} ms")
        print(f"  Packets:        {python_result['packet_count']}")

    if go_result:
        print(f"\n⚡ Go Version:")
        print(f"  Load time:      {go_result['load_time']*1000:.2f} ms")
        print(f"  Generate time:  {go_result['gen_time']*1000:.2f} ms")
        print(f"  Total time:     {go_result['total_time']*1000:.2f} ms")
        print(f"  Packets:        {go_result['packet_count']}")

    if python_result and go_result:
        speedup_load = python_result['load_time'] / go_result['load_time']
        speedup_gen = python_result['gen_time'] / go_result['gen_time']
        speedup_total = python_result['total_time'] / go_result['total_time']

        print(f"\n🚀 Speedup (Go vs Python):")
        print(f"  Load:           {speedup_load:.1f}x faster")
        print(f"  Generate:       {speedup_gen:.1f}x faster")
        print(f"  Total:          {speedup_total:.1f}x faster")

        if go_result['header']:
            print(f"\n📋 Firmware Info:")
            h = go_result['header']
            print(f"  FW Version:     {h['fw_ver']}")
            print(f"  PCB Version:    {h['pcb_ver']}")
            print(f"  Bootloader:     {h['btldr_ver']}")
            print(f"  Size:           {h['fw_len']} words ({h['fw_len']*4} bytes)")
            print(f"  Checksum:       0x{h['check_sum']:08X}")

    print("\n" + "="*60)


def main():
    if len(sys.argv) < 2:
        print("Usage: python benchmark_firmware.py <firmware.fw>")
        sys.exit(1)

    fw_file = sys.argv[1]

    if not Path(fw_file).exists():
        print(f"❌ File not found: {fw_file}")
        sys.exit(1)

    print(f"🔍 Testing firmware: {fw_file}\n")

    print("Running Python version...")
    python_result = benchmark_python(fw_file)

    print("Running Go version...")
    go_result = benchmark_go(fw_file)

    print_results(python_result, go_result)


if __name__ == "__main__":
    main()
