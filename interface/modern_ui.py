"""
Современный интерфейс DSU на базе CustomTkinter
Горизонтальная ориентация с широкой таблицей
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
import tkinter as tk


# Настройка темы
ctk.set_appearance_mode("dark")  # dark, light, system
ctk.set_default_color_theme("blue")  # blue, green, dark-blue


class ModernDSU(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Настройка окна
        self.title("DSU - Device Setup Utility v2.0")
        self.geometry("1400x800")
        self.minsize(1200, 600)

        # Настройка сетки
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)  # Таблица расширяется

        self.selected_device = None

        # Создание меню
        self.create_menu()

        # Создание toolbar
        self.create_toolbar()

        # Создание таблицы устройств (горизонтальная)
        self.create_device_table()

        # Создание панели деталей внизу
        self.create_details_panel()

        # Статус бар
        self.create_statusbar()

        # Привязка событий
        self.bind_events()

        # Обновление списка устройств
        self.refresh_devices()

    def create_menu(self):
        """Создание меню"""
        menubar = tk.Menu(self)
        self.config(menu=menubar)

        # Файл
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Файл", menu=file_menu)
        file_menu.add_command(label="Обновить список", command=self.refresh_devices)
        file_menu.add_separator()
        file_menu.add_command(label="Выход", command=self.quit)

        # Инструменты
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Инструменты", menu=tools_menu)

        # Команды
        commands_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Команды", menu=commands_menu)
        commands_menu.add_command(label="Перезагрузить контроллер", command=self.reboot_device)
        commands_menu.add_command(label="Перейти в режим загрузчика", command=self.goto_bootloader)
        commands_menu.add_command(label="Перейти в рабочий режим", command=self.goto_normal_mode)

        # Тестовые устройства
        test_menu = tk.Menu(tools_menu, tearoff=0)
        tools_menu.add_cascade(label="Тестовые устройства", menu=test_menu)
        test_menu.add_command(label="Добавить 1 устройство", command=self.add_test_device)
        test_menu.add_command(label="Добавить 5 устройств", command=lambda: self.add_multiple_test_devices(5))
        test_menu.add_command(label="Добавить 10 устройств", command=lambda: self.add_multiple_test_devices(10))

        # Вид
        view_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Вид", menu=view_menu)
        view_menu.add_command(label="Темная тема", command=lambda: self.change_theme("dark"))
        view_menu.add_command(label="Светлая тема", command=lambda: self.change_theme("light"))
        view_menu.add_command(label="Системная тема", command=lambda: self.change_theme("system"))

        # Помощь
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Справка", menu=help_menu)
        help_menu.add_command(label="О программе", command=self.show_about)

    def create_toolbar(self):
        """Создание toolbar"""
        toolbar = ctk.CTkFrame(self, height=50, corner_radius=0)
        toolbar.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        toolbar.grid_columnconfigure(3, weight=1)

        # Кнопки
        self.btn_refresh = ctk.CTkButton(
            toolbar, text="🔄 Обновить", width=120,
            command=self.refresh_devices
        )
        self.btn_refresh.grid(row=0, column=0, padx=5, pady=5)

        self.btn_apply = ctk.CTkButton(
            toolbar, text="💾 Применить настройки", width=150,
            command=self.apply_settings, state="disabled"
        )
        self.btn_apply.grid(row=0, column=1, padx=5, pady=5)

        self.btn_firmware = ctk.CTkButton(
            toolbar, text="📦 Прошить", width=120,
            command=self.load_firmware, state="disabled"
        )
        self.btn_firmware.grid(row=0, column=2, padx=5, pady=5)

        # Счетчик устройств справа
        self.device_count_label = ctk.CTkLabel(
            toolbar, text="Устройств: 0",
            font=ctk.CTkFont(size=12, weight="bold")
        )
        self.device_count_label.grid(row=0, column=3, padx=20, pady=5, sticky="e")

    def create_device_table(self):
        """Создание горизонтальной таблицы устройств"""
        # Контейнер для таблицы
        table_frame = ctk.CTkFrame(self)
        table_frame.grid(row=1, column=0, sticky="nsew", padx=10, pady=(5, 5))
        table_frame.grid_columnconfigure(0, weight=1)
        table_frame.grid_rowconfigure(0, weight=1)

        # Создаем ScrollableFrame для таблицы
        self.table_scroll = ctk.CTkScrollableFrame(table_frame)
        self.table_scroll.grid(row=0, column=0, sticky="nsew")
        self.table_scroll.grid_columnconfigure(0, weight=1)

        # Заголовки колонок
        headers = ["№", "Статус", "Тип", "Имя", "IP-адрес", "MAC", "Прошивка", "Режим", "Действия"]
        header_frame = ctk.CTkFrame(self.table_scroll)
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 5))

        for idx, header in enumerate(headers):
            label = ctk.CTkLabel(
                header_frame, text=header,
                font=ctk.CTkFont(size=12, weight="bold"),
                width=120 if idx > 0 else 50
            )
            label.grid(row=0, column=idx, padx=5, pady=5, sticky="ew")
            if idx > 0:
                header_frame.grid_columnconfigure(idx, weight=1)

        # Контейнер для строк устройств
        self.device_rows_frame = ctk.CTkFrame(self.table_scroll)
        self.device_rows_frame.grid(row=1, column=0, sticky="ew")
        self.device_rows_frame.grid_columnconfigure(0, weight=1)

    def create_device_row(self, device, index):
        """Создает строку устройства в таблице"""
        row_frame = ctk.CTkFrame(self.device_rows_frame)
        row_frame.grid(row=index, column=0, sticky="ew", pady=2, padx=2)

        # Статус иконка
        status_icon = "🟢" if device.dict['boot_mode'] == "ОСН." else "🟡"

        # Данные
        row_data = [
            str(index + 1),
            status_icon,
            device.dict['model'],
            device.dict['name'],
            device.dict['ip'],
            device.dict['mac'],
            device.dict['fw'],
            device.dict['boot_mode']
        ]

        # Создаем ячейки
        for col_idx, data in enumerate(row_data):
            label = ctk.CTkLabel(
                row_frame, text=data,
                font=ctk.CTkFont(size=11),
                width=120 if col_idx > 0 else 50
            )
            label.grid(row=0, column=col_idx, padx=5, pady=5, sticky="w")
            if col_idx > 0:
                row_frame.grid_columnconfigure(col_idx, weight=1)

        # Кнопка выбора
        btn_select = ctk.CTkButton(
            row_frame, text="Выбрать", width=80,
            command=lambda d=device: self.select_device(d)
        )
        btn_select.grid(row=0, column=len(row_data), padx=5, pady=5)

        return row_frame

    def create_details_panel(self):
        """Панель деталей устройства внизу"""
        details_container = ctk.CTkFrame(self, height=200)
        details_container.grid(row=2, column=0, sticky="ew", padx=10, pady=(5, 5))
        details_container.grid_columnconfigure(0, weight=1)

        # Заголовок
        header_frame = ctk.CTkFrame(details_container)
        header_frame.grid(row=0, column=0, sticky="ew", padx=5, pady=5)
        header_frame.grid_columnconfigure(1, weight=1)

        title_label = ctk.CTkLabel(
            header_frame, text="Параметры выбранного устройства",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        title_label.grid(row=0, column=0, padx=10, pady=5, sticky="w")

        # Содержимое
        content_frame = ctk.CTkFrame(details_container)
        content_frame.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 5))

        # Две колонки
        left_frame = ctk.CTkFrame(content_frame)
        left_frame.grid(row=0, column=0, sticky="nsew", padx=5)

        right_frame = ctk.CTkFrame(content_frame)
        right_frame.grid(row=0, column=1, sticky="nsew", padx=5)

        content_frame.grid_columnconfigure(0, weight=1)
        content_frame.grid_columnconfigure(1, weight=1)

        # Поля (левая колонка - только чтение, правая - редактируемые)
        self.detail_fields = {}

        # Левая колонка (информация)
        readonly_fields = [
            ("Модель:", "model"),
            ("Серийный номер:", "s_num"),
            ("MAC-адрес:", "mac"),
            ("Прошивка:", "fw"),
            ("Загрузчик:", "btldr"),
            ("Плата:", "pcb"),
        ]

        for idx, (label, key) in enumerate(readonly_fields):
            lbl = ctk.CTkLabel(left_frame, text=label, anchor="w")
            lbl.grid(row=idx, column=0, padx=5, pady=3, sticky="w")

            value_label = ctk.CTkLabel(left_frame, text="-", anchor="w")
            value_label.grid(row=idx, column=1, padx=5, pady=3, sticky="ew")
            left_frame.grid_columnconfigure(1, weight=1)

            self.detail_fields[key] = value_label

        # Правая колонка (редактируемые)
        editable_fields = [
            ("Имя:", "name"),
            ("IP-адрес:", "ip"),
            ("Маска:", "mask"),
            ("Шлюз:", "gateway"),
            ("Хост:", "host"),
            ("Порт:", "port"),
            ("Комментарий:", "comment"),
        ]

        for idx, (label, key) in enumerate(editable_fields):
            lbl = ctk.CTkLabel(right_frame, text=label, anchor="w")
            lbl.grid(row=idx, column=0, padx=5, pady=3, sticky="w")

            entry = ctk.CTkEntry(right_frame)
            entry.grid(row=idx, column=1, padx=5, pady=3, sticky="ew")
            right_frame.grid_columnconfigure(1, weight=1)

            self.detail_fields[key] = entry

    def create_statusbar(self):
        """Создание статус бара"""
        statusbar = ctk.CTkFrame(self, height=25, corner_radius=0)
        statusbar.grid(row=3, column=0, sticky="ew")
        statusbar.grid_columnconfigure(1, weight=1)

        self.status_label = ctk.CTkLabel(
            statusbar, text="Готов",
            font=ctk.CTkFont(size=10)
        )
        self.status_label.grid(row=0, column=0, padx=10, pady=2, sticky="w")

        # Версия справа
        version_label = ctk.CTkLabel(
            statusbar, text="DSU v2.0",
            font=ctk.CTkFont(size=10)
        )
        version_label.grid(row=0, column=1, padx=10, pady=2, sticky="e")

    def refresh_devices(self):
        """Обновляет список устройств"""
        # Очищаем текущий список
        for widget in self.device_rows_frame.winfo_children():
            widget.destroy()

        # Добавляем устройства
        for idx, device in enumerate(devs):
            self.create_device_row(device, idx)

        # Обновляем счетчик
        self.device_count_label.configure(text=f"Устройств: {len(devs)}")
        self.status_label.configure(text=f"Обновлено: {len(devs)} устройств")

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
        self.btn_apply.configure(state="normal")
        self.btn_firmware.configure(state="normal")

        self.status_label.configure(text=f"Выбрано: {device.dict['name']} ({device.dict['ip']})")

    def add_test_device(self):
        """Добавляет одно тестовое устройство"""
        from test_module import test

        for i in range(10):
            dev = test.test_dev(i)
            if devs.dev_index(dev) >= len(devs):
                devs.append(dev)
                self.refresh_devices()
                self.status_label.configure(text=f"Добавлено тестовое устройство #{i}")
                return

        messagebox.showwarning("Внимание", "Все тестовые устройства уже добавлены")

    def add_multiple_test_devices(self, count):
        """Добавляет несколько тестовых устройств"""
        from test_module import test

        added = 0
        for i in range(min(count, 10)):
            dev = test.test_dev(i)
            if devs.dev_index(dev) >= len(devs):
                devs.append(dev)
                added += 1

        if added > 0:
            self.refresh_devices()
            self.status_label.configure(text=f"Добавлено {added} тестовых устройств")

    def load_firmware(self):
        """Загрузка прошивки на устройство"""
        if not self.selected_device:
            messagebox.showwarning("Ошибка", "Выберите устройство")
            return

        file_path = filedialog.askopenfilename(
            title="Выберите файл прошивки",
            filetypes=[("Firmware files", "*.fw"), ("All files", "*.*")]
        )

        if not file_path:
            return

        self.show_progress_window(file_path)

    def show_progress_window(self, fw_path):
        """Окно прогресса прошивки"""
        progress_window = ctk.CTkToplevel(self)
        progress_window.title("Прошивка устройства")
        progress_window.geometry("500x200")
        progress_window.grab_set()

        label = ctk.CTkLabel(
            progress_window,
            text=f"Прошивка {self.selected_device.dict['name']}...",
            font=ctk.CTkFont(size=14)
        )
        label.pack(pady=20)

        progress = ctk.CTkProgressBar(progress_window, width=400)
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
                    messagebox.showinfo("Успех", "Прошивка завершена!")
                    self.status_label.configure(text="Прошивка завершена")
                    break

                time.sleep(0.1)

        threading.Thread(target=update_progress, daemon=True).start()

    def reboot_device(self):
        """Перезагрузка устройства"""
        if not self.selected_device:
            messagebox.showwarning("Ошибка", "Выберите устройство")
            return

        if messagebox.askyesno("Подтверждение",
                              f"Перезагрузить {self.selected_device.dict['name']}?"):
            self.selected_device.queue.append(
                locator.LocatorCmd.EXE_EL_CMD,
                pack=b'\x02'
            )
            self.selected_device.queue.run()
            self.status_label.configure(text="Команда перезагрузки отправлена")

    def goto_bootloader(self):
        """Переход в режим загрузчика"""
        if not self.selected_device:
            messagebox.showwarning("Ошибка", "Выберите устройство")
            return

        if messagebox.askyesno("Подтверждение",
                              f"Перейти в режим загрузчика {self.selected_device.dict['name']}?"):
            self.selected_device.queue.append(
                locator.LocatorCmd.EXE_EL_CMD,
                pack=eludp.ElCmd.RUN_BTLDR.value,
                pause=10
            )
            self.selected_device.queue.run()
            self.status_label.configure(text="Переход в режим загрузчика")

    def goto_normal_mode(self):
        """Переход в рабочий режим"""
        if not self.selected_device:
            messagebox.showwarning("Ошибка", "Выберите устройство")
            return

        if messagebox.askyesno("Подтверждение",
                              f"Перейти в рабочий режим {self.selected_device.dict['name']}?"):
            self.selected_device.queue.append(
                locator.LocatorCmd.EXE_EL_CMD,
                pack=b'\x05'
            )
            self.selected_device.queue.run()
            self.status_label.configure(text="Переход в рабочий режим")

    def apply_settings(self):
        """Применение настроек к устройству"""
        if not self.selected_device:
            return

        # Собираем настройки из полей
        settings = {}
        for key in ['name', 'ip', 'mask', 'gateway', 'host', 'port', 'comment']:
            if key in self.detail_fields and isinstance(self.detail_fields[key], ctk.CTkEntry):
                value = self.detail_fields[key].get()
                if key == 'port':
                    value = int(value)
                settings[key] = value

        self.selected_device.queue.append(
            locator.LocatorCmd.SET_PRIMARY,
            pack=self.selected_device.primary_settings_array(settings)
        )
        self.selected_device.queue.run()

        self.status_label.configure(text="Настройки применены")

        if messagebox.askyesno("Настройки применены",
                              "Перезагрузить устройство для применения?"):
            self.reboot_device()

    def change_theme(self, mode):
        """Смена темы интерфейса"""
        ctk.set_appearance_mode(mode)
        self.status_label.configure(text=f"Тема изменена: {mode}")

    def show_about(self):
        """О программе"""
        messagebox.showinfo(
            "О программе",
            "DSU - Device Setup Utility v2.0\n\n"
            "Утилита для настройки и обслуживания\n"
            "сетевых контроллеров\n\n"
            "Современный интерфейс на CustomTkinter\n"
            "Go модуль для быстрой прошивки"
        )

    def bind_events(self):
        """Привязка событий обновления списка"""
        devs.bind(lambda *args, **kwargs: self.after(100, self.refresh_devices),
                 [devices.DevLstEvent.APPEND_DEV,
                  devices.DevLstEvent.REMOVE_DEV,
                  devices.DevLstEvent.UPDATE_DEV])


def main():
    app = ModernDSU()
    app.mainloop()


if __name__ == "__main__":
    main()
