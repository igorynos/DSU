#!/bin/bash
# Скрипт для компиляции DSU в standalone executable

set -e

echo "======================================"
echo "DSU Build Script"
echo "======================================"

# Проверка виртуального окружения
if [ ! -d "venv" ]; then
    echo "❌ Virtual environment not found. Creating..."
    python3 -m venv venv
fi

# Активация venv
source venv/bin/activate

# Установка зависимостей
echo "📦 Installing dependencies..."
pip install -q --upgrade pip
pip install -q -r requirements.txt

# Сборка Go модуля
echo "🔧 Building Go firmware module..."
cd go-firmware
if command -v go &> /dev/null; then
    go build -o firmware -ldflags="-s -w" firmware.go
    echo "✅ Go module built successfully"
else
    echo "⚠️  Go not found, skipping firmware module build"
fi
cd ..

# Создание директории для ресурсов
mkdir -p assets

# Компиляция с PyInstaller
echo "🏗️  Building executable..."
pyinstaller --clean --noconfirm DSU.spec

# Проверка результата
if [ -f "dist/DSU" ] || [ -f "dist/DSU.exe" ]; then
    echo "✅ Build successful!"
    echo ""
    echo "Executable location:"
    ls -lh dist/DSU* 2>/dev/null || ls -lh dist/DSU.exe 2>/dev/null
    echo ""
    echo "To run: ./dist/DSU"
else
    echo "❌ Build failed!"
    exit 1
fi

echo ""
echo "======================================"
echo "Build complete!"
echo "======================================"
