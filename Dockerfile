FROM python:3.11-bookworm

WORKDIR /app

# Cài system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip và cài Cython cũ + wheel
RUN pip install --no-cache-dir --upgrade pip wheel setuptools \
    && pip install --no-cache-dir "Cython<3.0" numpy==1.26.4

# BUỘC CÀI PANDAS BẰNG WHEEL, KHÔNG CHO BUILD TỪ SOURCE
RUN pip install --no-cache-dir --no-build-isolation --no-deps pandas==2.2.2

# Cài các package còn lại
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
