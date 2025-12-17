# Docker Deployment for AI Video Analyzer

This guide explains how to run the AI Video Analyzer using Docker for easy deployment and isolation.

## Prerequisites

- Docker installed on your system
- docker-compose installed (usually comes with Docker Desktop)
- At least 8GB RAM recommended for Whisper model loading (or use remote execution from OpenAI)
- **GPU Support**: Optional GPU acceleration available for NVIDIA/AMD GPUs (automatic detection)

## Quick Start

1. **Set up environment variables:**

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

2. **For significantly faster processing on Whisper locally, enable GPU acceleration: (optional)**

```bash
# Auto-detect GPU and configure Docker
./run_gpu.sh
```

Refer to the [GPU docs](./GPU_README.md) for more details

3. **Build and run with Docker Compose:**

   ```bash
   docker compose up --build
   ```

4. **Access the application:**
   Open your browser and go to `http://localhost:8501`

---

## Detailed Usage

### Building the Docker Image

```bash
# Build the image
docker build -t ai-video-analyzer .

# Or use docker-compose (recommended)
docker-compose build
```

### Running the Container

```bash
# Using docker-compose (recommended)
docker-compose up

# Or run directly with docker
docker run -p 8501:8501 \
  -v $(pwd)/results:/app/results \
  -v $(pwd)/rubrics:/app/rubrics \
  -v $(pwd)/overrides:/app/overrides \
  -v $(pwd)/.env:/app/.env:ro \
  ai-video-analyzer
```

### Volume Mounts

The Docker setup mounts the following directories for persistence:

- `./results:/app/results` - Analysis results and JSON exports
- `./rubrics:/app/rubrics` - Custom evaluation rubrics
- `./overrides:/app/overrides` - Score override presets
- `./.env:/app/.env:ro` - Environment variables (read-only)

This ensures that your data persists between container restarts and is accessible from your host machine.

## Configuration

### Environment Variables

Create a `.env` file in the project root with your API keys:

```bash
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_anthropic_key_here
```

### Custom Rubrics

Place your custom rubric files in the `rubrics/` directory. They will be available in the Docker container.

### GPU Support

GPU acceleration is automatically configured based on your hardware:

```bash
# Auto-detect GPU and configure Docker
./run_gpu.sh
```

**Supported GPUs:**

- **NVIDIA GPUs**: CUDA acceleration via NVIDIA Container Toolkit (5-10x speedup)
- **AMD GPUs**: ROCm support for compatible GPUs (3-8x speedup)
- **Apple Silicon**: MPS acceleration when running natively (not in Docker)

The script automatically detects your GPU type and installs the appropriate PyTorch version. For detailed setup instructions, see [GPU_README.md](GPU_README.md).

**Manual GPU Configuration:**

```bash
# For NVIDIA GPUs (requires NVIDIA Container Toolkit)
docker run --gpus all -p 8501:8501 ai-video-analyzer

# For AMD GPUs (requires ROCm)
export TORCH_VARIANT=rocm
docker-compose up --build
```

## Troubleshooting

### Common Issues

1. **Port already in use:**

   ```bash
   # Change the port mapping
   docker-compose up -d
   # Then access at http://localhost:8502
   ```

2. **Permission issues with mounted volumes:**

   ```bash
   # Ensure the directories exist and have proper permissions
   mkdir -p results rubrics overrides
   ```

3. **Memory issues:**

   - Ensure your system has at least 8GB RAM
   - The Whisper model requires significant memory for loading

4. **API key issues:**
   - Verify your `.env` file is properly formatted
   - Check that API keys are valid and have sufficient credits

### Logs

```bash
# View container logs
docker-compose logs -f

# View logs for a specific service
docker-compose logs -f ai-video-analyzer
```

### Cleanup

```bash
# Stop and remove containers
docker-compose down

# Remove images and volumes
docker-compose down --volumes --rmi all
```

## Development

### Building for Development

```bash
# Build with development dependencies
docker build -f Dockerfile.dev -t ai-video-analyzer:dev .

# Run with hot reload
docker run -p 8501:8501 -v $(pwd):/app ai-video-analyzer:dev
```

## Security Considerations

- API keys are stored in environment variables
- Results are persisted to host directories
- Container runs with limited privileges
- No sensitive data is stored in the container itself

## Performance Notes

- First run may take longer due to model downloads
- GPU acceleration significantly improves transcription speed
- Results are cached in mounted volumes for faster subsequent runs

## macOS-Specific Instructions

The Docker deployment is optimized for macOS with Docker Desktop. The configuration includes:

- **tmpfs mount**: `/tmp` directory uses memory for better performance
- **User permissions**: Container runs as non-root user for security
- **Volume mounts**: Direct bind mounts for seamless file access

### macOS Setup

1. **Install Docker Desktop for Mac:**

   - Download from https://www.docker.com/products/docker-desktop
   - Ensure you have at least Docker Desktop 4.0+

2. **Increase memory allocation:**

   - Go to Docker Desktop > Settings > Resources
   - Allocate at least 8GB RAM
   - Allocate 4+ CPU cores

3. **File sharing permissions:**
   - Docker Desktop > Settings > Resources > File sharing
   - Add your project directory to allowed paths

### macOS Troubleshooting

1. **Slow performance:**

   - The `tmpfs` setting optimizes temporary file operations
   - Ensure Docker Desktop has sufficient resources allocated

2. **File permission issues:**

   - Files created in mounted volumes will have the container user ID
   - Use `chown` if needed: `sudo chown -R $USER results/`

3. **Port conflicts:**
   - macOS may have built-in services using port 8501
   - Change the port in `docker-compose.yml` if needed

### Performance Optimization

For best performance on macOS:

- Use Docker Desktop 4.0+ with Apple Silicon support (if applicable)
- Enable VirtioFS for faster file sharing (Docker Desktop > Settings > Experimental)
- Allocate sufficient RAM (8GB+) and CPU cores
