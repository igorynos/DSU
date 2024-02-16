import threading

from logic import cmd_queue as cmd_queue
from logic import devices as devices
import keyboard
from logic import locator as locator


def cbs1(evnt, dev, **kwargs: object):
    dev_str = f"\"{dev.dict['name']}\" s/n={dev.s_num}, IP={dev.dict['ip']}, MAC={dev.dict['mac']}"
    if evnt == devices.DevLstEvent.UPDATE_DEV:
        print(f"Update device {dev_str}")
    if evnt == devices.DevLstEvent.APPEND_DEV:
        print(f"Append device {dev_str}")
    if evnt == devices.DevLstEvent.REMOVE_DEV:
        print(f"Remove device {dev_str}")


def test_dev(n):
    if n < 0 or n > 9:
        return
    ba = b'\x02'
    ba += b'\x01'
    ba += n.to_bytes(1, byteorder='little') + \
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ba += b'\x1e0l\x00\x00' + n.to_bytes(1, byteorder='little')
    ba += b'\x00\x03'
    ba += b'\x00\x03'
    ba += b'\x00\x02'
    ba += b'Test ' + bytes(str(n), encoding='cp1251') + \
        b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ba += b'\xc0\xa8\x00' + (100 + n).to_bytes(1, byteorder='little')
    ba += b'\xff\xff\xff\x00'
    ba += b'\x00\x00\x00\x00'
    ba += b'\x00\x00\x00\x00'
    ba += b'\xef\x06'
    ba += b'Comment\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ba += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ba += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    ba += b'\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00\x00'
    return devices.Device(data=ba)


def append_remove_device(n, devs):
    dev = test_dev(n)
    if 0 <= devs.dev_index(dev) < len(devs):
        devs.remove(dev)
    else:
        devs.append(dev)


def queue_result(result):
    print(f'Результат выполнения очереди команд: {result}')


def print_time(result, pack):
    if result == cmd_queue.QueueResult.OK:
        print(
            f"{2000 + pack[8]}.{pack[7]:02}.{pack[6]:02} {pack[5]:02}:{pack[4]:02}:{pack[3]:02}\n")


def get_queue_test_device(devs):
    if not isinstance(devs, devices.DeviceList):
        return
    for d in devs:
        # if d.dict['name'].find('Queue test') >= 0:
        if d.dict['ip'] == '192.168.0.103':
            return d
    else:
        return None


def run_queue(dev):
    """
    Функция тестирования очереди команд
    Получает устройствл с именем "Queue test XX" и помещает в очередь три команды:
    1) записывает основные параметры с измененным именм, где номер увеличен на 1,
    2) записывает основные параметры с коментарием с тем же номером,
    3) запрашивает время на устройстве
    :param dev: тестовое устройство (должно иметь имя "Queue test XX")
    :return:
    """

    num = dev.dict['name'].replace('Queue test', '').strip()
    print(num)
    if num == '':
        num = 0
    else:
        try:
            num = int(num)
        except ValueError:
            num = 0
    num += 1
    print(num)

    dev.queue.cbs = queue_result
    print("Начало формирования очереди")
    dev_dict = dev.dict
    dev_dict['name'] = f'Queue test {num}'
    dev.queue.append(locator.LocatorCmd.SET_PRIMARY,
                     pack=d.primary_settings_array(dev_dict))
    dev_dict['comment'] = f'Comment {num}'
    dev.queue.append(locator.LocatorCmd.SET_PRIMARY,
                     pack=d.primary_settings_array(dev_dict))
    dev.queue.append(locator.LocatorCmd.READ_SETTINGS,
                     pack=b'\x20', cbs=print_time)
    print(f'Запуск очереди')
    dev.queue.run()


def get_dev_time(evnt, dev, **kwargs):
    if 'pack' not in kwargs.keys():
        return

    ba = kwargs['pack']
    print(ba)
    devs.unbind(get_dev_time, devices.DevLstEvent.CMD_RESPONSE)


def req_time(devs):
    devs[0].send_pack(locator.LocatorCmd.READ_SETTINGS, pack=b'\x20')
    devs.bind(get_dev_time, devices.DevLstEvent.CMD_RESPONSE)


if __name__ == "__main__":
    devs = devices.DeviceList()
    devs.bind(cbs1, [devices.DevLstEvent.UPDATE_DEV,
                     devices.DevLstEvent.APPEND_DEV,
                     devices.DevLstEvent.REMOVE_DEV,
                     ])
    lctr = locator.Locator(devs)
    keyboard.add_hotkey("F12", lctr.shutdown)
    keyboard.add_hotkey("F11", req_time, args=(devs,))
    for i in range(10):
        keyboard.add_hotkey(f"Ctrl+{i}", append_remove_device, args=(i, devs))

    lctr_thr = threading.Thread(
        target=lctr.run, name='locator.run() threading')
    lctr_thr.start()

    lctr_thr.join()
