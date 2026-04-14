FROM python:3.11-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev build-essential \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip wheel setuptools "Cython<3.0"

# Cài pandas bằng binary wheel (không compile source)
RUN pip install --no-cache-dir --no-build-isolation --only-binary :all: \
    numpy==1.26.4 pandas==2.2.2

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:$PORT", "--workers", "2", "--timeout", "120"]
