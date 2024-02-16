"""
Модуль определяет устройства, с которыми может работать утилита DSU
"""

import configparser
import socket
import threading
from enum import Enum, auto

import logic.eludp as eludp
import logic.locator as locator
import logic.cmd_queue as cmd_queue


class DevLstEvent(Enum):
    APPEND_DEV = 1
    REMOVE_DEV = auto()
    UPDATE_DEV = auto()
    POLL_RESPONSE = auto()
    CMD_RESPONSE = auto()
    CON_FAIL = auto()


# Модели устройств
DevModel = {
    0: "НЕИЗВ.",
    1: "CP-18",
    2: "POS",
    3: "AP-PRO",
    4: "TW-2020"
}

# Режим работы (ЗАГР./ОСН.)
DevBootMode = {
    0: "ЗАГР.",
    1: "ОСН.",
}


class Device(object):
    """
    Подключаемое устройство
    """
    WATCHDOG_TIMEOUT = 10

    def __init__(self, loc=None, el=None, data=b'', addr=None):
        """
        Устройство может задаваться набором основных параметров, полученных в ответ на широковещательный запрос,
        или парой (ip-адрес, порт), в этом случае набор параметров может быть опущен.

        Основные параметры (data) определяются следующей структурой языка Си:
        typedef struct
        {
            uint8_t     type;
            uint8_t     boot_mode;
            uint8_t     s_num[16];
            uint8_t     mac[6];
            uint16_t    fw;                    //  версия прошивки
            uint16_t    btldr;                 //  версия загрузчика
            uint16_t    pcb;                   //  версия платы
            char        name[16];              //  имя
            uint16_t    ip[2];                 //  IP-адрес контроллера
            uint16_t    mask[2];               //  маска подсети
            uint16_t    gateway[2];            //  IP-адрес шлюза
            uint16_t    host[2];               //  IP-адрес компьютера поддержки
            uint16_t    port;                  //  UDP-порт
            char        comment[64];           //  коментарий
        } Locator_Summary;

        :param loc:  интерфейс широковещательных команд
        :param el: интерфейс адресных команд
        :param data: массоив байт с основными параметрами устройства
        :param addr: (ip-адрес, порт) устройства для адресных команд
        """
        if len(data) != 128:
            data = bytes([0]*128)

        self.__dict = {}
        self.__update_dict = True

        self.__model = DevModel.get(data[0], 'НЕИЗВ.')
        self.__boot_mode = DevBootMode.get(data[1], '')
        if data[2:18] == bytes(16):
            self.__s_num = ''
        else:
            self.__s_num = data[17:1:-1].hex()
        if data[18:24] == bytes(6):
            self.__mac = ''
        else:
            self.__mac = data[18:24].hex(sep=':')
        if data[24:26] == bytes(6):
            self.__fw = ''
        else:
            self.__fw = '.'.join(map(str, (b for b in data[25:23:-1])))
        if data[26:28] == bytes(6):
            self.__btldr = ''
        else:
            self.__btldr = '.'.join(map(str, (b for b in data[27:25:-1])))
        if data[28:30] == bytes(6):
            self.__pcb = ''
        else:
            self.__pcb = '.'.join(map(str, (b for b in data[29:27:-1])))
        self.__name = self.str_from_bytes(data[30:46])
        if addr is None:
            self.__ip = self.ip_from_bytes(data[46:50])
            self.__port = int.from_bytes(data[62:64], byteorder='little')
        else:
            self.__ip = addr[0]
            self.__port = addr[1]
        self.__mask = self.ip_from_bytes(data[50:54])
        self.__gateway = self.ip_from_bytes(data[54:58])
        self.__host = self.ip_from_bytes(data[58:62])
        self.__comment = self.str_from_bytes(data[64:128])

        self.lst = None
        self.locator = loc
        self.el_udp = el
        self.queue = cmd_queue.CmdQueue(self)
        self.ai = None
        # Если ip-адрес контроллера находится в подсети одного из интерфейсов,
        # запоминаем этот интерфейс, что посылать команды только через него
        if self.locator is not None:
            for ai in self.locator.ai:
                if self.locator.subnet(ai['addr'], ai['netmask']) == self.locator.subnet(self.__ip, self.__mask):
                    self.ai = ai
        self.watchdog_timer = None

    @property
    def addr(self):
        return self.__ip, self.__port

    @property
    def s_num(self):
        return self.__s_num

    @property
    def dict(self):
        """
        Возвращает копию словаря атрибутов устройства

        'model' - модель устройства DevModel
        'boot_mod' - Режим работы DevBootMode
        'fw' - версия рошивки
        'btldr' - версия загрузчика
        'pcb' - версия печатной платы
        's_num' - серийный момер hex-строка 32 символа
        'mac' - MAC-адрес контроллера
        'name' - имя контроллера до 16 символов CP1251
        'ip' - IP-адрес контроллера
        'mask' - маска подсети
        'gateway' - шлюз
        'host' - IP-адрес хоста
        'port' - UDP-порт контроллера
        'comment' - крмментарий до 64 символов CP1251
        :return: копия словаря
        """
        if self.__update_dict:
            self.__dict['model'] = self.__model
            self.__dict['boot_mode'] = self.__boot_mode
            self.__dict['fw'] = self.__fw
            self.__dict['btldr'] = self.__btldr
            self.__dict['pcb'] = self.__pcb
            self.__dict['s_num'] = self.__s_num
            self.__dict['mac'] = self.__mac
            self.__dict['name'] = self.__name
            self.__dict['ip'] = self.__ip
            self.__dict['mask'] = self.__mask
            self.__dict['gateway'] = self.__gateway
            self.__dict['host'] = self.__host
            self.__dict['port'] = self.__port
            self.__dict['comment'] = self.__comment
            self.__update_dict = False
        return dict(self.__dict)

    def __str__(self):
        return f"\"{self.dict['name']}\" " \
               f"s/n={self.s_num}, " \
               f"IP={self.dict['ip']}, " \
               f"port={self.dict['port']}, " \
               f"MAC={self.dict['mac']}"

    def __eq__(self, other):
        """
        Два устройства считаются одинаковыми, если в словаре атрибутов все значения совпадают
        :param other: второе устройство
        :return:
        """
        if self.dict['s_num'] != '':
            return self.dict['s_num'] == other.dict['s_num']
        else:
            return self.dict['addr'] == other.dict['addr']

    def __ne__(self, other):
        """
        Два устройства считаются одинаковыми, если в словаре атрибутов все значения совпадают
        :param other: второе устройство
        :return:
        """
        return not self == other

    def update(self, dev):
        if isinstance(dev, Device):
            self.__model = dev.dict['model']
            self.__boot_mode = dev.dict['boot_mode']
            self.__fw = dev.dict['fw']
            self.__btldr = dev.dict['btldr']
            self.__pcb = dev.dict['pcb']
            self.__s_num = dev.dict['s_num']
            self.__mac = dev.dict['mac']
            self.__name = dev.dict['name']
            self.__ip = dev.dict['ip']
            self.__mask = dev.dict['mask']
            self.__gateway = dev.dict['gateway']
            self.__host = dev.dict['host']
            self.__port = dev.dict['port']
            self.__comment = dev.dict['comment']
            self.__update_dict = True
        elif isinstance(dev, dict):
            self.__model = dev['model']
            self.__boot_mode = dev['boot_mode']
            self.__fw = dev['fw']
            self.__btldr = dev['btldr']
            self.__pcb = dev['pcb']
            self.__s_num = dev['s_num']
            self.__mac = dev['mac']
            self.__name = dev['name']
            self.__ip = dev['ip']
            self.__mask = dev['mask']
            self.__gateway = dev['gateway']
            self.__host = dev['host']
            self.__port = dev['port']
            self.__comment = dev['comment']
            self.__update_dict = True

    def primary_settings_array(self, sttngs_dict=None):
        """
        Возвращает массив баыйтов с первичными настройками контроллера.
        При необходимости изменить настройки новые настройки передаются в виде словаря.
        :param sttngs_dict: Словарь с новыми настройаками контроллера.
        :return: массив байтов с настройками
        """
        if not isinstance(sttngs_dict, dict):
            sttngs_dict = {}
        ba = b''
        ba += self.str_to_bytes(sttngs_dict.get('name', self.dict['name']), 16)
        ba += self.ip_to_bytes(sttngs_dict.get('ip', self.dict['ip']))
        ba += self.ip_to_bytes(sttngs_dict.get('mask', self.dict['mask']))
        ba += self.ip_to_bytes(sttngs_dict.get('gateway',
                               self.dict['gateway']))
        ba += self.ip_to_bytes(sttngs_dict.get('host', self.dict['host']))
        ba += sttngs_dict.get('port',
                              self.dict['port']).to_bytes(2, byteorder='little')
        ba += self.str_to_bytes(sttngs_dict.get('comment',
                                self.dict['comment']), 64)
        return ba

    def restart_watchdog_timer(self, func):
        """
        Callback-функция, вызываемая при получении любого собщения от устройства
        Перезапускает сторожевой таймер
        :return:
        """
        if self.locator is None:
            return
        if self.watchdog_timer is not None:
            self.watchdog_timer.cancel()
        self.watchdog_timer = threading.Timer(interval=Device.WATCHDOG_TIMEOUT,
                                              function=func,
                                              args=(self,))
        self.watchdog_timer.name = f"Watchdog timer tread. Device {self.s_num} {self.dict['name']} {id(self)}"
        self.watchdog_timer.start()

    def send_pack(self, cmd=None, pack=b''):
        """
        Отправляет пакет устройству через заданный протокол
        :param cmd: команда (только для протокола Locator)
        :param pack: пакет данных, по умолчанию пустой
        :return:
        """
        if str(type(cmd)) == str(locator.LocatorCmd) and self.locator is not None:
            self.locator.send_pack(cmd, pack, self)
        elif self.el_udp is not None:
            self.el_udp.send_pack(self, pack)

    @staticmethod
    def str_from_bytes(ba):
        """
        Возвращает строку из массива байтов
        :param ba: массива байтов
        :return: строка в кодировке CP1251
        """
        if isinstance(ba, (bytes, bytearray)):
            l = ba.find(0)
            return (ba[:l] if l >= 0 else ba).decode('cp1251')
        else:
            return ""

    @staticmethod
    def ip_from_bytes(ba):
        """
        Возвращает строку с IP-адресом из массива байт
        :param ba: массив байтов с IP-адресом
        :return: строка с IP-адресом
        """
        if isinstance(ba, (bytes, bytearray)) and len(ba) == 4:
            return '.'.join(map(str, (b for b in ba)))
        else:
            return "0.0.0.0"

    @staticmethod
    def str_to_bytes(in_str, ba_len):
        """
        Возвращает массив байтов из строки. Остаток массива заполняет нулями
        :param in_str: строка в кодировке CP1251
        :param ba_len: длина масива байт
        :return: массив байтов
        """
        str_len = len(in_str)
        return bytes(in_str[:ba_len], encoding='cp1251') + (bytes(ba_len - str_len) if ba_len > str_len else b'')

    @staticmethod
    def ip_to_bytes(ip):
        """
        Возвращает массив байтов с IP-адресом из строки
        :param ip: строка с IP-адресом
        :return: массив байтов с IP-адресом
        """
        try:
            socket.inet_aton(ip)
            return bytes(map(int, ip.split('.')))
        except (socket.error, TypeError):
            return bytes(4)

    def set_primary_settings(self, d):
        self.send_pack(locator.LocatorCmd.SET_PRIMARY,
                       self.primary_settings_array(d))


