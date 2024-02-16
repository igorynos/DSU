import logic

import keyboard
import threading

from logic import devices
from test_module import test


devs = devices.DeviceList()
devs.bind(test.cbs1, [devices.DevLstEvent.UPDATE_DEV,
                      devices.DevLstEvent.APPEND_DEV,
                      devices.DevLstEvent.REMOVE_DEV,
                      ])
lctr = logic.locator.Locator(devs)
for i in range(10):
    keyboard.add_hotkey(
        f"Ctrl+{i}", test.append_remove_device, args=(i, devs))
keyboard.add_hotkey("F11", print, args=(devs,))
lctr_thr = threading.Thread(
    target=lctr.run, name='locator.run() threading')
