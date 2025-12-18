# Demo Video Analyzer
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Automatically evaluate demo videos using AI. For initial transcription and translation tasks, the project uses a **local-first pipeline** for cost control, with optional cloud API escalation for using different models. The user's choice of LLM provider (OpenAI or Anthropic) is then used to evaluate the video content against a selected rubric and provide quantitative feedback to the submitter.

## System Requirements

- Python 3.9+
- ffmpeg (for audio/video processing)
- 2GB+ RAM (for Whisper base model)
- Optional: GPU for faster transcription

> **⚠️ Virtual Environment Highly Recommended**: All commands must be run within the project's virtual environment. Use `./activate.sh` to set it up and activate it automatically.

## Features

- Native (local) or Docker deployment options (containerized deployment with volume persistence)
- Streamlit reviewer app with file upload and URL input
**URL Support**
- Analyze videos without downloading manually (YouTube, Vimeo, and direct video file URLs)
- Automatic cleanup of video files after analysis completes

- Choose between OpenAI or Anthropic models for evaluation
- GPU acceleration support (NVIDIA CUDA, AMD ROCm, Apple Silicon MPS - see documentation for details)
**Language Support**
- ASR transcription with timestamps using Whisper (local, free)
- Automatic language detection (Whisper detects 99+ languages)
- Detected language shown in results
- Translation to English (optional Whisper-based translation for non-English demos)
- Maintains technical term accuracy
**Multimodal alignment checks (non-feature-specific) between transcript and video frames**
- Support for multiple video formats (MP4, MOV, AVI, MKV) and audio formats (MP3, WAV, M4A, AAC)
- Transcription quality metrics (confidence, speech detection, compression ratio)

- Rubric management system with import and customizable capability
- Rubric-based scoring
- Qualitative feedback generation with 2 strengths and 2 areas for improvement

**Evaluation progress reporting during analysis**
- Progress of local tasks (URL download, transcription, and frame analysis)
- Progress of remote tasks (AI evaluation, qualitative feedback generation)

- Adaptive tone (congratulatory for passing scores, supportive for failing scores)
**Auto-Save Results**
- JSON results auto-saved to `results/` folder (<filename>_results_YYMMDD_HHMMSS.json)
- Timestamped results avoids overwrites

- CLI tool for testing

## Architecture

**AI-Powered Analysis with Local-First Transcription**

- **Transcription**: Local Whisper processing (free, supports 99+ languages)
- **Vision**: Optional multimodal alignment checks between transcript and video frames
- **Evaluation**: LLM-powered, rubric-based assessment using OpenAI or Anthropic APIs for intelligent scoring
- **Feedback**: AI-generated qualitative feedback with adaptive tone and specific recommendations
- **Fallback**: Conservative heuristic scoring when API keys are unavailable (limited functionality)

## Setup

