FROM python:3.11-slim-bookworm

WORKDIR /app

# Cài build dependencies
RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Nâng cấp pip
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# === CÀI PANDAS/NUMPY TRƯỚC (không dùng --only-binary) ===
RUN pip install --no-cache-dir numpy==1.26.4 pandas==2.2.2

# === SAU ĐÓ MỚI CÀI CÁC THƯ VIỆN KHÁC ===
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
