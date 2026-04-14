# Sử dụng bản 3.11 để có đầy đủ thư viện hỗ trợ (Wheels)
FROM python:3.11-slim-bookworm

WORKDIR /app

# Cài đặt các công cụ cần thiết cho hệ thống
RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Nâng cấp pip để đảm bảo tìm được bản binary mới nhất
RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# BƯỚC QUAN TRỌNG: Ép cài Pandas và Numpy từ bản build sẵn (binary)
# Điều này giúp tránh lỗi "standard attributes in middle of decl-specifiers" của Python 3.14
RUN pip install --no-cache-dir --only-binary :all: numpy==1.26.4 pandas==2.2.2

# Cài các thư viện còn lại
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render dùng biến môi trường PORT, thường là 10000
EXPOSE 10000

# Sử dụng dạng shell để biến $PORT được nhận diện chính xác
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
