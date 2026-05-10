# Gunicorn config
timeout = 600
workers = 1
worker_class = "gthread"
threads = 4
keepalive = 5
max_requests = 10
max_requests_jitter = 5
