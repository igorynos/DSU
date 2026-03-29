# 📡 DSU - Device Setup Utility v2.0

**Профессиональная утилита для обнаружения, настройки и обслуживания сетевых контроллеров**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)

📖 **[Полная документация](README_FULL.md)**

## Возможности

- 🔍 **Автоматическое обнаружение устройств** через широковещательный UDP протокол
- ⚙️ **Управление настройками** контроллеров (IP, маска, порт, имя)
- 🔄 **Прошивка устройств** с поддержкой различных моделей
- ⚡ **Высокая скорость** прошивки благодаря Go модулю (10-100x быстрее)
- 🕐 **Синхронизация времени** с устройствами
- 🎮 **Графический интерфейс** на Tkinter
- 🧪 **Тестовые устройства** для разработки и отладки

## Поддерживаемые устройства

- CP-18
- POS
- AP-PRO
- TW-2020

## Установка

### Требования

- Python 3.11+
- Go 1.20+ (для сборки модуля прошивки)

### ⚡ Быстрый старт

### Вариант 1: Исходники (рекомендуется)

```bash
# 1. Клонирование и установка
git clone <repository-url> && cd DSU
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# 2. Запуск современного интерфейса
python3 app_modern.py

# Для полного функционала (с правами root)
sudo python3 app_modern.py
```

### Вариант 2: Docker

```bash
# Быстрый запуск
docker-compose up
```

### Вариант 3: Standalone EXE (Windows)

```bash
# Собрать EXE
build_exe.bat

# Запустить
dist\DSU.exe
```

📖 **[Подробный Quick Start →](QUICKSTART.md)**

## Использование

### Основной интерфейс

Запустите программу:
```bash
./run.sh
# или
python3 app.py
```

### Добавление тестовых устройств

Для разработки и тестирования без реальных устройств:

1. Откройте меню **"Инструменты" → "Тестовые устройства"**
2. Выберите **"Добавить тестовое устройство"** или **"Добавить 5 тестовых устройств"**

Тестовые устройства будут иметь:
- IP адреса: 192.168.0.100-109
- Порт: 1775
- Имена: Test 0 - Test 9

### Прошивка устройств

#### Python версия (медленная)
```python
from logic.firmware import Firmware

fw = Firmware("firmware.fw")
# Использование...
```

#### Go версия (быстрая, рекомендуется)
```python
from logic.firmware_go import FirmwareGo as Firmware

fw = Firmware("firmware.fw")
# API полностью совместим!
```

Программа автоматически использует Go версию для ускорения прошивки.

### Тестирование производительности

Сравните скорость Python и Go версий:

```bash
python3 benchmark_firmware.py firmware.fw
```

Ожидаемый результат:
- Загрузка: 50-100x быстрее
- Генерация пакетов: 20-50x быстрее
- Общее время: 30-80x быстрее

## Архитектура

```
DSU/
├── app.py                 # Главный файл приложения
├── loader.py              # Инициализация модулей
├── logic/                 # Бизнес-логика
│   ├── devices.py         # Работа с устройствами
│   ├── locator.py         # Широковещательный протокол
│   ├── eludp.py           # Адресный UDP протокол
│   ├── firmware.py        # Прошивка (Python, медленно)
│   ├── firmware_go.py     # Прошивка (Go обертка, быстро)
│   └── cmd_queue.py       # Очередь команд
├── interface/             # GUI
│   └── tk_int_dsu.py      # Tkinter интерфейс
├── go-firmware/           # Go модуль прошивки
│   ├── firmware.go        # Исходный код
│   ├── firmware           # Скомпилированный бинарник
│   └── README.md          # Документация Go модуля
├── config/                # Конфигурация
├── test_module/           # Тестовые утилиты
└── venv/                  # Виртуальное окружение Python
```

## Протоколы

### Locator (Широковещательный протокол)

- **Порт**: 1770
- **Команды**: REQUEST, SET_PRIMARY, READ_SETTINGS, EXE_EL_CMD, и др.
- **Интервал опроса**: 2 секунды
- **Таймаут watchdog**: 10 секунд

### ElUDP (Адресный протокол)

- **Порт**: Настраиваемый (по умолчанию 1775)
- **Команды**: SET_ADDR, RESTART, FW_INFO, FW_PACK, RUN_MAIN, RUN_BTLDR

## Разработка

### Структура пакетов прошивки

Файл прошивки (.fw) содержит:
- Заголовок (20 байт): версии, размер, контрольная сумма
- Данные прошивки (переменная длина)

См. `go-firmware/README.md` для подробностей.

### Добавление новых устройств

1. Добавьте модель в `DevModel` (devices.py)
2. Обновите парсинг параметров устройства
3. При необходимости добавьте специфичную логику

## Известные ограничения

### WSL2
- Горячие клавиши (keyboard) не работают
- Broadcast UDP требует sudo
- Нужен X-сервер для GUI (WSLg в Windows 11)

### Linux
- Keyboard модуль требует root прав
- Broadcast UDP требует sudo

## Troubleshooting

### Программа не запускается

```
ImportError: No module named 'keyboard'
```
**Решение**: Установите зависимости: `pip install -r requirements.txt`

### GUI не отображается

**WSL2**: Установите X-сервер (VcXsrv, X410) или используйте Windows 11 с WSLg

### Permission denied для broadcast

**Решение**: Запустите с sudo: `sudo python3 app.py`

### Go модуль не найден

```
FileNotFoundError: Go firmware binary not found
```
**Решение**: Соберите Go модуль:
```bash
cd go-firmware
go build -o firmware firmware.go
```

## Зависимости

### Python
- tkinter (GUI)
- netifaces (сетевые интерфейсы)
- keyboard (горячие клавиши, опционально)

### Go
- Стандартная библиотека Go

## Лицензия

[Укажите вашу лицензию]

## Контакты

[Укажите контактную информацию]
