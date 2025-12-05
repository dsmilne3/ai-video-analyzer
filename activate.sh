#!/bin/bash
# AI Video Analyzer - Virtual Environment Setup and Launcher

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$PROJECT_DIR/venv/bin/activate"

# Install/update dependencies if requirements.txt exists
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    pip install -r "$PROJECT_DIR/requirements.txt"
fi

echo "Virtual environment ready!"
echo "To activate manually: source venv/bin/activate"
echo "To run the app: streamlit run app/reviewer.py"
echo "To run CLI: python cli/evaluate_video.py [args]"