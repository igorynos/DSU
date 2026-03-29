# 🚀 Quick Start Guide

Быстрый старт для DSU - от установки до первого запуска за 5 минут!

---

## ⚡ Самый быстрый способ

### Linux/macOS

```bash
# Клонирование и установка
git clone <repo-url> && cd DSU
python3 -m venv venv && source venv/bin/activate
pip install -r requirements.txt

# Запуск современного интерфейса
python3 app_modern.py
```

### Windows

```powershell
# Клонирование и установка
git clone <repo-url>
cd DSU
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt

# Запуск
python app_modern.py
```

---

## 🐳 Docker (самый простой)

```bash
# Сборка и запуск одной командой
docker-compose up

# Или вручную
docker build -t dsu:latest .
docker run --network=host -e DISPLAY=$DISPLAY \
  -v /tmp/.X11-unix:/tmp/.X11-unix:rw dsu:latest
```

---

## 💻 Standalone EXE (Windows)

```bash
# 1. Скачать готовый EXE из Releases
# 2. Запустить DSU.exe
# Готово!
```

Или собрать самостоятельно:
```bash
build_exe.bat
dist\DSU.exe
```

---

## 📱 Первые шаги

### 1. Добавить тестовое устройство

```
Меню → Инструменты → Тестовые устройства → Добавить тестовое устройство
```

### 2. Выбрать устройство

Кликните **"Выбрать"** на карточке устройства

### 3. Изменить настройки

Отредактируйте поля справа и нажмите **"Применить настройки"**

### 4. Прошить устройство

```
1. Выбрать устройство
2. Нажать "Прошить устройство"
3. Выбрать файл .fw
4. Дождаться завершения (прогресс-бар)
```

---

## 🔧 Решение проблем

### GUI не отображается

```bash
# Linux - установить tkinter
sudo apt install python3-tk

# Docker - разрешить X11
xhost +local:docker
```

### Permission denied

```bash
# Запустить с sudo для полного функционала
sudo python3 app_modern.py
```

### Зависимости не устанавливаются

```bash
# Обновить pip
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 📚 Дальше

- **Полная документация**: [README_FULL.md](README_FULL.md)
- **Go модуль**: [go-firmware/README.md](go-firmware/README.md)
- **Benchmarks**: `python3 benchmark_firmware.py firmware.fw`

---

## ✅ Checklist

- [ ] Python 3.11+ установлен
- [ ] Зависимости установлены (`pip install -r requirements.txt`)
- [ ] Go модуль собран (опционально)
- [ ] Приложение запускается
- [ ] Тестовое устройство добавлено
- [ ] Интерфейс работает

**Готово!** 🎉

---

**Проблемы?** → [Issues](https://github.com/yourname/DSU/issues) | [README_FULL.md](README_FULL.md#-troubleshooting)
