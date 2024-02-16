import socket

import keyboard
import threading
import netifaces
import logic.devices as devices
from enum import Enum

import test_module.test as test

REQUEST_TIMEOUT = 0.2
CMD_TIMEOUT = 1
POLL_INTERVAL = 2


class LocatorCmd(Enum):
    """ Набор команд широковещательного протокола """
    REQUEST = 0x01
    SET_PRIMARY = 0x02
    READ_SETTINGS = 0x03
    EXE_EL_CMD = 0x04
    READ_MEM_PROP = 0x05
    READ_MEM_DUMP = 0x06
    GET_MAP = 0x07
    GET_LOG = 0x08
    CLEAR_LOG = 0x09
    SET_USER = 0x0A
    GET_USER = 0x0B


class LocatorResult(Enum):
    """ Результаты выполнения команд широковещательного протокола """
    UNKNOWN_CMD = 0x00
    OK = 0x01
    ERROR = 0x02
    OUT_OF_MEM = 0x03
    MEM_ERROR = 0x04


class LocatorErrorCode(Enum):
    DEFAULT = 0xff


class Locator(object):
    """ Широковещательный протокл обмена с устройствами """

    def __init__(self, devices):
        self.__shutdown = False
        self.devices = devices
        ai = [netifaces.ifaddresses(nif).get(socket.AF_INET)
              for nif in netifaces.interfaces()]
        self.ai = [j for i in ai if i is not None for j in i]
        self.current_ai = None
        self.buff_size = 1024
        self.ver = 1
        self.port = 1770
        self.port2 = 1760
        self.pack = bytearray([])
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.bind(('', self.port))
        self.sock_thr = None
        self.poll_timer = None
        self.poll_thr = None

    def listening_port(self):
        """Прослушивание порта широковещательных команд """
        while not self.__shutdown:
            try:
                data, addr = self.sock.recvfrom(self.buff_size)
                if addr[0] in [ai['addr'] for ai in self.ai]:
                    continue
                header = self.check_header(data)
                if len(data) != header['len'] + 28:
                    print(f"Неверная длика пакета: {data}")
                if header['cmd'] == LocatorCmd.REQUEST:
                    self.devices.append(devices.Device(
                        loc=self, data=data[27:-1]))
                elif header['cmd'] in LocatorCmd:
                    self.devices.response_processing(header, data[27:-1])
            except OSError:
                break

    def poll(self):
        """
        Циклически опрашивает устройства в сети с индервалом POLL_INTERVAL
        :return:
        """
        while not self.__shutdown:
            self.poll_timer = threading.Timer(
                interval=POLL_INTERVAL, function=self.request)
            self.poll_timer.name = 'Locator poll timer thread'
            self.poll_timer.start()
            self.poll_timer.join()

    def request(self):
        """
        Подает команду опроса всем устройствам в локальной сети
        :return:
        """
        self.send_pack(LocatorCmd.REQUEST)
        if self.poll_timer is not None:
            self.poll_timer.cancel()

    @staticmethod
    def check_header(ba):
        """
        Проверяет корректность заголовка
        :param ba: массив байтов с заголовком
        :return: словарь параметров заголовка:
        's_num': серийный номер,
        'ver': версия заголовка,
        'cmd': команда,
        'len': длина паета с данными
        """
        if ba[:8].decode('cp1251') != '12345678':
            return {'s_num': None, 'ver': None, 'cmd': None, 'len': 0}
        return {'s_num': ba[23:7:-1].hex(),
                'ver': ba[24],
                'cmd': LocatorCmd(ba[25]),
                'len': ba[26]}

    @staticmethod
    def subnet(addr, mask='255.255.255.0'):
        """ Возвращаетет подсеть для данного адреса"""
        mask = list(map(int, mask.split('.')))
        addr = list(map(int, addr.split('.')))
        return '.'.join([str(mask[i] & addr[i]) for i in range(len(mask))])

    @staticmethod
    def check_sum(ba):
        """ Вычисляет контрольную сумму широковещательной команды """
        s = 0
        for b in ba:
            s -= b
        return s & 0xff

    def send_pack(self, cmd, data=b'', dev=None):
        """
        Посылает команду заданному устройству
        Если устройство не задано, команда отправляется всем устройствам в локальной сети

        :param cmd: команда
        :param data: данные команды
        :param dev: устройство, которому адресована команда
        :return:
        """
        s_n = bytes.fromhex(dev.s_num) if isinstance(
            dev, devices.Device) else bytes([0xff]*16)
        """ 
        Заголовок команды отределяется следующей структурой языка Си
        typedef struct
        {
            uint8_t         password[8];
            uint8_t         s_num[16];
            uint8_t         ver;
            uint8_t         cmd;
            uint8_t         len;
        } LOCATOR_Header;
        """
        if isinstance(cmd, Enum):
            cmd = cmd.value
        self.pack = bytearray('12345678', encoding='cp1251')
        self.pack += s_n[::-1]
        self.pack.append(self.ver)
        self.pack.append(cmd)
        self.pack.append(len(data))
        self.pack += data
        self.pack.append(self.check_sum(self.pack))
        for ai in self.ai:
            if dev is not None and dev.ai is not None and dev.ai != ai:
                continue
            if not self.__shutdown:
                self.sock.sendto(self.pack, (ai['broadcast'], self.port))

    def run(self):
        """
        Основной цикл потока широковещательного протокола
        :return:
        """
        self.sock_thr = threading.Thread(target=self.listening_port,
                                         name=f'Listening locator UDP-port {self.port}')
        self.sock_thr.start()
        self.poll_thr = threading.Thread(
            target=self.poll, name='Locator poll thread')
        self.poll_thr.start()
        self.request()
        while not self.__shutdown:
            pass
        self.sock.close()
        self.sock_thr.join()
        self.poll_timer.cancel()
        self.poll_thr.join()
        self.devices.clear()

    def shutdown(self):
        """
        Прерывает основной цикл потока широковещательного протокола
        :return:
        """
        self.__shutdown = True


if __name__ == "__main__":
    devs = devices.DeviceList()
    devs.bind(test.cbs1, [devices.DevLstEvent.UPDATE_DEV,
                          devices.DevLstEvent.APPEND_DEV,
                          devices.DevLstEvent.REMOVE_DEV,
                          ])
    locator = Locator(devs)
    keyboard.add_hotkey("F12", locator.shutdown)
    locator_thr = threading.Thread(
        target=locator.run, name='locator.run() threading')
    locator_thr.start()

    locator_thr.join()
    for t in threading.enumerate():
        print(f'Thread Name: {t.name}')
