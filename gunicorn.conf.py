import os

bind = f"0.0.0.0:{os.getenv('PORT', '5000')}"
workers = 4
worker_class = "sync"
timeout = 120
keepalive = 5
max_requests = 1000
max_requests_jitter = 50
