FROM python:3.11-slim

WORKDIR /app

# Cài system dependencies quan trọng để build pandas/numpy
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements trước để cache layer
COPY requirements.txt .

# Cài pandas với wheel trước, tránh build từ source
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir wheel numpy==1.26.4 \
    && pip install --no-cache-dir pandas==2.2.2

# Cài các package còn lại
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
