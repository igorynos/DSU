# DSU - Device Setup Utility v2.0

**Профессиональная утилита для обнаружения, настройки и обслуживания сетевых контроллеров**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED.svg)](https://docker.com)

## Возможности

- **Автоматическое обнаружение устройств** через широковещательный UDP протокол
- **Управление настройками** контроллеров (IP, маска, порт, имя)
- **Прошивка устройств** с поддержкой различных моделей
- **Синхронизация времени** с устройствами
- **Тестовые устройства** для разработки и отладки

## Поддерживаемые устройства

- CP-18
- POS
- AP-PRO
- TW-2020

## Установка

Требования:
- Python 3.11+
- (опционально) `keyboard` модуль для отладочных горячих клавиш

```bash
git clone <repository-url>
cd DSU
python3 -m venv .venv
source .venv/bin/activate
pip install .                      # для работы
pip install -e ".[dev]"            # для разработки (с pytest и ruff)
pip install ".[hotkeys]"           # с поддержкой keyboard-hotkeys
```

## Запуск

```bash
dsu                # установлено как консольная команда
python -m dsu      # эквивалент
dsu --debug        # подробное логирование + (если установлено) keyboard-hotkeys
```

Для broadcast UDP может потребоваться запуск с привилегиями: `sudo dsu`.

## Прошивка устройств

```python
from dsu.net.firmware import Firmware

fw = Firmware("firmware.fw")
for packet in fw():
    # отправка пакета на устройство
    ...
```

Модуль прошивки реализован на Python. В будущем (Plan B) будет заменён на C++ через pybind11 для ускорения.

## Архитектура

```
DSU/
├── pyproject.toml          # Метаданные пакета
├── src/dsu/                # Python-пакет
│   ├── __init__.py
│   ├── __main__.py         # `python -m dsu`
│   ├── cli.py              # точка входа `dsu`
│   ├── app.py              # Application + create_app()
│   ├── domain/             # Доменный слой (без сети)
│   │   ├── codec.py        # cp1251/IP конвертеры
│   │   ├── events.py       # EventBus + DevLstEvent
│   │   ├── models.py       # Device dataclass
│   │   └── registry.py     # DeviceRegistry
│   ├── net/                # Сетевой слой
│   │   ├── locator.py      # broadcast UDP (1770)
│   │   ├── eludp.py        # адресный UDP
│   │   ├── cmd_queue.py    # очередь команд
│   │   ├── controller.py   # watchdog + диспетчер пакетов
│   │   └── firmware.py     # обработчик .fw файлов
│   └── config/             # Конфигурация
│       ├── settings.py     # AppConfig + ini-loader
│       └── defaults.ini    # Базовые устройства
└── tests/                  # pytest
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

### Добавление новых устройств

1. Добавьте модель в `DevModel` (`src/dsu/domain/models.py`)
2. Обновите парсинг параметров устройства
3. При необходимости добавьте специфичную логику

## Известные ограничения

### WSL2
- Горячие клавиши (keyboard) не работают
- Broadcast UDP требует sudo

### Linux
- Keyboard модуль требует root прав
- Broadcast UDP требует sudo

## Troubleshooting

### Программа не запускается

```
ImportError: No module named 'netifaces'
```
**Решение**: Установите зависимости: `pip install .`

### Permission denied для broadcast

**Решение**: Запустите с sudo: `sudo dsu`

## Зависимости

Все зависимости описаны в `pyproject.toml`.

- `netifaces` — сетевые интерфейсы (обязательно)
- `keyboard` — горячие клавиши (опционально, через `pip install ".[hotkeys]"`)
- `pytest`, `ruff` — для разработки (через `pip install -e ".[dev]"`)

## Лицензия

[Укажите вашу лицензию]

## Контакты

[Укажите контактную информацию]
