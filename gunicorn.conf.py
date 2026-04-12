# Gunicorn config
timeout = 300  # 5 phút
workers = 1
worker_class = "sync"
keepalive = 5
max_requests = 10
max_requests_jitter = 5
