FROM python:3.11-slim-bookworm

WORKDIR /app

RUN apt-get update && apt-get install -y gcc g++ python3-dev && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:10000", "--workers", "2", "--timeout", "120"]
