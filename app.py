from loader import devs, lctr, lctr_thr

import logic
import config
import interface
import test_module

import keyboard
import threading

from logic import devices
from test_module import test
from interface.tk_int_dsu import MyFrame
from test_module import test


if __name__ == "__main__":
    lctr_thr.start()

    frame = MyFrame()
    devs.bind(frame.get_devs, [devices.DevLstEvent.APPEND_DEV,
                               devices.DevLstEvent.REMOVE_DEV,
                               devices.DevLstEvent.UPDATE_DEV,
                               ])
    devs.bind(frame.get_time, [devices.DevLstEvent.CMD_RESPONSE])
    frame.win.mainloop()

    lctr.shutdown()

    lctr_thr.join()
