FROM python:3.11-bookworm

WORKDIR /app

# Cài đầy đủ dependencies để build
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

# Upgrade pip và cài wheel + Cython cũ (quan trọng nhất)
RUN pip install --no-cache-dir --upgrade pip wheel setuptools \
    && pip install --no-cache-dir "Cython<3.0"  # Dùng Cython 0.29.x để tránh lỗi attribute

# Cài numpy + pandas trước bằng wheel (rất quan trọng)
RUN pip install --no-cache-dir numpy==1.26.4 pandas==2.2.2

# Copy và cài requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
