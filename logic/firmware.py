import threading
from enum import Enum

import logic.devices as devices
import logic.eludp as eludp
import keyboard
import logic.locator as locator
import test_module.test as test


class CryptMode(Enum):
    NONE = 0
    GOST = 1
    XOR_GOST = 2


class Firmware(object):
    BLOCK_SIZE = 32
    """
    Открывает файл прошивки и считыватет заголовок
    Указатель остается на первом байте после заголовка
    """

    def __init__(self, fw_name):
        self.__progress = 0
        self.cnt = 0
        try:
            fw_file = open(fw_name, mode='rb')
            self.__header = fw_file.read(20)
            self.fw = fw_file.read(self.header['fw_len'] * 4)
        except FileNotFoundError:
            self.__header = None

    def __call__(self):
        """
        Генератор выдает очередной пакет байтов прошивки и изменяет параметр progress
        Когда прочитан передан последний пакет progress становится равным 100%
        :return:
        """
        if self.header is None:
            self.__progress = 100
            return

        yield eludp.ElCmd.FW_INFO.value + self.__header
        fw_index = 0
        fw_len = self.header['fw_len'] * 4
        self.cnt = 0
        while fw_index < fw_len:
            self.cnt += 1
            self.__progress = int(100 * fw_index / fw_len)
            block_size = Firmware.BLOCK_SIZE if fw_len - \
                fw_index > Firmware.BLOCK_SIZE else fw_len - fw_index
            pack = eludp.ElCmd.FW_PACK.value + \
                (fw_index // 4).to_bytes(2, byteorder='little') + \
                self.fw[fw_index: fw_index+block_size]
            fw_index += Firmware.BLOCK_SIZE
            yield pack
        self.__progress = 100

    @property
    def header(self):
        """
        Возвращает словарь с параметрами прошивки из заголовка
        Заголовок имеет следующую структуру:
            typedef struct
            {
                uint8_t     crypt_mode;     // Способ шифрования
                uint8_t     device_header;  // Версия заголовка устройства
                uint8_t     fw_ver[2];      // Версия прошивки
                uint8_t     reserved[2];    // Зарезервировано
                uint8_t     pcb_ver[2];     // Версия печатной платы, под которую сделана прошивка
                uint8_t     btldr_ver[2];   // Версия загрузчика, под который сделана прошивка
                uint32_t    offset;         // Начальный адрес прошивки
                uint16_t    fw_len;         // Длина прошивки
                uint8_t     reserved_2[2];  // Зарезервировано
                uint32_t    check_sum;      // Контрольная сумма
            } FirmwareHeader;
        :return: словарь с параметрами
        """
        if self.__header is None:
            return None
        return {'crypt_mode': int(self.__header[0]),
                'device_header': int(self.__header[1]),
                'fw_ver': f'{self.__header[3]}.{self.__header[2]}',
                'pcb_ver': f'{self.__header[5]}.{self.__header[4]}',
                'btldr_ver': f'{self.__header[7]}.{self.__header[6]}',
                'offset': int.from_bytes(self.__header[8:12], byteorder='little'),
                'fw_len': int.from_bytes(self.__header[12:14], byteorder='little'),
                'check_sum': int.from_bytes(self.__header[16:20], byteorder='little')
                }

    def progress(self):
        progress = self.__progress
        if progress == 100:
            self.__progress = 0
        return progress


def load_fw():
    dev = test.get_queue_test_device(devs)
    if not isinstance(dev, devices.Device):
        print('No device')
        return
    dev.queue.cbs = test.queue_result
    dev.queue.append(locator.LocatorCmd.EXE_EL_CMD,
                     pack=eludp.ElCmd.RUN_BTLDR.value,
                     pause=10)
    dev.queue.append(locator.LocatorCmd.EXE_EL_CMD,
                     gen=Firmware('d:/Yar/Development/NXP/Projects/Parking/Main/V3.003/'
                                  'FLASH-0x10000/OBJECTS/parking.bin/parking_pcb2.0_v3.003_test7.fw'))
    dev.queue.append(locator.LocatorCmd.EXE_EL_CMD,
                     pack=eludp.ElCmd.RUN_MAIN.value,
                     pause=10)
    dev.queue.run()


if __name__ == '__main__':
    devs = devices.DeviceList()
    devs.bind(test.cbs1, [devices.DevLstEvent.UPDATE_DEV,
                          devices.DevLstEvent.APPEND_DEV,
                          devices.DevLstEvent.REMOVE_DEV,
                          ])
    lctr = locator.Locator(devs)
    keyboard.add_hotkey("F12", lctr.shutdown)
    # d = test.get_queue_test_device(devs)
    keyboard.add_hotkey("F11", load_fw)

    lctr_thr = threading.Thread(
        target=lctr.run, name='locator.run() threading')
    lctr_thr.start()

    lctr_thr.join()
