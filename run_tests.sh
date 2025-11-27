#!/bin/bash
# Run E2E Smoke Tests
# Requires server to be running on localhost:8000

echo "========================================"
echo "Lyra AI Mark2 - E2E Smoke Tests"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run ./setup_venv.sh first"
    exit 1
fi

# Activate virtual environment
source venv/bin/activate

# Install test dependencies
echo "Installing test dependencies..."
pip install -q -r requirements-test.txt

echo ""
echo "Running smoke tests..."
echo "Make sure the server is running on http://localhost:8000"
echo ""

# Run tests
pytest tests/e2e/test_smoke.py -v --asyncio-mode=auto

# Deactivate
deactivate

echo ""
echo "Tests complete!"
