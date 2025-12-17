#!/bin/bash
# AI Video Analyzer - Virtual Environment Setup and Launcher

# Determine script directory in a shell-friendly way
# Fall back gracefully if not running under bash
if [ -n "$BASH_VERSION" ]; then
    SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
else
    # When sourced from shells like zsh, BASH_SOURCE may be empty.
    # Use the directory of this file as seen by the current shell.
    SCRIPT_DIR="$(cd "$(dirname "$0")" 2>/dev/null || pwd)"
fi
PROJECT_DIR="$SCRIPT_DIR"

# Detect if this script is being sourced or executed
SOURCED=0
if [ -n "$ZSH_VERSION" ]; then
    case $ZSH_EVAL_CONTEXT in
        *:file) SOURCED=1 ;;
        *)      SOURCED=0 ;;
    esac
elif [ -n "$BASH_VERSION" ]; then
    if [ "${BASH_SOURCE[0]}" != "$0" ]; then
        SOURCED=1
    fi
else
    # POSIX-ish fallback: 'return' only works when sourced
    (return 0 2>/dev/null) && SOURCED=1 || SOURCED=0
fi

# Ensure virtual environment exists
if [ ! -d "$PROJECT_DIR/venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$PROJECT_DIR/venv"
fi

# Decide how to install deps and whether to activate
if [ "$SOURCED" -eq 1 ]; then
    echo "Activating virtual environment..."
    . "$PROJECT_DIR/venv/bin/activate"
    PIP_CMD="pip"
else
    echo "Note: activate.sh was executed, not sourced."
    echo "Dependencies will be installed, but activation won't persist."
    echo "To activate in your current shell, run: source activate.sh"
    PIP_CMD="$PROJECT_DIR/venv/bin/pip"
fi

# Install/update dependencies if requirements.txt exists
if [ -f "$PROJECT_DIR/requirements.txt" ]; then
    echo "Installing/updating dependencies..."
    "$PIP_CMD" install -r "$PROJECT_DIR/requirements.txt"
fi

if [ "$SOURCED" -eq 1 ]; then
    echo "Virtual environment activated. You're ready to go!"
else
    echo "Virtual environment prepared. Activate with: source activate.sh"
fi
echo "Tip: Run ./run.sh check to verify dependencies"