class DeviceList(list):
    """
    Список подключенных устройств
    """

    def __init__(self):
        super().__init__()
        self.cbs = {}
        self.bind([])
        self.lock = threading.Lock()
        self.ini = configparser.ConfigParser(delimiters=(':',))
        self.read_ini()

    def __str__(self):
        s = ''
        for i, d in enumerate(self):
            s += str(i) + ': ' + str(d) + '\n'
        return s

    def remove(self, dev):
        """
        Переопределяет метод remove класса list
        Удаляет устройство из списка
        :param dev: устройство Device
        :return:
        """
        i = self.dev_index(dev)
        if i < 0 or i >= len(self):
            return

        super().pop(i)
        dev.lst = None
        if dev.watchdog_timer is not None:
            dev.watchdog_timer.cancel()
        self.cbs_handler(DevLstEvent.REMOVE_DEV, dev)

    def clear(self):
        """
        Переопределяет метод clear класса list
        Отписывает все callbak-функции и очищает список устройств
        :return:
        """
        for dev in self:
            dev.lst = None
            if dev.watchdog_timer is not None:
                dev.watchdog_timer.cancel()
        self.unbind()
        super().clear()

    def dev_index(self, dev):
        """
        Ищет устройство в списке и возвращает его индекс
        Если устройства нет возвращается индекс равный длине списка
        Если входные данные некорректны, возвращает -1
        :param dev: устройство
        :return: индекс устройства
        """
        if dev.s_num != '':
            for i in range(len(self)):
                if self[i].s_num == dev.s_num:
                    return i
        elif dev.dict['port'] == 0:
            return -1
        else:
            for i in range(len(self)):
                if self[i].addr == dev.addr:
                    return i
        return len(self)

    def append(self, dev):
        """
        Переопределяет метод append класса list
        Обрабатывает ответы на опрос контроллеров.
        Добавляет устройство в список если его еще нет, для существующих обновляет информацию.
        Уникальность устройства определяется его серийным номером.
        При этом пара (ip-адрес, порт) может у разных устройств совпадать.
        Для адресных устройств серийных номер может не использоваться, в этом случае номер может быть нулевым,
        а уникальность устройства определяется парой (ip-адрес, порт).
        :param dev: устройство Device
        :return:
        """
        if not isinstance(dev, Device):
            return
        if id(dev) in map(id, self):
            self.cbs_handler(DevLstEvent.POLL_RESPONSE, dev)
            return
        i = self.dev_index(dev)
        if i < 0:
            return
        self.lock.acquire()
        if i < len(self):
            if self[i].locator is not None:
                self[i].restart_watchdog_timer(self.connection_fail)
                self.cbs_handler(DevLstEvent.POLL_RESPONSE, self[i])
            if self[i].dict != dev.dict:
                self[i].update(dev)
                self.cbs_handler(DevLstEvent.UPDATE_DEV, self[i])
            self.lock.release()
            return
        super().append(dev)
        dev.lst = self
        dev.restart_watchdog_timer(self.connection_fail)
        self.cbs_handler(DevLstEvent.APPEND_DEV, dev)
        self.lock.release()

    def response_processing(self, header, pack):
        """
        Обработка ответов на команды кроме запроса REQUEST
        :param header: заголовок ответа в виде словаря
        :param pack: пакет с данными ответа
        :return:
        """
        dev = None
        for i in range(len(self)):
            if self[i].s_num == header['s_num']:
                dev = self[i]
                break
        if dev is None:
            return

        dev.restart_watchdog_timer(self.connection_fail)
        if header['cmd'] != locator.LocatorCmd.REQUEST:
            self.cbs_handler(DevLstEvent.CMD_RESPONSE, dev,
                             cmd=header['cmd'], pack=pack)

    def connection_fail(self, dev):
        """
        Callback-функция вызывается при срабатывании сторожевого таймера связи с устройством
        :param dev: устройство, с которым потеряна связь
        :return:
        """
        self.cbs_handler(DevLstEvent.CON_FAIL, dev)
        self.remove(dev)

    def bind(self, cbs=None, events=None):
        """
        Подписывает callback-функции к сбытиям списка устройств
        :param cbs: callback-функция или список функций
        :param events: событие или список событий, на которые подписывается функция, по умолчанию на все
        :return:
        """
        if events is None:
            events = list(DevLstEvent)
        elif isinstance(events, DevLstEvent):
            events = [events]
        for evnt in events:
            if evnt not in self.cbs.keys():
                self.cbs[evnt] = []
            elif isinstance(cbs, list):
                self.cbs[evnt] += cbs
            elif cbs is not None:
                self.cbs[evnt].append(cbs)

    def unbind(self, cbs=None, events=None):
        """
        Отписывает callback-функции от сбытий списка устройств
        :param cbs: callback-функция или список функций, если None, отписывает все функции
        :param events: событие или список событий, от которых отписывается функция, по умолчанию ото всех
        :return:
        """
        if events is None:
            events = list(DevLstEvent)
        elif isinstance(events, DevLstEvent):
            events = [events]
        for evnt in events:
            if evnt in self.cbs.keys():
                if cbs is None:
                    self.cbs[evnt].clear()
                    break
                if not isinstance(cbs, list):
                    cbs = [cbs]
                for c in cbs:
                    if c in self.cbs[evnt]:
                        self.cbs[evnt].remove(c)

    def cbs_handler(self, evnt, dev, **kwargs):
        """
        Запускает callback-функции
        :param evnt: событие списка устройств DevLstEvent
        :param dev: устройство
        :param kwargs: дополнительные параметры, которые могут быть переданы обработчику
        :return:
        """
        for cbs in self.cbs[evnt]:
            cbs(evnt, dev, **kwargs)

    def read_ini(self):
        try:
            self.ini.read('devices.ini')
            devs = self.ini.options('ELUDP')
            for opt in devs:
                dev = dict(list(s.strip().split('=') for s in map(
                    str, self.ini.get('ELUDP', opt).split(','))))
                if 'ip' not in dev.keys():
                    continue
                ip = dev['ip']
                port = int(dev.get('port', '1775'))
                self.append(Device(addr=(ip, port)))
        except (configparser.ParsingError, configparser.NoSectionError):
            pass
