"""
Современный интерфейс DSU на базе CustomTkinter
"""

import customtkinter as ctk
from loader import devs
import threading
import time
import datetime

from logic import locator
from logic import devices
from logic import eludp
from logic import firmware_go as firmware
from tkinter import filedialog, messagebox


# Настройка темы
ctk.set_appearance_mode("dark")  # dark, light, system
ctk.set_default_color_theme("blue")  # blue, green, dark-blue


class ModernDSU(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Настройка окна
        self.title("DSU - Device Setup Utility")
        self.geometry("1200x700")

        # Настройка сетки
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        self.selected_device = None

        # Создание боковой панели
        self.create_sidebar()

        # Создание основной области
        self.create_main_area()

        # Создание панели деталей устройства
        self.create_device_details()

        # Привязка событий
        self.bind_events()

        # Обновление списка устройств
        self.refresh_devices()

    def create_sidebar(self):
        """Боковая панель с кнопками действий"""
        self.sidebar = ctk.CTkFrame(self, width=200, corner_radius=0)
        self.sidebar.grid(row=0, column=0, sticky="nsew", padx=0, pady=0)
        self.sidebar.grid_rowconfigure(8, weight=1)

        # Логотип
        self.logo_label = ctk.CTkLabel(
            self.sidebar,
            text="DSU",
            font=ctk.CTkFont(size=32, weight="bold")
        )
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 10))

        self.version_label = ctk.CTkLabel(
            self.sidebar,
            text="Device Setup Utility v2.0",
            font=ctk.CTkFont(size=10)
        )
        self.version_label.grid(row=1, column=0, padx=20, pady=(0, 20))

        # Кнопки действий
        self.btn_refresh = ctk.CTkButton(
            self.sidebar,
            text="🔄 Обновить",
            command=self.refresh_devices
        )
        self.btn_refresh.grid(row=2, column=0, padx=20, pady=10)

        self.btn_add_test = ctk.CTkButton(
            self.sidebar,
            text="➕ Тестовое устройство",
            command=self.add_test_device
        )
        self.btn_add_test.grid(row=3, column=0, padx=20, pady=10)

        self.btn_firmware = ctk.CTkButton(
            self.sidebar,
            text="📦 Прошить устройство",
            command=self.load_firmware,
            state="disabled"
        )
        self.btn_firmware.grid(row=4, column=0, padx=20, pady=10)

        self.btn_reboot = ctk.CTkButton(
            self.sidebar,
            text="🔄 Перезагрузка",
            command=self.reboot_device,
            state="disabled"
        )
        self.btn_reboot.grid(row=5, column=0, padx=20, pady=10)

        self.btn_settings = ctk.CTkButton(
            self.sidebar,
            text="⚙️ Применить настройки",
            command=self.apply_settings,
            state="disabled"
        )
        self.btn_settings.grid(row=6, column=0, padx=20, pady=10)

        # Переключатель темы
        self.theme_label = ctk.CTkLabel(self.sidebar, text="Тема:")
        self.theme_label.grid(row=9, column=0, padx=20, pady=(10, 0))

        self.theme_switch = ctk.CTkSwitch(
            self.sidebar,
            text="Темная",
            command=self.change_theme,
            onvalue="dark",
            offvalue="light"
        )
        self.theme_switch.grid(row=10, column=0, padx=20, pady=(0, 20))
        self.theme_switch.select()

    def create_main_area(self):
        """Основная область со списком устройств"""
        self.main_frame = ctk.CTkFrame(self)
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=10, pady=10)
        self.main_frame.grid_rowconfigure(1, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

        # Заголовок
        self.header_label = ctk.CTkLabel(
            self.main_frame,
            text="Обнаруженные устройства",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        self.header_label.grid(row=0, column=0, padx=20, pady=10, sticky="w")

        # Scrollable frame для устройств
        self.devices_frame = ctk.CTkScrollableFrame(
            self.main_frame,
            label_text="Устройства в сети"
        )
        self.devices_frame.grid(row=1, column=0, padx=20, pady=10, sticky="nsew")
        self.devices_frame.grid_columnconfigure(0, weight=1)

        # Счетчик устройств
        self.device_count_label = ctk.CTkLabel(
            self.main_frame,
            text="Устройств: 0",
            font=ctk.CTkFont(size=12)
        )
        self.device_count_label.grid(row=2, column=0, padx=20, pady=5, sticky="w")

    def create_device_details(self):
        """Панель с деталями выбранного устройства"""
        self.details_frame = ctk.CTkFrame(self)
        self.details_frame.grid(row=0, column=2, sticky="nsew", padx=(0, 10), pady=10)
        self.details_frame.grid_columnconfigure(1, weight=1)

        # Заголовок
        self.details_header = ctk.CTkLabel(
            self.details_frame,
            text="Детали устройства",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        self.details_header.grid(row=0, column=0, columnspan=2, padx=20, pady=15)

        # Поля для отображения/редактирования
        self.detail_fields = {}
        fields = [
            ("Модель:", "model", False),
            ("Сер. номер:", "s_num", False),
            ("MAC-адрес:", "mac", False),
            ("Прошивка:", "fw", False),
            ("Загрузчик:", "btldr", False),
            ("Плата:", "pcb", False),
            ("Имя:", "name", True),
            ("IP-адрес:", "ip", True),
            ("Маска:", "mask", True),
            ("Шлюз:", "gateway", True),
            ("Хост:", "host", True),
            ("Порт:", "port", True),
            ("Комментарий:", "comment", True),
        ]

        for idx, (label, key, editable) in enumerate(fields):
            lbl = ctk.CTkLabel(self.details_frame, text=label)
            lbl.grid(row=idx+1, column=0, padx=10, pady=5, sticky="e")

            if editable:
                entry = ctk.CTkEntry(self.details_frame, width=200)
                entry.grid(row=idx+1, column=1, padx=10, pady=5, sticky="ew")
                self.detail_fields[key] = entry
            else:
                value_label = ctk.CTkLabel(self.details_frame, text="-")
                value_label.grid(row=idx+1, column=1, padx=10, pady=5, sticky="w")
                self.detail_fields[key] = value_label

    def create_device_card(self, device, index):
        """Создает карточку устройства"""
        card = ctk.CTkFrame(self.devices_frame)
        card.grid(row=index, column=0, padx=5, pady=5, sticky="ew")
        card.grid_columnconfigure(1, weight=1)

        # Иконка статуса
        status_icon = "🟢" if device.dict['boot_mode'] == "ОСН." else "🟡"
        icon_label = ctk.CTkLabel(card, text=status_icon, font=ctk.CTkFont(size=20))
        icon_label.grid(row=0, column=0, rowspan=2, padx=10, pady=10)

        # Информация
        name_text = f"{device.dict['name']} ({device.dict['model']})"
        name_label = ctk.CTkLabel(
            card,
            text=name_text,
            font=ctk.CTkFont(size=14, weight="bold")
        )
        name_label.grid(row=0, column=1, padx=5, pady=(5, 0), sticky="w")

        info_text = f"IP: {device.dict['ip']} | FW: {device.dict['fw']}"
        info_label = ctk.CTkLabel(card, text=info_text, font=ctk.CTkFont(size=11))
        info_label.grid(row=1, column=1, padx=5, pady=(0, 5), sticky="w")

        # Кнопка выбора
        select_btn = ctk.CTkButton(
            card,
            text="Выбрать",
            width=80,
            command=lambda d=device: self.select_device(d)
        )
        select_btn.grid(row=0, column=2, rowspan=2, padx=10, pady=10)

        return card

    def refresh_devices(self):
        """Обновляет список устройств"""
        # Очищаем текущий список
        for widget in self.devices_frame.winfo_children():
            widget.destroy()

        # Добавляем устройства
        for idx, device in enumerate(devs):
            self.create_device_card(device, idx)

        # Обновляем счетчик
        self.device_count_label.configure(text=f"Устройств: {len(devs)}")

    def select_device(self, device):
        """Выбор устройства для работы"""
        self.selected_device = device

        # Заполняем поля
        for key, widget in self.detail_fields.items():
            if isinstance(widget, ctk.CTkEntry):
                widget.delete(0, "end")
                widget.insert(0, str(device.dict[key]))
            else:
                widget.configure(text=str(device.dict[key]))

        # Активируем кнопки
        self.btn_firmware.configure(state="normal")
        self.btn_reboot.configure(state="normal")
        self.btn_settings.configure(state="normal")

    def add_test_device(self):
        """Добавляет тестовое устройство"""
        from test_module import test

        for i in range(10):
            dev = test.test_dev(i)
            if devs.dev_index(dev) >= len(devs):
                devs.append(dev)
                self.refresh_devices()
                self.show_info("Успех", f"Добавлено тестовое устройство #{i}")
                return

        self.show_warning("Внимание", "Все тестовые устройства уже добавлены")

    def load_firmware(self):
        """Загрузка прошивки на устройство"""
        if not self.selected_device:
            self.show_warning("Ошибка", "Выберите устройство")
            return

        file_path = filedialog.askopenfilename(
            title="Выберите файл прошивки",
            filetypes=[("Firmware files", "*.fw"), ("All files", "*.*")]
        )

        if not file_path:
            return

        # Показываем прогресс
        self.show_progress_window(file_path)

    def show_progress_window(self, fw_path):
        """Окно прогресса прошивки"""
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Прошивка устройства")
        progress_window.geometry("400x200")
        progress_window.grab_set()

        label = ctk.CTkLabel(
            progress_window,
            text=f"Прошивка {self.selected_device.dict['name']}...",
            font=ctk.CTkFont(size=14)
        )
        label.pack(pady=20)

        progress = ctk.CTkProgressBar(progress_window, width=300)
        progress.pack(pady=20)
        progress.set(0)

        percent_label = ctk.CTkLabel(progress_window, text="0%")
        percent_label.pack(pady=10)

        def update_progress():
            self.selected_device.queue.append(
                locator.LocatorCmd.EXE_EL_CMD,
                pack=eludp.ElCmd.RUN_BTLDR.value,
                pause=10
            )
            self.selected_device.queue.append(
                locator.LocatorCmd.EXE_EL_CMD,
                gen=firmware.Firmware(fw_path)
            )
            self.selected_device.queue.append(
                locator.LocatorCmd.EXE_EL_CMD,
                pack=eludp.ElCmd.RUN_MAIN.value
            )
            self.selected_device.queue.run()

            while True:
                prog = self.selected_device.queue.progress()
                progress.set(prog / 100)
                percent_label.configure(text=f"{prog}%")

                if prog >= 100:
                    time.sleep(0.5)
                    progress_window.destroy()
                    self.show_info("Успех", "Прошивка завершена!")
                    break

                time.sleep(0.1)

        threading.Thread(target=update_progress, daemon=True).start()

    def reboot_device(self):
        """Перезагрузка устройства"""
        if not self.selected_device:
            return

        if messagebox.askyesno("Подтверждение",
                              f"Перезагрузить {self.selected_device.dict['name']}?"):
            self.selected_device.queue.append(
                locator.LocatorCmd.EXE_EL_CMD,
                pack=b'\x02'
            )
            self.selected_device.queue.run()
            self.show_info("Успех", "Команда перезагрузки отправлена")

    def apply_settings(self):
        """Применение настроек к устройству"""
        if not self.selected_device:
            return

        # Собираем настройки из полей
        settings = {}
        for key in ['name', 'ip', 'mask', 'gateway', 'host', 'port', 'comment']:
            if key in self.detail_fields:
                value = self.detail_fields[key].get()
                if key == 'port':
                    value = int(value)
                settings[key] = value

        self.selected_device.queue.append(
            locator.LocatorCmd.SET_PRIMARY,
            pack=self.selected_device.primary_settings_array(settings)
        )
        self.selected_device.queue.run()

        if messagebox.askyesno("Настройки применены",
                              "Перезагрузить устройство для применения?"):
            self.reboot_device()

    def change_theme(self):
        """Смена темы интерфейса"""
        if self.theme_switch.get() == "dark":
            ctk.set_appearance_mode("dark")
        else:
            ctk.set_appearance_mode("light")

    def bind_events(self):
        """Привязка событий обновления списка"""
        devs.bind(lambda *args, **kwargs: self.after(100, self.refresh_devices),
                 [devices.DevLstEvent.APPEND_DEV,
                  devices.DevLstEvent.REMOVE_DEV,
                  devices.DevLstEvent.UPDATE_DEV])

    def show_info(self, title, message):
        """Информационное сообщение"""
        messagebox.showinfo(title, message)

    def show_warning(self, title, message):
        """Предупреждение"""
        messagebox.showwarning(title, message)


def main():
    app = ModernDSU()
    app.mainloop()


if __name__ == "__main__":
    main()
