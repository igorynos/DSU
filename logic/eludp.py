import socket
from enum import Enum

import keyboard
import threading
import logic.devices as devices


class ElCmd(Enum):
    SET_ADDR = b'\x01'  # Установка адреса контроллера
    RESTART = b'\x02'  # Перезагрузить контроллер
    FW_INFO = b'\x03'  # Запись информации о прошивке
    FW_PACK = b'\x04'  # Загрузка фрагмента файла прошивки
    RUN_MAIN = b'\x05'  # Перейти к выполнению основной программы
    RUN_BTLDR = b'\x06'  # Перейти в режим загрузчика


class ElUdp(object):
    """ Адресный протокл обмена с устройствами """

    def __init__(self):
        self.__shutdown = False
        self.buff_size = 1024

        # Сокеты представлены в виде словаря:
        #   ключ - port
        #   значение - кортеж (socket, thread)
        self.sockets = {}

        # Устройства представлены в виде словаря:
        #   ключ - кортеж (ip-адрес, port)
        #   значение - кортеж (socket,
        #                      список callback-функций [cbs]
        #                      )
        self.devices = {}

    def close(self):
        for s in self.sockets.values():
            s[0].close()
        self.sockets.clear()
        self.devices.clear()

    def bind(self, dev, cbs):
        """
        Подписывает callback-функцию на ответы от устройства
        :param dev: устройство Device
        :param cbs: callback-функция
        :return:
        """
        if not isinstance(dev, devices.Device):
            return

        if dev.addr in self.devices.keys():
            if cbs in self.devices[dev.addr][1]:
                return
            else:
                self.devices[dev.addr][1].append(cbs)
        else:
            self.devices[dev.addr] = [None, [cbs]]

        if dev.dict['port'] not in self.sockets:
            # Если у добавленного устройства новый порт, начинаем его прослушивать
            self.sockets[dev.addr[1]] = (socket.socket(socket.AF_INET, socket.SOCK_DGRAM),
                                         threading.Thread(target=self.listening_port,
                                                          args=(dev.addr[1],),
                                                          name=f'Listening port {dev.addr[1]}'))
            self.sockets[dev.addr[1]][0].bind(('', dev.addr[1]))
            self.sockets[dev.addr[1]][0].settimeout(0.1)
            self.sockets[dev.addr[1]][1].start()
        # присваиваиваем устройству сокет
        self.devices[dev.addr][0] = self.sockets[dev.addr[1]][0]

    def listening_port(self, port):
        """
        Прослушивает заданный порт
        При приеме пакета от устройства из devices вызывает все подписанные callback-функции
        :param port:
        :return:
        """
        while not self.__shutdown:
            try:
                data, addr = self.sockets[port][0].recvfrom(self.buff_size)
                for dev_addr in self.devices.keys():
                    if dev_addr == addr:
                        for func in self.devices[dev_addr][1]:
                            func(data)
            except TimeoutError:
                continue
        self.sockets[port][0].close()

    def unbind(self, dev, cbs=None):
        """
        Отписывает заданную callback-функцию от ответов от устройства
        Если callback-функция None, отписываются все callback-функции
        :param dev: устройство Device
        :param cbs: callback-функция
        :return:
        """
        if not isinstance(dev, devices.Device):
            return

        if dev.addr in self.devices.keys():
            if cbs is None:
                self.devices.pop(dev.addr)
            else:
                if cbs not in self.devices[dev]:
                    return
                self.devices[dev].remove(cbs)
                if len(self.devices[dev.addr]) == 0:
                    self.devices.pop(dev.addr)

        # Проверяем: остались ли устройства с тем же портом, если нет, удаляем порт из списка прослушивания
        for dev_addr in self.devices.keys():
            if dev_addr[1] == dev.addr[1]:
                return
        self.sockets[dev.addr[1]].close()
        self.sockets.pop(dev.addr[1])

    def send_pack(self, dev, pack):
        """
        Отправляет пакет на устройство

        :param dev: устройство Device
        :param pack: передаваемый пакет
        :return:
        """
        if not isinstance(dev, devices.Device):
            return

        self.devices[dev.addr][0].sendto(pack, dev.addr)

    def run(self):
        """
        Основной цикл потока адресного протокола
        :return:
        """
        while not self.__shutdown:
            pass
        for s in self.sockets.values():
            s[1].join()
        self.sockets.clear()
        self.devices.clear()

    def shutdown(self):
        """
        Прерывает основной цикл потока адресного протокола
        :return:
        """
        self.__shutdown = True


def cbs1(data):
    print(data)


if __name__ == "__main__":
    el_udp = ElUdp()
    keyboard.add_hotkey("F12", el_udp.shutdown)
    el_thr = threading.Thread(target=el_udp.run, name='el_udp.run() threading')
    el_thr.start()

    dev1 = devices.Device(addr=('192.168.0.120', 1775))
    el_udp.bind(dev1, cbs1)
    el_udp.send_pack(dev1, bytes(
        [0x00, 0x1d, 0x00, 0x00, 0x3f, 0xef, 0xba, 0x35]))
