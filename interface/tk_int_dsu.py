from loader import devs

import tkinter as tk
from tkinter import ttk
from tkinter import messagebox
from tkinter import filedialog

from . import icons_dict
import base64

import threading
import time
import datetime

import logic
import keyboard
from logic import locator
import socket
import test_module.test as test
from logic import firmware
from logic import eludp


# Part of interface


class MyFrame:
    def __init__(self):
        self.win = tk.Tk()
        self.win.protocol("WM_DELETE_WINDOW", self.close_win)
        self.win.geometry("760x560")
        self.win.minsize(760, 460)
        self.win.columnconfigure(0, minsize=700, weight=1)
        self.win.rowconfigure(0, minsize=50, weight=0)
        self.win.rowconfigure(1, minsize=150, weight=1)
        self.win.rowconfigure(2, minsize=200, weight=0)

        self.toolbar = ttk.Frame(self.win, padding=5)
        self.toolbar.grid(column=0, row=0, sticky='we')

        self.progressbar = ttk.Frame(self.win, padding=5)
        self.progressbar.grid(column=0, row=3, columnspan=2, sticky='ew')
        self.progressbar.columnconfigure(0, weight=1)

        self.frame_list = ttk.Frame(self.win, padding=5)
        self.frame_list.grid(column=0, row=1, sticky='nswe')
        self.frame_list.columnconfigure(0, weight=1)
        self.frame_list.columnconfigure(1, weight=0)
        self.frame_list.rowconfigure(0, weight=1)
        self.frame_parametry = ttk.Frame(self.win, padding=5)
        self.frame_parametry.grid(column=0, row=2, sticky='we', padx=18)
        self.frame_parametry.grid_columnconfigure(0, minsize=100, weight=0)
        self.frame_parametry.grid_columnconfigure(1, minsize=300, weight=1)
        self.frame_parametry.grid_columnconfigure(2, minsize=100, weight=1)
        self.frame_parametry.grid_columnconfigure(3, minsize=200, weight=1)
        for x in range(6):
            self.frame_parametry.grid_rowconfigure(x, minsize=25, weight=1)

        # Style
        self.style = ttk.Style()
        self.style.configure("Treeview.Heading", font=(None, 12))
        self.style.configure("TLabel", font=(None, 12))
        self.style.configure("Treeview", font=(None, 12))
        self.style.configure('Normal.TEntry')
        self.style.configure('Error.TEntry', fieldbackground='red')
        self.style.layout('Error.TEntry',
                          [('Entry.plain.field',
                            {'sticky': 'nswe',
                             'border': 1,
                             'children': [('Entry.background',
                                           {'sticky': 'nswe',
                                            'children': [('Entry.padding',
                                                          {'sticky': 'nswe',
                                                           'children': [('Entry.textarea',
                                                                         {'sticky': 'nswe'}
                                                                         )]})]})]})])

        # Menu
        self.mainmenu = tk.Menu(self.win)
        self.win.config(menu=self.mainmenu)

        self.filemenu = tk.Menu(self.mainmenu, tearoff=0)

        self.mainmenu.add_cascade(label=" Файл", menu=self.filemenu)

        self.filemenu.add_command(label="Пусто", state='disabled')

        self.toolmenu = tk.Menu(self.mainmenu, tearoff=0)
        self.comandmenu = tk.Menu(self.toolmenu, tearoff=0)

        self.mainmenu.add_cascade(label="Инструменты", menu=self.toolmenu)

        self.toolmenu.add_cascade(label="Команды", menu=self.comandmenu)
        self.comandmenu.add_command(
            label='Перезагрузить контроллер', command=self.ask_reset)
        self.comandmenu.add_command(
            label='Перейти в режим загрузчика', command=self.loadmode)
        self.comandmenu.add_command(
            label='Перейти в рабочий режим', command=self.normalmode)

        self.toolmenu.add_cascade(
            label="Установка времени", command=self.time_seting)

        # Import image

        self.image_toolbar1 = tk.PhotoImage(
            data=base64.b64decode(icons_dict.dict_icon['send_settings']))

        self.image_toolbar2 = tk.PhotoImage(
            data=base64.b64decode(icons_dict.dict_icon['restart']))

        self.image_toolbar3 = tk.PhotoImage(
            data=base64.b64decode(icons_dict.dict_icon['load_fw']))

        # Toolbar
        self.insertbutton = ttk.Button(self.toolbar, image=self.image_toolbar1,
                                       command=self.dev_dict_send, state="disabled")
        self.insertbutton.grid(row=0, column=0)

        self.insertbutton_reset = ttk.Button(self.toolbar, image=self.image_toolbar2,
                                             command=self.ask_reset, state="disabled")
        self.insertbutton_reset.grid(row=0, column=1, padx=5)

        self.insertbutton_load_fw = ttk.Button(self.toolbar, image=self.image_toolbar3,
                                               command=self.load_fw, state="disabled")
        self.insertbutton_load_fw.grid(row=0, column=2, padx=5)

        # Progressbar

        self.progress_line = ttk.Progressbar(
            self.progressbar, orient="horizontal", mode="determinate")
        self.progress_line.grid(row=0, column=0, sticky="we")

        # GlobalVar
        self.strvar = []
        for x in range(7):
            self.strvar.append(tk.StringVar())
            self.strvar[x].trace("w", self.turn_button)

        self.view_time = tk.StringVar()
        self.view_time.trace_add("write", self.update_time)
        self.view_date = tk.StringVar()
        self.view_date.trace_add("write", self.update_date)

        # LST - DEVICE
        head = [("№", 30), ("Тип", 80), ("Модель", 80),
                ("Версия", 180), ("Имя", 200), ("IP", 150)]
        self.table = ttk.Treeview(self.frame_list, show="headings")
        self.table.grid(column=0, row=0, sticky='nswe')
        self.table['columns'] = head

        self.scroll = ttk.Scrollbar(
            self.frame_list, command=self.table.yview, orient='vertical')
        self.scroll.grid(column=1, row=0, sticky='ns')
        self.table.config(yscrollcommand=self.scroll.set)

        for i, x in enumerate(head):
            self.table.heading(i, text=x[0], anchor='center')
            self.table.column(i, anchor="center", width=x[1])

        self.table.bind("<<TreeviewSelect>>", self.item_selected)

        self.lst_device_name = ["Устройство", "Сер. номер", "MAC-адрес",
                                "Прошивка", "Загрузчик", "Плата", "Имя",
                                "Адрес", "Маска", "Шлюз", "Хост", "Порт", "Коментарий"]
        self.lst_device = []
        self.lst_device_value = []
        for i, x in enumerate(self.lst_device_name[:-1]):
            if i < 6:
                self.lst_device.append(ttk.Label(self.frame_parametry, text=x))
                self.lst_device[-1].grid(row=i, column=0, sticky='e')
                self.lst_device_value.append(
                    ttk.Label(self.frame_parametry, text=""))
                self.lst_device_value[-1].grid(row=i, column=1, sticky='w')
            else:
                self.lst_device.append(ttk.Label(self.frame_parametry, text=x))
                self.lst_device[-1].grid(row=i - 6, column=2, sticky="e")
                self.lst_device_value.append(
                    ttk.Entry(self.frame_parametry, font=(None, 12), style='Normal.TEntry'))
                self.lst_device_value[-1].grid(row=i - 6,
                                               column=3, sticky="we")

        self.lst_device.append(
            ttk.Label(self.frame_parametry, text=self.lst_device_name[-1]))
        self.lst_device[-1].grid(row=7, column=0, sticky="e")
        self.lst_device_value.append(
            ttk.Entry(self.frame_parametry, font=(None, 12)))
        self.lst_device_value[-1].grid(row=7,
                                       column=1, columnspan=3, sticky="we")
        for i, x in enumerate(self.lst_device_value[6:]):
            x['textvariable'] = self.strvar[i]

        self.slct_dev = None
        self.get_devs(None, None)

    # Func

    def get_devs(self, *args, **kwargs):
        self.clear_dev()
        for item in self.table.get_children():
            self.table.delete(item)
        for i, x in enumerate(devs):
            self.table.insert('', tk.END, values=[i + 1, x.dict['model'], x.dict['boot_mode'],
                                                  f"{x.dict['fw']}/{x.dict['btldr']}/{x.dict['pcb']}",
                                                  x.dict['name'], x.dict['ip']])

    def item_selected(self, event):
        get_index = None
        for selected_item in self.table.selection():
            item = self.table.item(selected_item)
            get_index = item["values"]
        if get_index is None:
            return
        self.slct_dev = devs[int(get_index[0]) - 1]
        for i, x in enumerate(self.lst_device_value):
            get_key = ['model', 's_num', 'mac', 'fw', 'btldr',
                       'pcb', 'name', 'ip', 'mask', 'gateway', 'host', 'port', 'comment']
            if i < 6:
                x["text"] = f"{self.slct_dev.dict[get_key[i]]}"
            else:
                if x.get() != "":
                    x.delete(0, "end")
                x.insert(
                    0, f"{self.slct_dev.dict[get_key[i]]}")

    def dev_dict_send(self):
        result = messagebox.askquestion(
            'Подтверждение', f'Изменить настройки контроллера "{self.slct_dev.dict["name"]}" по адресу "{self.slct_dev.dict["ip"]}"?')
        if result == 'yes':
            dev_dict = {}
            get_key = ['name', 'ip', 'mask',
                       'gateway', 'host', 'port', 'comment']
            for i, x in enumerate(get_key):
                dev_dict[x] = self.lst_device_value[6+i].get()
            dev_dict['port'] = int(dev_dict['port'])
            self.slct_dev.queue.append(
                locator.LocatorCmd.SET_PRIMARY, pack=self.slct_dev.primary_settings_array(dev_dict))
            self.slct_dev.queue.run()
            self.get_devs()

            result = messagebox.askquestion(
                'Подтверждение', 'Данные настройки будут применены только после перезагрузки контроллера.\nПерезагрузить контроллер?')
            if result == 'yes':
                self.reset_button()

    def turn_button(self, *args):
        error = [self.lst_device_value[6:][x] for x in self.check_value()]
        self.rigth_dev(error)
        if len(error) != 0:
            self.insertbutton.config(state='disabled')
            self.insertbutton_reset.config(state='disabled')
            self.insertbutton_load_fw.config(state='disabled')
        else:
            self.insertbutton.config(state='normal')
            self.insertbutton_reset.config(state='normal')
            self.insertbutton_load_fw.config(state='normal')

    def ask_reset(self):
        if self.slct_dev is None:
            messagebox.showwarning('Предупреждение', 'Выберите контроллер')
            return
        result = messagebox.askquestion(
            'Подтверждение', f'Перезагрузить контроллер "{self.slct_dev.dict["name"]}" по адресу "{self.slct_dev.dict["ip"]}"?')
        if result == 'yes':
            self.reset_button()

    def reset_button(self):
        if self.slct_dev is None:
            messagebox.showwarning('Предупреждение', 'Выберите контроллер')
            return
        self.slct_dev.queue.append(
            locator.LocatorCmd.EXE_EL_CMD, pack=b'\x02')
        self.slct_dev.queue.run()
        for x in range(20):
            self.progress_line['value'] += 5
            time.sleep(0.5)
        self.progress_line['value'] = 0

    def check_dev_value(self, i):
        if i == 0 and len(self.strvar[i].get()) > 16:
            return False
        if i in range(1, 5) and self.is_ip(self.strvar[i].get()) == False:
            return False
        if i == 5:
            if not all(map(lambda x: x in "0123456789", self.strvar[i].get())):
                return False
            if self.strvar[i].get() != '':
                if int(self.strvar[i].get()) > 65536 or int(self.strvar[i].get()) < 0:
                    return False
        if i == 6 and 64 < len(self.strvar[i].get()):
            return False
        if i in range(1, 6) and len(self.strvar[i].get()) < 1 and self.slct_dev is not None:
            return False
        return True

    def check_value(self):
        error_lst = []
        for i, val in enumerate(self.lst_device_value[6:]):
            if not self.check_dev_value(i):
                error_lst.append(i)
        return error_lst

    def rigth_dev(self, lst):
        for x in lst:
            x['style'] = 'Error.TEntry'
        for x in self.lst_device_value[6:]:
            if x not in lst:
                x['style'] = 'Normal.TEntry'

    def clear_dev(self):
        if self.slct_dev is None:
            return
        if self.slct_dev in devs:
            return
        for i, x in enumerate(self.lst_device_value):
            get_key = ['model', 's_num', 'mac', 'fw', 'btldr',
                       'pcb', 'name', 'ip', 'mask', 'gateway', 'host', 'port', 'comment']
            if i < 6:
                x["text"] = ""
            else:
                x.delete(0, "end")
        self.slct_dev = None
        for x in self.lst_device_value[6:]:
            x['style'] = 'Normal.TEntry'

    def is_ip(self, ip):
        try:
            socket.inet_aton(ip)
            return True
        except socket.error:
            return False

    def normalmode(self):
        if self.slct_dev is None:
            messagebox.showwarning('Предупреждение', 'Выберите контроллер')
            return
        result = messagebox.askquestion(
            'Подтверждение', f'Перейти в рабочий режим контроллера "{self.slct_dev.dict["name"]}" по адресу "{self.slct_dev.dict["ip"]}"?')
        if result == 'yes':
            self.slct_dev.queue.append(
                locator.LocatorCmd.EXE_EL_CMD, pack=b'\x05')
            self.slct_dev.queue.run()

    def loadmode(self):
        if self.slct_dev is None:
            messagebox.showwarning('Предупреждение', 'Выберите контроллер')
            return
        result = messagebox.askquestion(
            'Подтверждение', f'Перейти в режим загрузчика контроллера "{self.slct_dev.dict["name"]}" по адресу "{self.slct_dev.dict["ip"]}"?')
        if result == 'yes':
            self.slct_dev.queue.append(
                locator.LocatorCmd.EXE_EL_CMD, pack=eludp.ElCmd.RUN_BTLDR.value, pause=10)
            self.slct_dev.queue.run()

    def load_fw(self):
        wanted_file = (('FW', '*.fw'),
                       ('DOCX', '*.txt, *.docx'))
        file = filedialog.askopenfilename(filetypes=wanted_file)
        if len(file) == 0 or '.fw' not in file:
            return
        self.slct_dev.queue.append(
            locator.LocatorCmd.EXE_EL_CMD, pack=eludp.ElCmd.RUN_BTLDR.value, pause=10)
        self.slct_dev.queue.append(
            locator.LocatorCmd.EXE_EL_CMD, gen=firmware.Firmware(file))
        self.slct_dev.queue.append(
            locator.LocatorCmd.EXE_EL_CMD, pack=eludp.ElCmd.RUN_MAIN.value)
        self.slct_dev.queue.run()
        thread = threading.Thread(target=self.progress_queue)
        thread.start()

    def progress_queue(self):
        prog = 1
        while prog != 0:
            time.sleep(0.5)
            prog = self.slct_dev.queue.progress()
            self.progress_line['value'] = prog

    def time_seting(self):
        if self.slct_dev is None:
            messagebox.showwarning('Предупреждение', 'Выберите контроллер')
            return

        self.time_slct_dev = bytes(6)

        self.slct_dev.queue.append(
            locator.LocatorCmd.READ_SETTINGS, pack=b'\x20')
        self.slct_dev.queue.run()

        self.view_time.set(
            f'{self.time_slct_dev[-4]:02}:{self.time_slct_dev[-5]:02}:{self.time_slct_dev[-6]:02}')
        self.view_date.set(
            f'{self.time_slct_dev[-3]:02}.{self.time_slct_dev[-2]:02}.{self.time_slct_dev[-1]:02}')

        self.win_time = tk.Tk()
        self.win_time.protocol("WM_DELETE_WINDOW", self.close_win_time)
        self.win_time.title('Установка времени')

        self.win_flag = True

        self.win_time.grid_columnconfigure(0, minsize=30, weight=1)
        self.win_time.grid_columnconfigure(1, minsize=30, weight=1)

        self.devise_time = ttk.Label(
            self.win_time, text='Время контроллера', font=12)
        self.devise_time.grid(row=0, column=0, columnspan=2,
                              sticky='ew', padx=5, pady=2)
        self.time_value = ttk.Entry(self.win_time, font=(
            None, 12), style='Normal.TEntry', textvariable=self.view_time)
        # self.time_value.insert(0, self.view_time)
        self.time_value.grid(row=1, column=0, columnspan=3,
                             sticky='ew', padx=5, pady=2)
        self.devise_date = ttk.Label(
            self.win_time, text='Дата контроллера', font=12)
        self.devise_date.grid(row=2, column=0, columnspan=2,
                              sticky='ew', padx=5, pady=2)
        self.date_value = ttk.Entry(self.win_time, font=(
            None, 12), style='Normal.TEntry', textvariable=self.view_date)
        # self.date_value.insert(0, self.view_date)
        self.date_value.grid(row=3, column=0, columnspan=3,
                             sticky='ew', padx=5, pady=2)
        self.button_install_time = tk.Button(
            self.win_time, text='Установка даты и времени', font=12, command=self.install_time)
        self.button_install_time.grid(row=4, column=0, columnspan=3,
                                      sticky='ew', padx=5, pady=2)
        self.button_install_sys = tk.Button(
            self.win_time, text='Системные дата и время', font=12, command=self.time_now)
        self.button_install_sys.grid(row=5, column=0, columnspan=3,
                                     sticky='ew', padx=5, pady=2)
        self.button_install_hand = tk.Button(
            self.win_time, text='Свои дата и время', font=12, command=self.time_hand)
        self.button_install_hand.grid(row=6, column=0, columnspan=3,
                                      sticky='ew', padx=5, pady=2)

    def get_time(self, ev, dev, cmd, pack):
        self.time_slct_dev = [byte for byte in pack]
        print(self.time_slct_dev)
        self.view_time.set(
            f'{self.time_slct_dev[-4]:02}:{self.time_slct_dev[-5]:02}:{self.time_slct_dev[-6]:02}')
        self.view_date.set(
            f'{self.time_slct_dev[-3]:02}.{self.time_slct_dev[-2]:02}.{self.time_slct_dev[-1]:02}')
        self.tread1 = threading.Thread(target=self.test_print, args=(
            self.view_time.get(), self.view_date.get()))
        self.tread1.start()

    def install_time(self):
        time = [int(x) for x in self.time_value.get().split(":")]
        date = [int(x) for x in self.date_value.get().split(".")]
        pack_byte = b'\x20' + bytes([time[-1], time[-2],
                                    time[-3], date[-3], date[-2], date[-1], 1])
        self.slct_dev.queue.append(
            locator.LocatorCmd.EXE_EL_CMD, pack=pack_byte)
        self.slct_dev.queue.run()

    def test_print(self, get_time, get_date):
        dev_time = []
        dev_date = []
        for x in get_time.split(':'):
            if x[0] == '0':
                dev_time.append(int(x[1]))
            else:
                dev_time.append(int(x))
        for x in get_date.split('.'):
            if x[0] == '0':
                dev_date.append(int(x[1]))
            else:
                dev_date.append(int(x))
        if dev_date[0] == 0:
            dev_date[0] = 1
        if dev_date[1] == 0:
            dev_date[1] = 1

        self.my_time = datetime.datetime(
            year=2000+dev_date[2], month=dev_date[1], day=dev_date[0], hour=dev_time[0], minute=dev_time[1], second=dev_time[2])

        while self.win_flag:
            self.my_time += datetime.timedelta(seconds=1)
            self.view_time.set(f"{self.my_time.strftime('%H:%M:%S')}")
            self.view_date.set(f"{self.my_time.strftime('%d.%m.%Y')}")
            time.sleep(1)

    def update_time(self, *args):
        try:
            self.time_value.delete(0, tk.END)
            self.time_value.insert(0, self.view_time.get())
        except:
            pass

    def update_date(self, *args):
        try:
            self.date_value.delete(0, tk.END)
            self.date_value.insert(0, self.view_date.get())
        except:
            pass

    def time_now(self):
        self.my_time = datetime.datetime.now()

    def time_hand(self):
        self.win_flag = False

    def close_win_time(self):
        self.win_flag = False
        self.win_time.destroy()

    def close_win(self):
        if messagebox.askokcancel("Выход из приложения", "Хотите выйти из приложения?"):
            self.win.destroy()
            self.win_flag = False
            try:
                self.close_win_time()
            except:
                pass
