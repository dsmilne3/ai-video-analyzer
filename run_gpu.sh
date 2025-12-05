#!/bin/bash
# GPU Detection and Docker Configuration Script
# This script detects available GPUs and configures Docker accordingly

set -e

# Check for dry-run flag
DRY_RUN=false
if [ "$1" = "--dry-run" ]; then
    DRY_RUN=true
    echo "🔍 Dry-run mode: Detecting GPU availability (no Docker commands will be executed)..."
else
    echo "🔍 Detecting GPU availability..."
fi

# Function to check for NVIDIA GPU
check_nvidia() {
    if command -v nvidia-smi &> /dev/null; then
        echo "✅ NVIDIA GPU detected"
        GPU_COUNT=$(nvidia-smi --list-gpus | wc -l)
        echo "   Found $GPU_COUNT NVIDIA GPU(s)"
        return 0
    fi
    return 1
}

# Function to check for AMD GPU
check_amd() {
    if command -v rocminfo &> /dev/null || lspci 2>/dev/null | grep -i amd &> /dev/null; then
        echo "✅ AMD GPU detected"
        return 0
    fi
    return 1
}

# Function to check for Apple Silicon
check_apple_silicon() {
    if [[ "$OSTYPE" == "darwin"* ]] && sysctl -n machdep.cpu.brand_string 2>/dev/null | grep -i apple &> /dev/null; then
        echo "✅ Apple Silicon detected (M1/M2/M3)"
        return 0
    fi
    return 1
}

# Detect GPU type
GPU_TYPE="cpu"
TORCH_VARIANT="cpu"
GPU_COUNT=0

if check_nvidia; then
    GPU_TYPE="nvidia"
    TORCH_VARIANT="cuda"
    GPU_COUNT=$GPU_COUNT
elif check_amd; then
    GPU_TYPE="amd"
    TORCH_VARIANT="rocm"
elif check_apple_silicon; then
    GPU_TYPE="apple"
    TORCH_VARIANT="cpu"  # Docker doesn't support MPS directly
else
    echo "⚠️  No GPU detected, using CPU-only mode"
fi

# Create GPU override file if GPUs are available
if [ "$GPU_COUNT" -gt 0 ] && [ "$GPU_TYPE" = "nvidia" ]; then
    cat > docker-compose.override.yml << EOF
services:
  ai-video-analyzer:
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: $GPU_COUNT
              capabilities: [gpu]
EOF
    echo "📄 Created GPU override configuration"
else
    # Remove any existing override file
    rm -f docker-compose.override.yml
    echo "📄 No GPU override needed (using CPU)"
fi

# Create or update .env file with GPU settings
if [ ! -f .env ]; then
    touch .env
fi

# Update or add GPU-related environment variables
if ! grep -q "^TORCH_VARIANT=" .env 2>/dev/null; then
    echo "TORCH_VARIANT=$TORCH_VARIANT" >> .env
else
    sed -i.bak "s/^TORCH_VARIANT=.*/TORCH_VARIANT=$TORCH_VARIANT/" .env
fi

if ! grep -q "^GPU_COUNT=" .env 2>/dev/null; then
    echo "GPU_COUNT=$GPU_COUNT" >> .env
else
    sed -i.bak "s/^GPU_COUNT=.*/GPU_COUNT=$GPU_COUNT/" .env
fi

echo ""
echo "🚀 Starting Docker container with GPU support..."

# Check if docker-compose is available
if command -v docker-compose &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker-compose"
elif docker compose version &> /dev/null; then
    DOCKER_COMPOSE_CMD="docker compose"
else
    echo "❌ Neither docker-compose nor 'docker compose' found."
    echo ""
    echo "Installation instructions:"
    echo "1. Install Docker Desktop: https://www.docker.com/products/docker-desktop"
    echo "2. Or install docker-compose: https://docs.docker.com/compose/install/"
    echo ""
    echo "For Apple Silicon users, run natively for GPU acceleration:"
    echo "  ./activate.sh"
    echo "  streamlit run Home.py"
    exit 1
fi

# Build and run with GPU configuration
if [ "$DRY_RUN" = true ]; then
    echo ""
    echo "🔧 Dry-run complete. To start the container, run:"
    echo "   ./run_gpu.sh"
    echo ""
    echo "Configuration that would be used:"
    echo "   TORCH_VARIANT=$TORCH_VARIANT"
    echo "   GPU_COUNT=$GPU_COUNT"
    echo "   GPU_TYPE=$GPU_TYPE"
else
    if [ "$GPU_TYPE" = "nvidia" ]; then
        echo "Using NVIDIA Container Toolkit..."
        $DOCKER_COMPOSE_CMD up --build
    elif [ "$GPU_TYPE" = "apple" ]; then
        echo "Note: Apple Silicon MPS acceleration not available in Docker."
        echo "For best performance, run the application natively on macOS."
        echo "Continuing with CPU-only Docker container..."
        $DOCKER_COMPOSE_CMD up --build
    else
        $DOCKER_COMPOSE_CMD up --build
    fi
fi