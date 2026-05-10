# Gunicorn config — v4.0 fix
#
# VẤN ĐỀ CŨ (v3.0):
#   - worker_class = "sync" → time.sleep() trong rate limit BLOCK toàn bộ worker
#   - timeout = 300s nhưng Groq rate limit đôi khi yêu cầu chờ 1500s+
#   → Worker bị SIGKILL → crash loop
#
# FIX:
#   - worker_class = "gevent" → sleep không block, worker vẫn nhận request khác
#   - timeout tăng lên 600s để xử lý các request phân tích nặng
#   - MAX_RATE_LIMIT_SLEEP = 55s trong llm.py đảm bảo không bao giờ vượt timeout

timeout = 600          # 10 phút — đủ cho pipeline CoT 2 bước
workers = 1
worker_class = "gevent"   # Async I/O — sleep không block worker
worker_connections = 20
keepalive = 5
max_requests = 10
max_requests_jitter = 5
