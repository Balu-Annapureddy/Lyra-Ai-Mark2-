"""
Gunicorn configuration for Railway deployment
Optimized for cloud hosting with dynamic port binding
"""

import os
import multiprocessing

# Bind to Railway's PORT environment variable
port = os.environ.get("PORT", "8000")
bind = f"0.0.0.0:{port}"

# Worker configuration
# Railway provides limited resources, so we use fewer workers
workers = int(os.environ.get("WEB_CONCURRENCY", 2))
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "-"  # Log to stdout
errorlog = "-"   # Log to stderr
loglevel = os.environ.get("LOG_LEVEL", "info")

# Process naming
proc_name = "lyra-ai-railway"

# Server mechanics
daemon = False
preload_app = True  # Preload for faster startup

# Restart workers to prevent memory leaks
max_requests = 1000
max_requests_jitter = 50

# Graceful timeout
graceful_timeout = 30

print(f"Starting Lyra AI on port {port} with {workers} workers")
