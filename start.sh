#!/bin/bash
# Quick Start Script for Lyra AI Mark2
# Activates virtual environment and starts the application

echo "========================================"
echo "Lyra AI Mark2 - Quick Start"
echo "========================================"
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo "ERROR: Virtual environment not found!"
    echo "Please run ./setup_venv.sh first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi

echo ""
echo "Starting Lyra AI Mark2..."
echo "Server will be available at: http://localhost:8000"
echo "Health check: http://localhost:8000/health/"
echo ""

# Start the application
cd ai-worker
python app.py

# Deactivate on exit
deactivate
