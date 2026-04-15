FROM python:3.11-slim-bookworm

WORKDIR /app

# Cài đặt các công cụ build cần thiết
RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Nâng cấp pip
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# === BƯỚC 1: Cài pandas và numpy từ binary wheels ===
RUN pip install --no-cache-dir --only-binary :all: numpy==1.26.4 pandas==2.2.2

# === BƯỚC 2: Copy và cài requirements.txt (KHÔNG chứa pandas/numpy) ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy toàn bộ code
COPY . .

EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
