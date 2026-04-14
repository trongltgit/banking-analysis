FROM python:3.11-bookworm   # Dùng bookworm thay vì slim để có nhiều thư viện hơn

WORKDIR /app

# Cài đầy đủ build dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    libpq-dev \
    libssl-dev \
    libffi-dev \
    build-essential \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip và cài wheel trước
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Cài pandas + numpy bằng wheel trước để tránh build từ source
RUN pip install --no-cache-dir \
    numpy==1.26.4 \
    pandas==2.2.2

# Cài các package còn lại
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy code
COPY . .

EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
