# GPU Acceleration Guide

This guide explains how to enable GPU acceleration for faster video processing in the AI Video Analyzer.

## Supported GPUs

### NVIDIA GPUs (CUDA)

- **Requirements**: NVIDIA drivers and NVIDIA Container Toolkit
- **PyTorch**: CUDA 12.1 support
- **Performance**: 5-10x faster than CPU for Whisper transcription

### AMD GPUs (ROCm)

- **Requirements**: ROCm drivers and compatible AMD GPU
- **PyTorch**: ROCm 6.0 support
- **Performance**: 3-8x faster than CPU

### Apple Silicon (MPS)

- **Requirements**: macOS with Apple Silicon (M1/M2/M3)
- **PyTorch**: Metal Performance Shaders
- **Performance**: 2-4x faster than CPU
- **Note**: MPS acceleration only available when running natively, not in Docker

## Quick Start

### Automatic GPU Detection

```bash
# Option 1: Detect GPU and start Docker container
./run_gpu.sh

# Option 2: Detect GPU and configure .env without starting Docker
./run_gpu.sh --dry-run
```

This script automatically detects your GPU type and count, creates the necessary Docker configuration, and updates your `.env` file with GPU settings.

### Manual Configuration

#### For NVIDIA GPUs:

1. Install NVIDIA Container Toolkit:

   ```bash
   # Ubuntu/Debian
   distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
   curl -s -L https://nvidia.github.io/nvidia-docker/gpgkey | sudo apt-key add -
   curl -s -L https://nvidia.github.io/nvidia-docker/$distribution/nvidia-docker.list | sudo tee /etc/apt/sources.list.d/nvidia-docker.list
   sudo apt-get update && sudo apt-get install -y nvidia-docker2
   sudo systemctl restart docker
   ```

2. Run with GPU:
   ```bash
   export TORCH_VARIANT=cuda
   export GPU_COUNT=1  # or number of GPUs
   docker-compose up --build
   ```

#### For AMD GPUs:

```bash
export TORCH_VARIANT=rocm
docker-compose up --build
```

#### For Apple Silicon:

Run natively (not in Docker) for MPS acceleration:

```bash
./activate.sh
streamlit run Home.py
```

## Performance Comparison

| Configuration     | Whisper Medium | PyTorch Inference | Overall Speedup   |
| ----------------- | -------------- | ----------------- | ----------------- |
| CPU Only          | ~30s           | ~10s              | 1x (baseline)     |
| NVIDIA RTX 3080   | ~3s            | ~1s               | ~8-10x            |
| AMD RX 6800       | ~5s            | ~2s               | ~5-6x             |
| Apple M2 (native) | ~8s            | ~3s               | ~3-4x             |
| Apple M2 (Docker) | ~30s           | ~10s              | 1x (CPU fallback) |

## Troubleshooting

### NVIDIA Issues

- **Error**: `nvidia-container-runtime not found`

  - Solution: Install NVIDIA Container Toolkit as shown above

- **Error**: `CUDA out of memory`
  - Solution: Reduce batch size or use smaller Whisper model

### AMD Issues

- **Error**: `ROCm not supported`
  - Solution: Check if your AMD GPU supports ROCm 6.0+

### Apple Silicon Issues

- **Docker limitation**: MPS not available in containers
  - Solution: Run natively for GPU acceleration

### General Issues

- **Container won't start**: Check GPU_COUNT environment variable
- **Slow performance**: Verify TORCH_VARIANT is set correctly
- **Import errors**: Ensure PyTorch GPU version is installed

## Environment Variables

| Variable        | Description                     | Default |
| --------------- | ------------------------------- | ------- |
| `TORCH_VARIANT` | PyTorch version (cpu/cuda/rocm) | cpu     |
| `GPU_COUNT`     | Number of GPUs to use           | 0       |

## Advanced Configuration

### Multiple GPUs

```bash
export GPU_COUNT=2
export TORCH_VARIANT=cuda
docker-compose up --build
```

### Custom PyTorch Installation

Edit the Dockerfile to install specific PyTorch versions:

```dockerfile
# For CUDA 11.8
RUN pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/cu118

# For ROCm 5.7
RUN pip install torch>=2.0.0 --index-url https://download.pytorch.org/whl/rocm5.7
```

### Memory Optimization

For GPUs with limited VRAM, use smaller Whisper models:

```python
# In video_evaluator.py, change model name
model_name = "base"  # instead of "medium"
```
