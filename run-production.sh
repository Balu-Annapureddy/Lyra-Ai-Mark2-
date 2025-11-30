#!/bin/bash
# Lyra AI Mark2 - Production Run Script (Linux)
# Starts the application with optimal production settings

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "========================================"
echo "Lyra AI Mark2 - Production Startup"
echo "========================================"
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${RED}ERROR: Virtual environment not found${NC}"
    echo "Please run setup first or create venv manually"
    exit 1
fi

# Activate virtual environment
echo "[1/5] Activating virtual environment..."
source venv/bin/activate
echo -e "${GREEN}✓ Virtual environment activated${NC}"
echo ""

# Check Python version
echo "[2/5] Checking Python version..."
PYTHON_VERSION=$(python3 --version 2>&1 | awk '{print $2}')
echo "Python version: $PYTHON_VERSION"
echo ""

# Auto-detect CPU/GPU configuration
echo "[3/5] Detecting hardware configuration..."

# Detect CPU cores
CPU_CORES=$(nproc)
echo "CPU Cores: $CPU_CORES"

# Calculate optimal worker count: (2 × CPU cores) + 1
WORKERS=$((2 * CPU_CORES + 1))
echo "Recommended workers: $WORKERS"

# Detect GPU
GPU_AVAILABLE=false
if command -v nvidia-smi &> /dev/null; then
    if nvidia-smi &> /dev/null; then
        GPU_AVAILABLE=true
        GPU_NAME=$(nvidia-smi --query-gpu=name --format=csv,noheader | head -n 1)
        echo -e "${GREEN}✓ GPU detected: $GPU_NAME${NC}"
    fi
fi

if [ "$GPU_AVAILABLE" = false ]; then
    echo -e "${YELLOW}⚠ No GPU detected, running in CPU mode${NC}"
fi
echo ""

# Check if Gunicorn is installed
echo "[4/5] Checking Gunicorn installation..."
if ! python -c "import gunicorn" &> /dev/null; then
    echo -e "${YELLOW}⚠ Gunicorn not found, installing...${NC}"
    pip install gunicorn
fi
echo -e "${GREEN}✓ Gunicorn ready${NC}"
echo ""

# Create necessary directories
mkdir -p ai-worker/logs
mkdir -p ai-worker/cache
mkdir -p ai-worker/state
mkdir -p ai-worker/config

# Start production server
echo "[5/5] Starting production server..."
echo "Workers: $WORKERS"
echo "Bind: 0.0.0.0:8000"
echo "Worker class: uvicorn.workers.UvicornWorker"
echo ""

cd ai-worker

# Create Gunicorn configuration on-the-fly
cat > gunicorn_config_auto.py << EOF
import multiprocessing

# Server socket
bind = "0.0.0.0:8000"
backlog = 2048

# Worker processes
workers = $WORKERS
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

# Restart workers after this many requests (prevent memory leaks)
max_requests = 1000
max_requests_jitter = 50
EOF

echo -e "${GREEN}========================================"
echo "Starting Lyra AI Mark2..."
echo "========================================${NC}"
echo ""
echo "Access the application at: http://localhost:8000"
echo "Health check: http://localhost:8000/health"
echo "Status: http://localhost:8000/status"
echo ""
echo "Press Ctrl+C to stop"
echo ""

# Start Gunicorn with auto-restart on failure
while true; do
    gunicorn -c gunicorn_config_auto.py app:app || {
        echo -e "${RED}Server crashed! Restarting in 5 seconds...${NC}"
        sleep 5
    }
done
