import threading
from enum import Enum, auto
import time

import logic.devices as devices
import keyboard
import logic.locator as locator
import logic.eludp as eludp
import test_module.test as test


class QueueResult(Enum):
    """
    Результаты выполнения очереди команд
    """
    OK = auto()
    FAIL = auto()
    TIMEOUT = auto()


class CmdQueue(list):
    """
    Очередь команд контроллеру
    """

    MAX_ATTEMPT_NUM = 3  # Максимальное количество попыток передать команду

    def __init__(self, dev, cbs=None, timeout=2):
        """
        Инициализация очереди
        :param dev: устройство, которому принадлежит очередь
        :param cbs: callback-функция
        :param timeout: таймаут по умодчанию (у каждой команды может быть свой таймаут)
        """
        super().__init__()
        self.__shutdown = False
        self.__response_received = False
        self.__fail = False
        self.__timeout = False
        self.__progress = 0
        if isinstance(dev, devices.Device):
            self.dev = dev
        self.cbs = cbs
        self.default_timeout = timeout
        self.queue_thr = None
        self.response_timer = None
        self.attempt_num = 0
        self.current_cmd = None

        self.cnt = 0
        self.prev_gen_cnt = 0

    def append(self, code, pack=b'', gen=None, timeout=None, pause=0, cbs=None):
        """
        Переопределяет метод append класса list. Добавляет команду в очередь
        Команда не может быть добавлена, если в данный момент очередь исполняется
        :param code: код команды. Для протокола locator - LocatorCmd, для eludp - None
        :param pack: пакет с данными команды
        :param gen: генератор длинных очередей команд
        :param timeout: таймаут выполнения команды, по умолчанию присваивается self.default_timeout
        :param pause: пауза после выполнения команды.
        :param cbs: callback-функция команды, в нее передается ответ контроллера при успешном выполнении команды
               Должна принимать следующие аргументы:
               result: QueueResult (обязательный аргумент)
               **kwargs  (необязательные именованные аргументы)
                    'pack' - пакет с данными
                    'cmd_result' - (result, error_code) короткий ответ "результат выполнения команды"
        :return:
        """
        if 0 < self.__progress < 100:
            return
        if timeout is None:
            timeout = self.default_timeout
        super().append({'code': code, 'pack': pack, 'gen': gen,
                        'timeout': timeout, 'pause': pause, 'cbs': cbs})

    def progress(self):
        """
        Возвращает прогресс очереди в процентах
        Если прогресс равен 100%, значение сбрасывается сразу после чтения
        :return: прогресс
        """
        progress = self.__progress
        if progress == 100:
            self.__progress = 0
        return progress

    def timeout(self):
        """
        Вызывается по завершению таймаута ожидания ответа на команду
        Если количество попыток исполнить команду не превышает MAX_ATTEMPT_NUM, команда повторяется
        :return:
        """
        self.attempt_num += 1
        if self.attempt_num >= CmdQueue.MAX_ATTEMPT_NUM:
            self.__timeout = True
            if self.current_cmd['cbs'] is not None:
                self.current_cmd['cbs'](QueueResult.TIMEOUT)
        else:
            self.response_timer = threading.Timer(interval=self.current_cmd['timeout'],
                                                  function=self.timeout)
            self.response_timer.name = 'Response timer thread'
            self.response_timer.start()
            self.dev.send_pack(
                self.current_cmd['code'], self.current_cmd['pack'])

    def calc_progress(self):
        if self.__progress == 1:
            self.__progress = 2

        gen_num = 0
        progress = 0
        for cmd in self:
            if cmd['gen'] is not None:
                gen_num += 1
                break
        if gen_num == 0:
            progress = int(100 * (self.index(self.current_cmd) / len(self)))
        else:
            if self.current_cmd['gen'] is None:
                progress += 1
            else:
                gen_weight = (97 - len(self) + gen_num) // gen_num
                progress += gen_weight * \
                    self.current_cmd['gen'].progress() // 100
        self.__progress = progress if progress > 2 else 2

    def queue_process(self):
        """
        Цикл отправки очереди команд
        :return:
        """
        def cmd_process():
            nonlocal self
            self.__response_received = self.__fail = self.__timeout = False
            self.attempt_num = 0
            self.response_timer = threading.Timer(interval=self.current_cmd['timeout'],
                                                  function=self.timeout)
            self.response_timer.name = 'Response timer thread'
            self.response_timer.start()
            while not self.__shutdown \
                    and not self.__response_received \
                    and not self.__fail \
                    and not self.__timeout:
                pass
            if self.__shutdown:
                print('Завершение работы')
                self.response_timer.cancel()
                self.__progress = 0
                return False
            if self.__timeout:
                print(f"Таймаут исполнения команды {self.current_cmd['code']}")
                self.cbs(QueueResult.TIMEOUT)
                self.__progress = 0
                return False
            if self.__fail:
                print(f"Ошибка исполнения команды {self.current_cmd['code']}")
                self.response_timer.cancel()
                self.cbs(QueueResult.FAIL)
                self.__progress = 0
                return False
            self.response_timer.cancel()
            self.calc_progress()
            return True

        self.__progress = 1
        for self.current_cmd in self:
            if self.current_cmd['gen'] is None:
                self.dev.send_pack(
                    self.current_cmd['code'], self.current_cmd['pack'])
                if not cmd_process():
                    break
                time.sleep(self.current_cmd['pause'])
            else:
                break_queue = False
                for cmd_pack in self.current_cmd['gen']():
                    self.current_cmd['pack'] = cmd_pack
                    self.dev.send_pack(self.current_cmd['code'], cmd_pack)
                    if not cmd_process():
                        break_queue = True
                        break
                if break_queue:
                    break
                time.sleep(self.current_cmd['pause'])
        else:
            self.__progress = 100
            if self.cbs is not None:
                self.cbs(QueueResult.OK)
        self.dev.lst.unbind(self.response_processing)
        self.clear()

    def run(self):
        """
        Запуск очереди команд
        Очередь запускается в отдельном потоке
        :return:
        """
        self.dev.lst.bind(self.response_processing,
                          devices.DevLstEvent.CMD_RESPONSE)
        self.queue_thr = threading.Thread(target=self.queue_process,
                                          name=f"Command queue thread of {self.dev.dict['s_num']}")
        self.queue_thr.start()

    def stop(self):
        """
        Остановка исполнения очереди команд
        :return:
        """
        self.__shutdown = True
        self.queue_thr.join()
        self.clear()

    def response_processing(self, event, dev, **kwargs):
        """
        Обработчик ответа на команду
        Вызывается по событию DevLstEvent.CMD_RESPONSE (получен ответ на команду)
        :param event: Событие списка устройств
        :param dev: Устройство, вызвывшее событие
        :param kwargs: Набор именованных аргументов
                       должны присутствовать аргумнты с именами
                       'cmd' - команда, на которую пришел ответ
                       'pack' - пакет данных, структура зависит от команды
        :return:
        """
        if self.current_cmd['gen'] is not None:
            if self.current_cmd['gen'].cnt - self.prev_gen_cnt > 1:
                print(
                    f" > 1 ({self.current_cmd['gen'].cnt - self.prev_gen_cnt})")
            self.prev_gen_cnt = self.current_cmd['gen'].cnt
        if event != devices.DevLstEvent.CMD_RESPONSE:
            return
        if self.dev != dev:
            print("Device doesn`t match")
            return
        if 'cmd' not in kwargs.keys():
            return
        if kwargs['cmd'] != self.current_cmd['code']:
            print("Cmd doesn`t match", kwargs['cmd'], self.current_cmd['code'])
            return
        pack = kwargs['pack']
        result = None
        self.cnt += 1
        if kwargs['cmd'] == locator.LocatorCmd.SET_PRIMARY or \
           kwargs['cmd'] == locator.LocatorCmd.EXE_EL_CMD or \
           kwargs['cmd'] == locator.LocatorCmd.CLEAR_LOG:
            result = self.cmd_result(pack)
        elif kwargs['cmd'] == locator.LocatorCmd.READ_SETTINGS:
            if len(pack) <= 2 and pack[0] in [res.value for res in locator.LocatorResult]:
                result = self.cmd_result(pack)
            else:
                self.__response_received = True
        elif (kwargs['cmd'] == locator.LocatorCmd.READ_MEM_PROP or
              kwargs['cmd'] == locator.LocatorCmd.READ_MEM_DUMP or
              kwargs['cmd'] == locator.LocatorCmd.GET_MAP or
              kwargs['cmd'] == locator.LocatorCmd.GET_LOG or
              kwargs['cmd'] == locator.LocatorCmd.CLEAR_LOG or
              kwargs['cmd'] == locator.LocatorCmd.SET_USER or
              kwargs['cmd'] == locator.LocatorCmd.GET_USER):
            __response_received = True
        if self.current_cmd['cbs'] is not None:
            if self.__response_received:
                if result is None:
                    self.current_cmd['cbs'](QueueResult.OK, pack=pack)
                else:
                    self.current_cmd['cbs'](QueueResult.OK, result=result)
            elif self.__fail:
                self.current_cmd['cbs'](QueueResult.FAIL, result=result)

    def cmd_result(self, pack):
        """
        Обработка простого ответа "Результат выполнения команды"
        :param pack:
        :return:
        """
        result = locator.LocatorResult(pack[0])
        error_code = locator.LocatorErrorCode.DEFAULT if len(pack) < 2 or result == locator.LocatorResult.OK \
            else locator.LocatorErrorCode(pack[1])
        self.__response_received = (result == locator.LocatorResult.OK)
        self.__fail = not self.__response_received
        return result, error_code


def run_queue():
    dev = test.get_queue_test_device(devs)
    test.run_queue(dev)


if __name__ == "__main__":
    devs = devices.DeviceList()
    devs.bind(test.cbs1, [devices.DevLstEvent.UPDATE_DEV,
                          devices.DevLstEvent.APPEND_DEV,
                          devices.DevLstEvent.REMOVE_DEV,
                          ])
    lctr = locator.Locator(devs)
    keyboard.add_hotkey("F12", lctr.shutdown)
    keyboard.add_hotkey("F11", run_queue)

    for i in range(10):
        keyboard.add_hotkey(
            f"Ctrl+{i}", test.append_remove_device, args=(i, devs))

    lctr_thr = threading.Thread(
        target=lctr.run, name='locator.run() threading')
    lctr_thr.start()

    lctr_thr.join()
