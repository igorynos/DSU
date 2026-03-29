"""
Быстрый модуль прошивки на базе Go
Использует скомпилированный Go бинарник для высокой производительности
"""

import json
import subprocess
import os
from pathlib import Path

import logic.eludp as eludp


class FirmwareGo(object):
    """
    Обертка над Go модулем прошивки для быстрой обработки файлов
    """

    def __init__(self, fw_name):
        self.__progress = 0
        self.cnt = 0
        self.fw_name = fw_name
        self._packets = None
        self._header = None

        # Путь к Go бинарнику
        self.go_binary = Path(__file__).parent.parent / "go-firmware" / "firmware"

        if not self.go_binary.exists():
            raise FileNotFoundError(f"Go firmware binary not found: {self.go_binary}")

        # Загружаем прошивку через Go
        self._load_firmware()

    def _load_firmware(self):
        """Загружает прошивку через Go модуль"""
        try:
            # Вызываем Go программу с флагом --json
            result = subprocess.run(
                [str(self.go_binary), self.fw_name, "--json"],
                capture_output=True,
                text=True,
                check=True
            )

            # Парсим JSON ответ
            data = json.loads(result.stdout)
            self._header = data["header"]

            # Конвертируем пакеты из JSON в bytes
            self._packets = []
            for packet in data["packets"]:
                cmd = packet["cmd"]
                packet_data = bytes(packet["data"])
                self._packets.append((cmd, packet_data))

        except subprocess.CalledProcessError as e:
            print(f"Error loading firmware: {e.stderr}")
            self._header = None
            self._packets = None
        except FileNotFoundError:
            print(f"Firmware file not found: {self.fw_name}")
            self._header = None
            self._packets = None
        except json.JSONDecodeError as e:
            print(f"Error parsing Go output: {e}")
            self._header = None
            self._packets = None

    def __call__(self):
        """
        Генератор выдает очередной пакет байтов прошивки и изменяет параметр progress
        """
        if self._packets is None:
            self.__progress = 100
            return

        total_packets = len(self._packets)

        for i, (cmd, data) in enumerate(self._packets):
            self.cnt += 1
            self.__progress = int((i * 100) / total_packets)

            # Формируем пакет: команда + данные
            pack = bytes([cmd]) + data
            yield pack

        self.__progress = 100

    @property
    def header(self):
        """
        Возвращает словарь с параметрами прошивки из заголовка
        """
        return self._header

    def progress(self):
        """Возвращает текущий прогресс прошивки"""
        progress = self.__progress
        if progress == 100:
            self.__progress = 0
        return progress


# Для обратной совместимости - используем Go версию как Firmware
Firmware = FirmwareGo


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python firmware_go.py <firmware.fw>")
        sys.exit(1)

    fw_file = sys.argv[1]

    print(f"Loading firmware: {fw_file}")
    fw = FirmwareGo(fw_file)

    if fw.header:
        print("\nFirmware Header:")
        print(f"  FW Version:    {fw.header['fw_ver']}")
        print(f"  PCB Version:   {fw.header['pcb_ver']}")
        print(f"  Bootloader:    {fw.header['btldr_ver']}")
        print(f"  Crypt Mode:    {fw.header['crypt_mode']}")
        print(f"  Data Length:   {fw.header['fw_len']} words")
        print(f"  Checksum:      0x{fw.header['check_sum']:08X}")

        print("\nGenerating packets...")
        packet_count = 0
        for packet in fw():
            packet_count += 1

        print(f"Generated {packet_count} packets")
        print(f"Progress: {fw.progress()}%")
    else:
        print("Failed to load firmware")
