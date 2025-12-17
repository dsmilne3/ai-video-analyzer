# Quick Start Guide

## Application Features

An AI-powered demo video evaluation system with:

- ✅ Web UI (Streamlit)
- ✅ Multimodal alignment checks
- ✅ Local Whisper transcription (free, privacy-preserving)
- ✅ Rubric management system
- ✅ AI-assisted video evaluations with rubric-based scoring
- ✅ Ai-assisted qualitative feedback
- ✅ JSON transcription and analysis results

## Environment Setup

### 1. Install System Dependencies
```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Linux (RHEL/CentOS)
sudo yum install ffmpeg
## Deployment Options
```

### 2. Configure GPU Support (Optional but Recommended)
```bash
# Creates the .env file with detected GPU settings
./run_gpu.sh --dry-run
```

### 3. Configure API Keys
Add your API keys to the .env file created in Step 2.

```bash
# OpenAI
echo OPENAI_API_KEY=<your-api-key> >> ./.env

# Anthropic (optional)
echo ANTHROPIC_API_KEY=<your-api-key> >> ./.env
```

## Choose Your Deployment Method

### 🚀 Option 1: Native Installation (Recommended for Mac Users)

#### A. Install Python Dependencies

```bash
# Set up virtual environment (one-time setup) and install dependencies
./activate.sh

# Verify dependency installation
./run.sh check
```

#### B. Run the Application

```bash
# Recommended launch script that runs the app in a Python virtual environment
./run.sh app
```

### Option 2: Docker Installation

#### A. Quick Docker Deployment

GPU Support in Docker on Mac is not available

```bash
# Ensure Docker and docker-compose (or docker compose) are installed
# Then build the Docker image
docker compose build
# Then start a container from the image
docker compose up

# Access at http://localhost:8501
```

## Using the Application to Evaluate a Demo Video

### Typical Workflow Overview

```
Partner submits video
        ↓
Run evaluator
        ↓
Review results
        ↓
If score < 6.0 or flagged: re-run with LLM for detailed analysis
        ↓
Share results with partner
```

### Navigating the Application

1. **Verify System Status**
   Ensure the Systems Status in the navigation bar shows required dependencies are set up correctly

2. **Navigate to the Analyze Video page**

3. **Fill out the submitter information**

4. **Select the Input Method**
   After selection, navigate to the local file or provide the URL to the demo video

5. **Select Processing Options**
   Enable translation from non-English and Visual Alignment checks as needed

6. **Select the rubric to be used for scoring the video**

7. **Start the Analysis**
   Click the `Analyze Video` button


## Next Steps

1. **List available rubrics** to see evaluation options
2. **Test on 3-5 real demo videos** with appropriate rubrics
3. **Choose or create rubric** that matches your demo evaluation needs (see `rubrics/README.md`)
4. **Gather feedback** from your team on scoring accuracy

## Troubleshooting

**Error: "No module named 'whisper'"**

- Solution: Ensure the application is running in a virtual environment `./run.sh app` or `source ./venv/bin/activate && streamlit run Home.py`

**Error: "ffmpeg not found"**

- Solution: `brew install ffmpeg` (takes 5-10 min)

**Error: API key issues**

- Solution: `export API_KEY=your-key` or verify your api key is set in the .env file

**Slow transcription**

- Whisper runs on CPU unless GPU acceleration is enabled
- For faster processing: use a Mac with Apple Silicon, or enable GPU acceleration:
  - **Docker**: Run `./run_gpu.sh` for automatic GPU detection
  - **Native**: GPU acceleration available on NVIDIA/AMD GPUs and Apple Silicon

## Get Help

- See `README.md` for full documentation
- See `IMPLEMENTATION_SUMMARY.md` for technical details
- Testing guide: [docs/TESTING.md](docs/TESTING.md)
- Run demo: `python tests/run_end_to_end_demo.py`
- Check tests: `pytest -q`
- Optional browser E2E: see [docs/TESTING.md](docs/TESTING.md#browser-e2e-playwright)

---
