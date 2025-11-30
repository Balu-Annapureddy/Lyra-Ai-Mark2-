# Lyra AI Mark2 - Deployment Guide

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation](#installation)
3. [Production Server Setup](#production-server-setup)
4. [Scaling Guide](#scaling-guide)
5. [Failure Recovery](#failure-recovery)
6. [Development vs Production](#development-vs-production)

---

## System Requirements

### Minimum Requirements
- **Python**: 3.10 or higher
- **RAM**: 8GB minimum
- **Disk Space**: 20GB (for models and cache)
- **OS**: Windows 10/11, Ubuntu 20.04+, macOS 12+

### Recommended Requirements
- **Python**: 3.11+
- **RAM**: 16GB or higher
- **GPU**: NVIDIA GPU with CUDA 11.8+ (optional, CPU fallback available)
- **Disk Space**: 50GB+ SSD
- **OS**: Ubuntu 22.04 LTS (for production)

### GPU Requirements (Optional)
- **NVIDIA GPU** with Compute Capability 7.0+
- **CUDA**: 11.8 or higher
- **cuDNN**: 8.6 or higher
- **VRAM**: 4GB minimum, 8GB+ recommended

---

## Installation

### 1. Clone Repository
```bash
git clone https://github.com/yourusername/Lyra-Mark2.git
cd Lyra-Mark2
```

### 2. Create Virtual Environment

**Windows:**
```bash
python -m venv venv
.\venv\Scripts\activate
```

**Linux/macOS:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 4. Verify GPU (Optional)
```bash
python -c "import torch; print(f'CUDA Available: {torch.cuda.is_available()}')"
```

### 5. Configure Environment Variables

Create `.env` file in the root directory:
```bash
# Application Settings
LYRA_ENV=production
LYRA_HOST=0.0.0.0
LYRA_PORT=8000

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/lyra.log

# Cache Settings
CACHE_DIR=ai-worker/cache
CACHE_MAX_SIZE_GB=50

# Performance
MAX_WORKERS=4
MEMORY_LIMIT_PERCENT=85

# Security (Production)
ALLOWED_ORIGINS=https://yourdomain.com,https://www.yourdomain.com
SECRET_KEY=your-secret-key-here
```

### 6. Initialize Application
```bash
cd ai-worker
python app.py
```

Verify at: `http://localhost:8000`

---

## Production Server Setup

### Option 1: Gunicorn + Uvicorn Workers (Recommended)

#### 1. Install Gunicorn
```bash
pip install gunicorn
```

#### 2. Create Gunicorn Configuration

Create `gunicorn_config.py`:
```python
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "uvicorn.workers.UvicornWorker"
worker_connections = 1000
timeout = 120
keepalive = 5

# Logging
accesslog = "logs/access.log"
errorlog = "logs/error.log"
loglevel = "info"

# Process naming
proc_name = "lyra-ai-mark2"

# Server mechanics
daemon = False
pidfile = "lyra.pid"
umask = 0
user = None
group = None
tmp_upload_dir = None

# SSL (if not using Nginx)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

#### 3. Start Production Server
```bash
gunicorn -c gunicorn_config.py app:app
```

### Option 2: Systemd Service (Linux)

#### 1. Create Service File

Create `/etc/systemd/system/lyra-ai.service`:
```ini
[Unit]
Description=Lyra AI Mark2 Application
After=network.target

[Service]
Type=notify
User=lyra
Group=lyra
WorkingDirectory=/opt/lyra-mark2/ai-worker
Environment="PATH=/opt/lyra-mark2/venv/bin"
ExecStart=/opt/lyra-mark2/venv/bin/gunicorn -c /opt/lyra-mark2/gunicorn_config.py app:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### 2. Enable and Start Service
```bash
sudo systemctl daemon-reload
sudo systemctl enable lyra-ai
sudo systemctl start lyra-ai
sudo systemctl status lyra-ai
```

#### 3. View Logs
```bash
sudo journalctl -u lyra-ai -f
```

### Option 3: Nginx Reverse Proxy

#### 1. Install Nginx
```bash
sudo apt update
sudo apt install nginx
```

#### 2. Create Nginx Configuration

Create `/etc/nginx/sites-available/lyra-ai`:
```nginx
upstream lyra_backend {
    server 127.0.0.1:8000;
    keepalive 32;
}

server {
    listen 80;
    server_name yourdomain.com www.yourdomain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name yourdomain.com www.yourdomain.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/yourdomain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/yourdomain.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;
    ssl_prefer_server_ciphers on;
    
    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Logging
    access_log /var/log/nginx/lyra-access.log;
    error_log /var/log/nginx/lyra-error.log;
    
    # Max upload size
    client_max_body_size 100M;
    
    # Proxy settings
    location / {
        proxy_pass http://lyra_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_buffering off;
        proxy_request_buffering off;
        proxy_read_timeout 300s;
        proxy_connect_timeout 75s;
    }
    
    # WebSocket support
    location /events/ws {
        proxy_pass http://lyra_backend;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_read_timeout 86400;
    }
    
    # Health check endpoint
    location /health {
        proxy_pass http://lyra_backend;
        access_log off;
    }
}
```

#### 3. Enable Site and Restart Nginx
```bash
sudo ln -s /etc/nginx/sites-available/lyra-ai /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl restart nginx
```

### Option 4: SSL/TLS with Certbot

#### 1. Install Certbot
```bash
sudo apt install certbot python3-certbot-nginx
```

#### 2. Obtain Certificate
```bash
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

#### 3. Auto-renewal
```bash
sudo certbot renew --dry-run
```

---

## Scaling Guide

### Worker Count Recommendations

**Formula**: `workers = (2 × CPU cores) + 1`

| CPU Cores | Recommended Workers |
|-----------|---------------------|
| 2         | 5                   |
| 4         | 9                   |
| 8         | 17                  |
| 16        | 33                  |

### Multi-Model Caching Strategy

1. **Pin Critical Models**:
```python
from core.managers.cache_manager import get_cache_manager

cache_mgr = get_cache_manager()
cache_mgr.pin_model("phi-3-mini", reason="primary_model")
```

2. **Adjust Cache Size**:
```python
# In config or environment
CACHE_MAX_SIZE_GB=100  # Increase for more models
```

3. **Monitor Cache Metrics**:
```bash
curl http://localhost:8000/status | jq '.cache'
```

### Handling 10+ Concurrent Models

1. **Increase Memory Limits**:
   - RAM: 32GB+ recommended
   - Swap: 16GB minimum

2. **Use Model Quantization**:
   - 4-bit or 8-bit quantized models
   - Reduces memory footprint by 50-75%

3. **Implement Model Rotation**:
   - Unload least-used models automatically
   - Configure via `lazy_loader` auto-unload

### Horizontal Scaling

#### Load Balancer Setup (Nginx)

```nginx
upstream lyra_cluster {
    least_conn;
    server 192.168.1.10:8000 weight=1;
    server 192.168.1.11:8000 weight=1;
    server 192.168.1.12:8000 weight=1;
}

server {
    listen 80;
    location / {
        proxy_pass http://lyra_cluster;
    }
}
```

#### Shared Cache Strategy
- Use NFS or distributed file system for cache
- Mount shared cache directory on all nodes
- Configure cache locking to prevent conflicts

---

## Failure Recovery

### CrashRecoveryManager Configuration

The application automatically detects crashes and restores state.

#### Enable Crash Recovery
```python
from core.crash_recovery import get_crash_recovery_manager

recovery_mgr = get_crash_recovery_manager()
recovery_mgr.mark_running()  # Mark app as running
recovery_mgr.start_scheduled_saves()  # Auto-save state every 60s
```

#### State Restoration on Restart
```python
# On startup
if recovery_mgr.detect_crash():
    print("Previous crash detected, restoring state...")
    recovery_mgr.restore_state()
    recovery_mgr.cleanup_gpu_vram()
```

#### Clean Shutdown
```python
# On graceful shutdown
recovery_mgr.mark_clean_shutdown()
```

### Warm Cache Strategy

Pre-load frequently used models on startup:

```python
from core.lazy_loader import get_lazy_loader

loader = get_lazy_loader()

# Pre-load models
models_to_preload = ["phi-3-mini", "llama-3-8b"]
for model_id in models_to_preload:
    loader.load_model(model_id)
```

### Health Check Endpoints

Monitor application health:

```bash
# Quick health check
curl http://localhost:8000/health

# Detailed status
curl http://localhost:8000/status

# Component health
curl http://localhost:8000/health/checks
```

---

## Development vs Production

### Key Differences

| Feature | Development | Production |
|---------|-------------|------------|
| **Debug Mode** | Enabled | Disabled |
| **Hot Reload** | Enabled | Disabled |
| **CORS** | `*` (all origins) | Specific domains |
| **Logging** | DEBUG level | INFO/WARNING |
| **Workers** | 1 | Multiple |
| **SSL/TLS** | Optional | Required |
| **Error Details** | Full stack traces | Generic messages |

### Development Setup

```bash
# Run with hot reload
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

### Production Checklist

- [ ] Disable debug mode
- [ ] Configure specific CORS origins
- [ ] Set `LOG_LEVEL=INFO` or `WARNING`
- [ ] Use Gunicorn with multiple workers
- [ ] Enable SSL/TLS (HTTPS)
- [ ] Set strong `SECRET_KEY`
- [ ] Configure firewall rules
- [ ] Set up log rotation
- [ ] Enable rate limiting
- [ ] Configure monitoring/alerting
- [ ] Set up automated backups
- [ ] Test crash recovery
- [ ] Load test application

### Security Hardening

1. **Environment Variables**: Never commit `.env` to version control
2. **API Keys**: Rotate regularly, use secrets management
3. **Rate Limiting**: Implement per-IP rate limits
4. **Input Validation**: Validate all user inputs
5. **HTTPS Only**: Redirect all HTTP to HTTPS
6. **Security Headers**: Enable CSP, HSTS, X-Frame-Options
7. **Regular Updates**: Keep dependencies updated

---

## Monitoring and Maintenance

### Log Rotation

Create `/etc/logrotate.d/lyra-ai`:
```
/opt/lyra-mark2/logs/*.log {
    daily
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 lyra lyra
    sharedscripts
    postrotate
        systemctl reload lyra-ai > /dev/null 2>&1 || true
    endscript
}
```

### Performance Monitoring

Monitor key metrics:
```bash
# CPU and Memory
htop

# Disk I/O
iotop

# Network
iftop

# Application metrics
curl http://localhost:8000/status | jq '.warnings, .fallbacks, .cache'
```

### Backup Strategy

1. **Configuration**: Daily backups of `.env` and config files
2. **Cache**: Weekly backups of model cache
3. **State**: Automated state snapshots every hour
4. **Logs**: Retain for 30 days minimum

---

## Troubleshooting

### Common Issues

**Issue**: Application won't start
- Check logs: `sudo journalctl -u lyra-ai -n 50`
- Verify Python version: `python --version`
- Check port availability: `sudo lsof -i :8000`

**Issue**: High memory usage
- Check `/status` for warnings
- Review cache size: `/status` → `cache.size_mb`
- Reduce `CACHE_MAX_SIZE_GB`

**Issue**: Slow response times
- Check `/status` → `warnings` for slow tasks
- Increase worker count
- Enable GPU acceleration

**Issue**: WebSocket disconnects
- Check Nginx timeout settings
- Increase `proxy_read_timeout`
- Monitor `/status` → `fallbacks.websocket_disconnects`

---

## Support

For issues and questions:
- GitHub Issues: https://github.com/yourusername/Lyra-Mark2/issues
- Documentation: https://docs.lyra-ai.com
- Community: https://discord.gg/lyra-ai
