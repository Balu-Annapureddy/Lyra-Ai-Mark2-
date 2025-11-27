#!/bin/bash

echo "========================================"
echo "Lyra AI Mark2 - Virtual Environment Setup"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "ERROR: Python 3 is not installed"
    echo "Please install Python 3.9+ from your package manager"
    exit 1
fi

# Check RAM (basic check)
echo "Checking system RAM..."
if command -v free &> /dev/null; then
    total_ram=$(free -g | awk '/^Mem:/{print $2}')
    echo "Detected RAM: ${total_ram}GB"
    if [ "$total_ram" -lt 8 ]; then
        echo "WARNING: Less than 8GB RAM detected. Lyra will use low-power mode."
    fi
else
    echo "WARNING: Could not detect RAM. Proceeding anyway..."
fi

# Create virtual environment
echo ""
echo "Creating virtual environment..."
if [ -d "venv" ]; then
    echo "Virtual environment already exists. Skipping creation."
else
    python3 -m venv venv
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "Virtual environment created successfully."
fi

# Activate virtual environment
echo ""
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo ""
echo "Upgrading pip..."
python -m pip install --upgrade pip

# Install lightweight dependencies
echo ""
echo "Installing lightweight dependencies..."
if [ -f "requirements-lightweight.txt" ]; then
    pip install -r requirements-lightweight.txt
else
    echo "WARNING: requirements-lightweight.txt not found"
    echo "Installing from requirements.txt instead..."
    if [ -f "requirements.txt" ]; then
        pip install -r requirements.txt
    else
        echo "ERROR: No requirements file found"
        exit 1
    fi
fi

echo ""
echo "========================================"
echo "Setup Complete!"
echo "========================================"
echo ""
echo "Virtual environment is ready at: $(pwd)/venv"
echo ""
echo "To activate the virtual environment:"
echo "  source venv/bin/activate"
echo ""
echo "To start the backend:"
echo "  python app.py"
echo ""
