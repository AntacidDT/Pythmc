#!/bin/bash
# Pythmc - Minecraft Clone
# Just run: ./run.sh

echo "Starting Pythmc..."
echo ""

# Get script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
cd "$SCRIPT_DIR"

# Try python3 first, then python
if command -v python3 &> /dev/null; then
    python3 run.py
elif command -v python &> /dev/null; then
    python run.py
else
    echo "Python not found!"
    echo "Install Python 3.8+ from python.org"
    exit 1
fi