### Testing Summary
- Full guide: see [docs/TESTING.md](docs/TESTING.md)
- Unit/integration: `./run.sh test`
- Browser E2E: `venv/bin/python -m pytest -m e2e tests/e2e -v` (requires Playwright; see [docs/TESTING.md](docs/TESTING.md#browser-e2e-playwright))

### Prerequisites

#### 1. Install System Dependencies

```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Linux (RHEL/CentOS)
sudo yum install ffmpeg
```

#### 2. Configure GPU Support (Optional but Recommended)

Detect available GPUs and configure the environment:

```bash
# Creates the .env file with detected GPU settings
./run_gpu.sh --dry-run
```

The detected GPU settings will be used by either deployment option. Additional output simply shows the shows the Docker configuration that would be used if the Docker deployment option were selected in subsequent steps.  It does NOT actually start any containers.

#### 3. Configure API Keys (Required for Qualitative Analysis)

**API keys are required** for the core qualitative analysis and feedback generation features. Without them, the system falls back to basic, less accurate heuristic scoring.

**Option A: Environment Variables (Quick Setup)**

```bash
export OPENAI_API_KEY=your-openai-api-key
# or
export ANTHROPIC_API_KEY=your-anthropic-api-key
```

**Option B: .env File (Recommended for persistent setup)**

Add your API keys to the .env file created in Step 2

**Note**: Environment variables override .env file values. See [API_KEYS.md](docs/API_KEYS.md) for detailed configuration.

### Choose Your Deployment Method

This project offers two deployment options. Choose based on your needs:

#### 🚀 Option 1: Native Installation (Recommended for Mac Users)

**Pros:**

- ⚡ **GPU acceleration** on Apple Silicon (MPS) - 2-4x faster transcription
- 🔧 Full control over environment and dependencies
- 🐛 Easier debugging and development

**Cons:**

- 📦 Requires installing system dependencies (ffmpeg)
- ⚙️ More setup steps
- 🔄 Manual virtual environment management

#### 🐳 Option 2: Docker Installation (Recommended for Simplicity)

**Pros:**

- 📦 **No system dependencies** to install
- 🚀 One-command deployment
- 🔒 Isolated environment, no conflicts

**Cons:**

- 🚫 **No Apple Silicon GPU acceleration** (MPS not available in containers) increases CPU load during transcription
- 📊 Less transparent for debugging
- 💾 Larger container images

---

### Native Installation Setup

#### 1. Install Python Dependencies

```bash
# Set up virtual environment (one-time setup) and install dependencies
./activate.sh

# Verify dependency installation
./run.sh check
```

A final check to see that all dependencies are installed or identify ones still missing.

#### 2. Run the Application

```bash
# Recommended launch script that runs the app in a Python virtual environment
./run.sh app
```

**You're all set!** The system is functional and ready to evaluate demo videos.


**Command Reference (Native Installation Only)**
After setting up with native installation, you can use these convenience scripts:

```bash
# Quick launch commands (virtual environment activated automatically)
./run.sh demo     # Run end-to-end demo
./run.sh test     # Run tests

# Alternate launch commands to run the app after entering a Python virtual environment (not recommended)
source venv/bin/activate
streamlit run Home.py
```


---

### Docker Installation Setup

#### 1. Quick Docker Deployment

**GPU Support in Docker:**

- **NVIDIA GPUs**: Automatic CUDA acceleration via NVIDIA Container Toolkit
- **AMD GPUs**: ROCm support for compatible AMD GPUs
- **Apple Silicon**: MPS acceleration not available in Docker (use native installation)

See [DOCKER_README.md](DOCKER_README.md) for detailed Docker deployment instructions.
See [GPU_README.md](GPU_README.md) for detailed GPU setup instructions.

```bash
# Ensure Docker and docker-compose (or docker compose) are installed
# Then build the Docker image
docker compose build
# Then start a container from the image
docker compose up

# Access at http://localhost:8501
```


## Evaluation Rubrics

The system supports **multiple evaluation rubrics** for different types of demos. Each rubric defines criteria, weights, and pass/fail thresholds optimized for specific use cases (e.g., sales demos, technical demos, general partner demos).

### Multiple Rubric Support

The system supports different evaluation rubrics for different demo types. Each rubric defines criteria, weights, and 
thresholds optimized for specific use cases.

### Creating Custom Rubrics

You can create custom rubrics by adding JSON files to the `rubrics/` directory. See `rubrics/README.md` for:

- Rubric structure and requirements
- Examples of existing rubrics
- Instructions for creating custom rubrics
- Validation rules

### Using Rubrics

Select from the available evaluation rubrics. The UI shows all available rubrics with their descriptions and criteria.

**Available rubrics** are stored in the `rubrics/` directory. See `rubrics/README.md` for details on existing rubrics 
and how to create custom ones.

## What Each Score Means

| Score   | Meaning    | Action                      |
| ------- | ---------- | --------------------------- |
| 8-10    | Excellent  | ✅ Publish as-is            |
| 6.5-7.9 | Good       | ✅ Pass with minor notes    |
| 5.0-6.4 | Needs work | ⚠️ Revise before publishing |
| < 5.0   | Poor       | ❌ Re-record required       |

**Note:** Specific thresholds may vary by rubric. Use `--list-rubrics` to see thresholds for each rubric.

## Language Support & Translation

The system supports **99+ languages** through Whisper's automatic language detection:

### Automatic Language Detection

Whisper automatically detects the language of the audio and displays it in the UI:

- **UI**: Displays in the Transcription Quality expander

### Translation to English (Default)

**Translation is enabled by default** to ensure consistent English evaluations across all demos.

**UI:**

- "Translate to English" is checked by default
- Uncheck to keep the original language

**How it works:**

- Uses Whisper's built-in translation capability
- Free, local translation (no API costs)
- High quality (same model used by professionals)
- Maintains technical term accuracy

**When detected language is translated:**

- Shows: "Detected Language: ES → 🌐 Translated to English"
- Evaluation and feedback use the English translation

**Supported languages:** All languages Whisper supports (99+), including:

- Spanish, French, German, Italian, Portuguese
- Japanese, Chinese, Korean
- Arabic, Russian, Dutch, Polish
- And many more...

## Results Storage

After each evaluation, results are **automatically saved** to the `results/` folder with timestamps to preserve evaluation history:

### UI Results

- **Format**: Human-readable text file
- **Location**: `results/<filename>_results_YYYYMMDD_HHMMSS.json`
- **Download**: Interactive download button in the UI
- **Contents**: Evaluation summary, quality metrics, feedback, and transcript

**Note**: JSON export is currently disabled for UI simplicity. See `REMINDER_JSON_EXPORT.md` if you need structured data export for dashboards, APIs, or bulk analysis.

### No Overwrites

Each evaluation creates a **new timestamped file**, so you can:

- Compare results across multiple runs
- Track improvements over time
- Preserve complete evaluation history
- Never lose previous results

**Example**:

Use the Streamlit UI to analyze videos. Results are automatically saved with timestamps.

The `results/` directory is git-ignored to avoid committing evaluation outputs.

## Feedback for Submitters

In addition to numeric scores, the evaluator generates **qualitative feedback** for each video:

- **2 Strengths**: Specific areas where the demo excelled (2-3 sentences each)
- **2 Areas for Improvement**: Actionable suggestions for enhancement (2-3 sentences each)
- **Adaptive Tone**:
  - **Congratulatory** tone for passing videos (score ≥ 6.5)
  - **Supportive** tone for videos needing revision (score < 6.5)

This feedback is designed to help submitters understand their performance and improve future demos.

## Project Structure

```
demo-video-analyzer/
├── activate.sh                       # Python virtual environment helper script
├── check_dependencies.py             # Dependency validation module
├── clear_cache.sh                    # Python cache clearing helper script
├── docker-compose.yml                # Docker project build spec
├── Dockerfile                        # Docker image build spec
├── docs                              # Documentation repository
├── Home.py                           # Streamlit app
├── pages/                            # Main UI pages
├── README.md                         # This file
├── requirements.txt                  # Python dependencies
├── results/                          # Repository for Auto-saved evaluation results
├── rubrics/
│   ├── partner-ditl.json             # Day-In-The-Life demo flow rubric used for partner certification videos
│   ├── README.md                     # Rubric documentation
│   ├── sales-demo.json               # Sales-focused rubric
│   ├── sample-rubric.json            # Sample rubric for general demos
│   └── sample-technical-demo.json    # Technical deep-dive rubric
├── rubric_helper.py                  # Rubric management module
├── run_gpu.sh                        # GPU detection script
├── run.sh                            # Application launch wrapper script
├── src/
│   └── video_evaluator.py            # Video evaluation module
├── test_data/                        # Unit test resources
├── tests/                            # Unit testing utilities
└── validation_ui.py                  # Rubric validation module
```

## Cost Optimization

**Free/Local Components:**

- Whisper (transcription): Open-source, runs locally
- ffmpeg: Free audio/video processing
- OpenCV: Free frame extraction
- Streamlit: Free UI framework

**Paid/Cloud Components:**

- Primary evaluation and feedback generation: OpenAI GPT-4o, Anthropic Claude-3-5-Haiku-20241022
- Cheaper models used as valuation and feedback helpers: GPT-4o-mini, Anthropic Claude-3
- (future) Secondary vision analysis: OpenAI GPT-4o Vision, Anthropic Claude-3 Vision

## Testing

See TESTING.md in the `docs/` directory.

## Documentation

**Additional documentation is available in the `docs/` folder:**

## License

See [LICENSE](LICENSE) for details.
