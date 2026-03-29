# DSU - Device Setup Utility
# Multi-stage build для оптимизации размера

# Stage 1: Build Go firmware module
FROM golang:1.21-alpine AS go-builder

WORKDIR /build
COPY go-firmware/ ./

RUN go build -o firmware -ldflags="-s -w" firmware.go


# Stage 2: Python application
FROM python:3.11-slim

LABEL maintainer="DSU Team"
LABEL description="Device Setup Utility - Network device management tool"
LABEL version="2.0"

# Установка системных зависимостей
RUN apt-get update && apt-get install -y \
    # GUI dependencies
    libx11-6 \
    libxext6 \
    libxrender1 \
    libxinerama1 \
    libxi6 \
    libxrandr2 \
    libxcursor1 \
    libxcomposite1 \
    libxdamage1 \
    libfontconfig1 \
    libxfixes3 \
    # Network tools
    net-tools \
    iputils-ping \
    # Build dependencies
    gcc \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Рабочая директория
WORKDIR /app

# Копируем requirements
COPY requirements.txt .

# Устанавливаем Python зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем приложение
COPY . .

# Копируем скомпилированный Go бинарник
COPY --from=go-builder /build/firmware /app/go-firmware/firmware
RUN chmod +x /app/go-firmware/firmware

# Создаем non-root пользователя
RUN useradd -m -u 1000 dsu && \
    chown -R dsu:dsu /app

USER dsu

# X11 forwarding
ENV DISPLAY=:0

# Expose UDP ports
EXPOSE 1770/udp
EXPOSE 1775/udp

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python3 -c "import sys; sys.exit(0)"

# Default command - modern UI
CMD ["python3", "app_modern.py"]
