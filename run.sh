#!/bin/bash
# AI Video Analyzer - Run Scripts

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$SCRIPT_DIR"

# Function to activate virtual environment
activate_venv() {
    if [ ! -d "$PROJECT_DIR/venv" ]; then
        echo "Virtual environment not found. Run ./activate.sh first."
        exit 1
    fi
    source "$PROJECT_DIR/venv/bin/activate"
}

# Check command
case "$1" in
    "app"|"web"|"streamlit")
        activate_venv
        echo "Starting Streamlit app..."
        streamlit run Home.py
        ;;
    "test")
        activate_venv
        echo "Running tests..."
        python -m pytest tests/ -v
        ;;
    "demo")
        activate_venv
        echo "Running end-to-end demo..."
        python test_data/run_end_to_end_demo.py
        ;;
    "check")
        activate_venv
        echo "Running dependency check..."
        python check_dependencies.py
        ;;
    "chunking-test")
        activate_venv
        echo "Testing chunking evaluation fixes..."
        python test_chunking_fix.py
        ;;
    *)
        echo "Usage: $0 {app|test|demo|check|chunking-test}"
        echo ""
        echo "Commands:"
        echo "  app           - Start the Streamlit web interface"
        echo "  test          - Run the test suite"
        echo "  demo          - Run the end-to-end demo"
        echo "  check         - Check system dependencies"
        echo "  chunking-test - Test chunking evaluation fixes (requires API keys)"
        echo ""
        echo "Make sure to run ./activate.sh first to set up the virtual environment."
        exit 1
        ;;
esac