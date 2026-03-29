@echo off
REM Скрипт для компиляции DSU в EXE на Windows

echo ======================================
echo DSU Build Script for Windows
echo ======================================

REM Проверка Python
python --version >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found! Please install Python 3.11+
    exit /b 1
)

REM Проверка виртуального окружения
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
)

REM Активация venv
call venv\Scripts\activate.bat

REM Установка зависимостей
echo Installing dependencies...
pip install --upgrade pip --quiet
pip install -r requirements.txt --quiet

REM Сборка Go модуля
echo Building Go firmware module...
cd go-firmware
where go >nul 2>&1
if not errorlevel 1 (
    go build -o firmware.exe -ldflags="-s -w" firmware.go
    echo [OK] Go module built successfully
) else (
    echo [WARNING] Go not found, skipping firmware module
)
cd ..

REM Создание директории для ресурсов
if not exist "assets" mkdir assets

REM Компиляция с PyInstaller
echo Building executable...
pyinstaller --clean --noconfirm DSU.spec

REM Проверка результата
if exist "dist\DSU.exe" (
    echo [SUCCESS] Build complete!
    echo.
    echo Executable location:
    dir dist\DSU.exe
    echo.
    echo To run: dist\DSU.exe
) else (
    echo [ERROR] Build failed!
    exit /b 1
)

echo.
echo ======================================
echo Build complete!
echo ======================================
pause
