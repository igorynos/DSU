# 📡 DSU - Device Setup Utility v2.0

<div align="center">

**Профессиональная утилита для обнаружения, настройки и обслуживания сетевых контроллеров**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Go](https://img.shields.io/badge/Go-1.21+-00ADD8.svg)](https://golang.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

[Возможности](#-возможности) • [Установка](#-установка) • [Запуск](#-запуск) • [Документация](#-документация) • [FAQ](#-faq)

</div>

---

## 📋 Содержание

- [Возможности](#-возможности)
- [Системные требования](#-системные-требования)
- [Установка](#-установка)
  - [Из исходников](#из-исходников)
  - [Docker](#docker)
  - [Standalone EXE](#standalone-exe-windows)
- [Запуск](#-запуск)
  - [Основные способы](#основные-способы-запуска)
  - [Docker запуск](#запуск-в-docker)
  - [Режимы работы](#режимы-работы)
- [Интерфейсы](#-интерфейсы)
- [Функционал](#-функционал)
- [Протоколы](#-протоколы)
- [Архитектура](#-архитектура)
- [Производительность](#-производительность)
- [Troubleshooting](#-troubleshooting)
- [Разработка](#-разработка)

---

## 🚀 Возможности

### Основной функционал

- 🔍 **Автоматическое обнаружение устройств**
  - Широковещательный UDP протокол (порт 1770)
  - Циклический опрос каждые 2 секунды
  - Автоматическое отслеживание подключений/отключений
  - Watchdog-мониторинг доступности (таймаут 10 сек)

- ⚙️ **Управление настройками**
  - Изменение IP-адреса, маски, шлюза
  - Настройка UDP-порта устройства
  - Редактирование имени и комментария
  - Валидация параметров в реальном времени
  - Применение настроек с автоматической перезагрузкой

- 📦 **Прошивка устройств**
  - Поддержка файлов .fw
  - **Ускорение в 20-100 раз** благодаря Go модулю
  - Отображение прогресса в реальном времени
  - Автоматическое переключение в режим загрузчика
  - Проверка контрольной суммы

- 🕐 **Синхронизация времени**
  - Установка системного времени
  - Ручная настройка даты/времени
  - Отображение текущего времени устройства

- 🧪 **Тестовый режим**
  - Виртуальные устройства для разработки
  - Не требует реального оборудования
  - Полная эмуляция протоколов

### Поддерживаемые устройства

| Модель | Описание | Протокол |
|--------|----------|----------|
| **CP-18** | Контроллер парковки | Locator + ElUDP |
| **POS** | POS-терминал | Locator + ElUDP |
| **AP-PRO** | Точка доступа PRO | Locator + ElUDP |
| **TW-2020** | Турникет 2020 | Locator + ElUDP |

---

## 💻 Системные требования

### Минимальные

- **OS**: Linux, Windows 10+, macOS 10.14+
- **Python**: 3.11 или выше
- **RAM**: 256 MB
- **Disk**: 500 MB свободного места
- **Network**: Ethernet/Wi-Fi с поддержкой UDP broadcast

### Рекомендуемые

- **OS**: Ubuntu 22.04 LTS / Windows 11 / macOS 13+
- **Python**: 3.11+
- **Go**: 1.21+ (для компиляции firmware модуля)
- **RAM**: 512 MB
- **Disk**: 1 GB
- **Network**: Gigabit Ethernet

### Опциональные зависимости

- **Docker**: 20.10+ (для контейнерного запуска)
- **X11 Server**: Для GUI в WSL2/Docker
- **Go compiler**: Для пересборки firmware модуля

---

## 📥 Установка

### Из исходников

#### Linux / macOS

```bash
# 1. Клонирование репозитория
git clone https://github.com/yourname/DSU.git
cd DSU

# 2. Создание виртуального окружения
python3 -m venv venv
source venv/bin/activate

# 3. Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# 4. Сборка Go модуля (опционально, для максимальной скорости)
cd go-firmware
go build -o firmware firmware.go
cd ..

# 5. Запуск
python3 app_modern.py
```

#### Windows

```powershell
# 1. Клонирование
git clone https://github.com/yourname/DSU.git
cd DSU

# 2. Создание виртуального окружения
python -m venv venv
venv\Scripts\activate

# 3. Установка зависимостей
pip install --upgrade pip
pip install -r requirements.txt

# 4. Сборка Go модуля
cd go-firmware
go build -o firmware.exe firmware.go
cd ..

# 5. Запуск
python app_modern.py
```

### Docker

```bash
# Сборка образа
docker build -t dsu:latest .

# Или использование docker-compose
docker-compose up -d
```

**Примечание**: Для GUI в Docker требуется X11 forwarding (см. раздел [Docker запуск](#запуск-в-docker))

### Standalone EXE (Windows)

```bash
# Компиляция в EXE
./build_exe.bat

# Запуск
dist\DSU.exe
```

---

## 🎮 Запуск

### Основные способы запуска

#### 1. Современный интерфейс (рекомендуется)

```bash
# С темной темой
python3 app_modern.py

# Или используя алиас
./run_modern.sh
```

**Особенности**:
- Темная/светлая тема
- Современный Material Design
- Responsive layout
- Карточки устройств
- Прогресс-бары
- Интерактивные элементы

#### 2. Классический интерфейс (Tkinter)

```bash
python3 app.py
```

**Особенности**:
- Совместимость со старыми системами
- Меньше зависимостей
- Быстрый запуск

#### 3. Командная строка (без GUI)

```python
from loader import devs, lctr, lctr_thr

# Запуск locator в фоне
lctr_thr.start()

# Работа с API
print(f"Найдено устройств: {len(devs)}")
for dev in devs:
    print(dev)

# Завершение
lctr.shutdown()
lctr_thr.join()
```

### Запуск в Docker

#### Linux

```bash
# 1. Разрешить X11 connections
xhost +local:docker

# 2. Запуск контейнера
docker run --rm -it \
  --network=host \
  --cap-add=NET_ADMIN \
  --cap-add=NET_RAW \
  -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  dsu:latest

# 3. Или через docker-compose
docker-compose up
```

#### Windows (с VcXsrv)

```powershell
# 1. Установить VcXsrv или X410
# 2. Запустить X Server с опцией "Disable access control"

# 3. Запуск контейнера
docker run --rm -it ^
  --network=host ^
  -e DISPLAY=host.docker.internal:0 ^
  dsu:latest
```

### Режимы работы

#### Обычный режим (без прав root)

```bash
python3 app_modern.py
```

**Доступно**:
- Просмотр устройств (если есть в devices.ini)
- Тестовые устройства
- Настройка параметров
- Прошивка (только для тестовых)

**Недоступно**:
- Широковещательный поиск
- Реальные сетевые команды

#### Привилегированный режим (с sudo)

```bash
sudo python3 app_modern.py
```

**Полный функционал**:
- ✅ Автоматическое обнаружение устройств
- ✅ Отправка broadcast UDP
- ✅ Прошивка реальных устройств
- ✅ Все сетевые операции

---

## 🎨 Интерфейсы

### Современный интерфейс (CustomTkinter)

<details>
<summary><b>Скриншоты и описание</b></summary>

#### Главное окно

**Компоненты**:
1. **Боковая панель** (слева)
   - Логотип и версия
   - Кнопки действий
   - Переключатель темы

2. **Список устройств** (центр)
   - Карточки с информацией
   - Статус-иконки (🟢 ОСН / 🟡 ЗАГР)
   - Кнопки выбора

3. **Панель деталей** (справа)
   - Просмотр параметров
   - Редактирование настроек
   - Валидация ввода

#### Функции интерфейса

- **Обновить** - принудительное обновление списка
- **Тестовое устройство** - добавление виртуальных контроллеров
- **Прошить устройство** - загрузка firmware
- **Перезагрузка** - restart контроллера
- **Применить настройки** - сохранение изменений

#### Темы

- **Темная** (по умолчанию) - снижает нагрузку на глаза
- **Светлая** - классический вид

</details>

### Классический интерфейс (Tkinter)

<details>
<summary><b>Описание</b></summary>

**Основные элементы**:
- Таблица устройств с сортировкой
- Меню с командами
- Панель инструментов
- Область редактирования параметров

**Преимущества**:
- Нативный вид ОС
- Минимальные зависимости
- Стабильная работа

</details>

---

## 📖 Функционал

### 1. Обнаружение устройств

#### Автоматическое

```python
# Автоматически запускается при старте
# Опрос каждые 2 секунды
# Broadcast на порт 1770
```

#### Ручное добавление

```python
# Через devices.ini
[ELUDP]
device1: ip=192.168.1.100, port=1775
device2: ip=192.168.1.101, port=1775
```

### 2. Настройка параметров

**Редактируемые поля**:
- `name` - имя устройства (16 символов)
- `ip` - IP-адрес (формат: xxx.xxx.xxx.xxx)
- `mask` - маска подсети
- `gateway` - шлюз
- `host` - IP хоста
- `port` - UDP порт (1-65535)
- `comment` - комментарий (64 символа)

**Валидация**:
- IP адреса проверяются на корректность
- Порт в диапазоне 1-65535
- Длина строк не превышает лимиты
- Подсветка ошибок в реальном времени

### 3. Прошивка устройств

#### Процесс прошивки

```
1. Выбор устройства
2. Выбор файла .fw
3. Переход в режим загрузчика (10 сек)
4. Отправка заголовка firmware
5. Отправка данных блоками по 32 байта
6. Проверка контрольной суммы
7. Переход в основной режим
```

#### Формат файла прошивки

```c
typedef struct {
    uint8_t   crypt_mode;      // Режим шифрования
    uint8_t   device_header;   // Версия заголовка
    uint8_t   fw_ver[2];       // Версия прошивки
    uint8_t   reserved[2];     // Резерв
    uint8_t   pcb_ver[2];      // Версия платы
    uint8_t   btldr_ver[2];    // Версия загрузчика
    uint32_t  offset;          // Начальный адрес
    uint16_t  fw_len;          // Длина (в 32-бит словах)
    uint8_t   reserved_2[2];   // Резерв
    uint32_t  check_sum;       // Контрольная сумма
} FirmwareHeader;  // 20 байт

// Затем следуют данные прошивки
```

### 4. Тестовые устройства

**Создание**:
```python
# Через меню: Инструменты → Тестовые устройства
# Или программно:
from test_module import test
from loader import devs

for i in range(5):
    dev = test.test_dev(i)
    devs.append(dev)
```

**Параметры тестовых устройств**:
- IP: 192.168.0.100 - 192.168.0.109
- Порт: 1775
- Модель: POS
- Имя: Test 0 - Test 9

---

## 🔌 Протоколы

### Locator Protocol (Широковещательный)

**Порт**: 1770 UDP
**Интервал**: 2 секунды

#### Команды

| Команда | Код | Описание |
|---------|-----|----------|
| `REQUEST` | 0x01 | Запрос обнаружения |
| `SET_PRIMARY` | 0x02 | Установка основных настроек |
| `READ_SETTINGS` | 0x03 | Чтение настроек |
| `EXE_EL_CMD` | 0x04 | Выполнение адресной команды |
| `READ_MEM_PROP` | 0x05 | Чтение свойств памяти |
| `READ_MEM_DUMP` | 0x06 | Дамп памяти |
| `GET_MAP` | 0x07 | Получение карты |
| `GET_LOG` | 0x08 | Получение лога |
| `CLEAR_LOG` | 0x09 | Очистка лога |
| `SET_USER` | 0x0A | Установка пользователя |
| `GET_USER` | 0x0B | Получение пользователя |

#### Структура пакета

```c
typedef struct {
    uint8_t  password[8];  // '12345678'
    uint8_t  s_num[16];    // Серийный номер (reversed)
    uint8_t  ver;          // Версия протокола
    uint8_t  cmd;          // Команда
    uint8_t  len;          // Длина данных
    uint8_t  data[len];    // Данные
    uint8_t  checksum;     // Контрольная сумма
} LocatorPacket;
```

### ElUDP Protocol (Адресный)

**Порт**: Настраиваемый (по умолчанию 1775)

#### Команды

| Команда | Код | Описание |
|---------|-----|----------|
| `SET_ADDR` | 0x01 | Установка адреса |
| `RESTART` | 0x02 | Перезагрузка |
| `FW_INFO` | 0x03 | Информация о прошивке |
| `FW_PACK` | 0x04 | Пакет прошивки |
| `RUN_MAIN` | 0x05 | Запуск основной программы |
| `RUN_BTLDR` | 0x06 | Запуск загрузчика |

---

## 🏗️ Архитектура

### Структура проекта

```
DSU/
├── 📱 Интерфейсы
│   ├── interface/
│   │   ├── tk_int_dsu.py      # Классический Tkinter
│   │   └── modern_ui.py       # Современный CustomTkinter
│   ├── app.py                 # Запуск классического
│   └── app_modern.py          # Запуск современного
│
├── 🧠 Бизнес-логика
│   ├── logic/
│   │   ├── devices.py         # Управление устройствами
│   │   ├── locator.py         # Широковещательный протокол
│   │   ├── eludp.py           # Адресный протокол
│   │   ├── firmware.py        # Прошивка (Python, медленно)
│   │   ├── firmware_go.py     # Прошивка (Go обертка, быстро)
│   │   └── cmd_queue.py       # Очередь команд
│   └── loader.py              # Инициализация
│
├── ⚡ Go модуль
│   └── go-firmware/
│       ├── firmware.go        # Исходный код
│       ├── firmware           # Скомпилированный бинарник
│       └── README.md
│
├── 🧪 Тестирование
│   ├── test_module/
│   │   └── test.py
│   └── benchmark_firmware.py
│
├── 🐳 Docker
│   ├── Dockerfile
│   ├── docker-compose.yml
│   └── .dockerignore
│
├── 📦 Компиляция
│   ├── DSU.spec               # PyInstaller config
│   ├── build_exe.sh           # Linux/Mac build
│   └── build_exe.bat          # Windows build
│
└── 📚 Документация
    ├── README.md              # Краткое описание
    ├── README_FULL.md         # Полная документация (этот файл)
    └── go-firmware/README.md  # Go модуль
```

### Компоненты

#### 1. Device Management Layer

**Класс `Device`**:
- Хранит параметры устройства
- Валидация данных
- Очередь команд
- Watchdog таймер

**Класс `DeviceList`**:
- Список устройств
- Event система (append/remove/update)
- Поиск по серийному номеру/IP
- Thread-safe операции

#### 2. Protocol Layer

**Locator**:
- Broadcast UDP сканирование
- Прием ответов
- Обработка команд
- Threading для асинхронности

**ElUDP**:
- Адресная отправка
- Множественные порты
- Callback система

#### 3. Firmware Layer

**Python версия** (`firmware.py`):
- Чистый Python
- Медленная обработка
- Генераторы для стриминга

**Go версия** (`firmware_go.py`):
- Вызов Go бинарника
- JSON парсинг
- 20-100x быстрее

#### 4. UI Layer

**Modern UI** (`modern_ui.py`):
- CustomTkinter
- Material Design
- Темная/светлая тема
- Responsive

**Classic UI** (`tk_int_dsu.py`):
- Tkinter
- Табличное представление
- Меню и toolbar

---

## ⚡ Производительность

### Benchmark результаты

#### Загрузка прошивки (100 KB файл)

| Версия | Загрузка | Генерация пакетов | Общее время | Ускорение |
|--------|----------|-------------------|-------------|-----------|
| Python | 45 ms | 120 ms | 165 ms | 1x |
| Go | 0.8 ms | 3.2 ms | 4 ms | **41x** |

#### Обработка большого файла (1 MB)

| Версия | Время | Память |
|--------|-------|--------|
| Python | 1650 ms | 12 MB |
| Go | 28 ms | 2 MB |
| **Ускорение** | **59x** | **6x меньше** |

### Запуск benchmark

```bash
python3 benchmark_firmware.py firmware.fw
```

---

## ❓ Troubleshooting

### Проблемы запуска

#### Python не найден

```bash
# Linux/Mac
which python3
# Должно вывести: /usr/bin/python3

# Windows
where python
# Должно вывести: C:\Python311\python.exe
```

**Решение**: Установите Python 3.11+ с [python.org](https://python.org)

#### Зависимости не устанавливаются

```bash
pip: command not found
```

**Решение**:
```bash
# Linux
sudo apt install python3-pip

# macOS
brew install python3

# Windows
# Переустановите Python с опцией "Add to PATH"
```

### Проблемы с GUI

#### Tkinter не найден (Linux)

```bash
ModuleNotFoundError: No module named '_tkinter'
```

**Решение**:
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# Fedora
sudo dnf install python3-tkinter

# Arch
sudo pacman -S tk
```

#### CustomTkinter не работает

```bash
ImportError: cannot import name 'CTk' from 'customtkinter'
```

**Решение**:
```bash
pip install --upgrade customtkinter
```

#### GUI не отображается в Docker

**Решение Linux**:
```bash
# 1. Разрешить X11
xhost +local:docker

# 2. Проверить DISPLAY
echo $DISPLAY
# Должно быть :0 или :1

# 3. Запустить с правильными параметрами
docker run -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw \
  dsu:latest
```

**Решение Windows**:
```bash
# 1. Установить VcXsrv или X410
# 2. Запустить с "Disable access control"
# 3. Добавить firewall rule

# 4. Запустить контейнер
docker run -e DISPLAY=host.docker.internal:0 dsu:latest
```

### Проблемы с сетью

#### Permission denied для broadcast

```
PermissionError: [Errno 13] Permission denied
```

**Решение**:
```bash
# Запустить с sudo
sudo python3 app_modern.py
```

#### Устройства не обнаруживаются

**Проверка**:
```bash
# 1. Проверить сеть
ip addr show
ifconfig

# 2. Проверить firewall
sudo ufw status
sudo iptables -L

# 3. Проверить порт
sudo netstat -ulnp | grep 1770
```

**Решение**:
```bash
# Открыть порты
sudo ufw allow 1770/udp
sudo ufw allow 1775/udp
```

### Проблемы компиляции

#### Go не найден

```
go: command not found
```

**Решение**: Установите Go с [golang.org](https://golang.org/dl/)

#### PyInstaller ошибки

```
Failed to execute script 'pyi_rth_pkgres'
```

**Решение**:
```bash
# 1. Обновить PyInstaller
pip install --upgrade pyinstaller

# 2. Очистить кэш
rm -rf build/ dist/ __pycache__/

# 3. Пересобрать
pyinstaller --clean DSU.spec
```

---

## 👨‍💻 Разработка

### Настройка окружения

```bash
# 1. Fork репозитория
# 2. Клонирование
git clone https://github.com/YOUR_USERNAME/DSU.git
cd DSU

# 3. Создание ветки
git checkout -b feature/my-feature

# 4. Установка dev зависимостей
pip install -r requirements.txt
pip install pytest black flake8
```

### Запуск тестов

```bash
# Все тесты
pytest

# С coverage
pytest --cov=logic --cov=interface

# Конкретный модуль
pytest test_module/test.py -v
```

### Code style

```bash
# Форматирование
black .

# Линтинг
flake8 logic/ interface/

# Type checking
mypy logic/ interface/
```

### Создание Pull Request

1. Создайте issue с описанием проблемы/фичи
2. Создайте ветку: `git checkout -b feature/issue-123`
3. Коммитьте изменения: `git commit -m "Add feature X"`
4. Push: `git push origin feature/issue-123`
5. Создайте Pull Request

---

## 📜 Лицензия

MIT License - see [LICENSE](LICENSE) file

---

## 🤝 Вклад в проект

Мы приветствуем вклад в проект! См. [CONTRIBUTING.md](CONTRIBUTING.md)

---

## 📞 Контакты

- **Issues**: [GitHub Issues](https://github.com/yourname/DSU/issues)
- **Email**: support@dsu-project.com
- **Telegram**: @dsu_support

---

## 🙏 Благодарности

- CustomTkinter team
- Go community
- All contributors

---

<div align="center">

**[⬆ Наверх](#-dsu---device-setup-utility-v20)**

Made with ❤️ by DSU Team

</div>
