#!/usr/bin/env python3
"""
DSU - Device Setup Utility
Современная версия с CustomTkinter
"""

from loader import devs, lctr, lctr_thr
from interface.modern_ui import ModernDSU

if __name__ == "__main__":
    # Запускаем поток locator
    lctr_thr.start()

    # Создаем и запускаем GUI
    app = ModernDSU()
    app.mainloop()

    # Завершаем работу
    lctr.shutdown()
    lctr_thr.join()
