FROM python:3.11-slim-bookworm

WORKDIR /app

# Install build essentials for any other C-extensions
RUN apt-get update && apt-get install -y \
    gcc g++ python3-dev \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir --upgrade pip wheel setuptools

# Pre-install the "heavy" libraries as binaries
RUN pip install --no-cache-dir --only-binary :all: numpy==1.26.4 pandas==2.2.2

COPY requirements.txt .
# Use a grep trick to install everything EXCEPT pandas/numpy if they are still in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Render expects the app to listen on the port they provide
EXPOSE 10000

# Using shell form to ensure $PORT is expanded
CMD gunicorn app:app --bind 0.0.0.0:$PORT --workers 2 --timeout 120
