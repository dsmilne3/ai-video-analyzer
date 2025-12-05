# Demo Video Analyzer

Automatically evaluate demo videos using AI. This project implements a **local-first pipeline** with optional cloud API escalation for cost optimization.

> **⚠️ Virtual Environment Required**: All commands must be run within the project's virtual environment. Use `./activate.sh` to set it up and activate it automatically.

## Install

### Docker (Recommended)

For easier deployment without installing system dependencies check [this guide](docs/setup/DOCKER.md) to know where to set your API keys and build for the first time


### Locally with Python
#### 0. Check Dependencies (Recommended First Step)

```bash
# Check if all dependencies are installed
python3 check_dependencies.py
```

This will show you which dependencies are installed and which are missing.

#### 1. Install System Dependencies

```bash
# macOS
brew install ffmpeg

# Linux (Ubuntu/Debian)
sudo apt-get install ffmpeg

# Linux (RHEL/CentOS)
sudo yum install ffmpeg
```

#### 2. Install Python Dependencies

```bash
# Set up virtual environment (one-time setup)
./activate.sh

# Or manually:
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt

# Verify installation
python check_dependencies.py
```
#### 4. Set API Keys

For full LLM evaluation (not needed for basic testing):

```bash
export API_KEY=your-openai-or-anthropic-api-key
```

#### 5. Run Demo

```bash
# Quick launch commands (virtual environment activated automatically)
./run.sh app      # Launch reviewer UI
./run.sh demo     # Run end-to-end demo
./run.sh test     # Run tests
./run.sh check    # Check dependencies

# Or manually activate and run:
source venv/bin/activate
streamlit run Home.py
```

**Note**: The `realistic_demo.wav` file contains synthetic speech simulating a real product demo (pre-generated and included in the repo). See `test_data/realistic_demo_script.md` and `test_data/realistic_demo_transcript.md` for the script and transcription.

## Details

<details>
<summary>Features</summary>

### Features

- ✓ ASR transcription with timestamps using Whisper (local, free)
- ✓ **Transcription quality metrics** (confidence, speech detection, compression ratio)
- ✓ **Automatic language detection** (Whisper detects 99+ languages)
- ✓ **Translation to English** (optional Whisper-based translation for non-English demos)
- ✓ Auto-summary and jump-to highlights
- ✓ **Multiple evaluation rubrics** (sales-demo, technical-demo, default)
- ✓ **Qualitative feedback generation with 2 strengths and 2 areas for improvement**
- ✓ **Adaptive tone (congratulatory for passing scores, supportive for failing scores)**
- ✓ Multimodal alignment checks (non-feature-specific) between transcript and video frames
- ✓ Support for multiple video formats (MP4, MOV, AVI, MKV) and audio formats (MP3, WAV, M4A, AAC)
- ✓ **URL support** (YouTube, Vimeo, and direct video links)
- ✓ **Auto-save results with timestamps** (no overwrites)
- ✓ **CLI pagination** (results displayed through `less`/`more`)
- ✓ **Progress reporting** in UI terminal during analysis
- ✓ Choose between OpenAI or Anthropic models for evaluation
- ✓ CLI tool for batch processing
- ✓ Streamlit reviewer app with file upload and URL input
- ✓ **Docker deployment** (containerized deployment with volume persistence)
- ✓ **GPU acceleration support** (NVIDIA CUDA, AMD ROCm, Apple Silicon MPS)
</details>

<details>
<summary>Architecture</summary>

### Architecture

**Recommended Default: Local-First with Escalation**

- Primary: Local Whisper transcription + heuristic evaluation (free, privacy-preserving)
- Escalation: Call paid APIs (OpenAI/Anthropic) only for low-confidence transcripts or human-flagged videos
- Vision analysis: Optional multimodal alignment checks for transcript verification
</details>

<details>
<summary>Evaluation Rubrics</summary>

### Evaluation Rubrics

The system supports **multiple evaluation rubrics** for different types of demos. Each rubric defines criteria, weights, and thresholds optimized for specific use cases (e.g., sales demos, technical demos, general partner demos).

#### Using Rubrics

Use the Streamlit UI to select from available evaluation rubrics. The UI shows all available rubrics with their descriptions and criteria.

**In Streamlit UI:** Select rubric from the dropdown in the sidebar before clicking "Analyze"

#### Creating Custom Rubrics

You can create custom rubrics by adding JSON files to the `rubrics/` directory. See `docs/rubrics/README.md` for:

- Rubric structure and requirements
- Examples of existing rubrics
- Instructions for creating custom rubrics
- Validation rules

</details>


<details>
<summary>Language Support & Translation</summary>

### Language Support & Translation 

The system supports **99+ languages** through Whisper's automatic language detection:

#### Automatic Language Detection

Whisper automatically detects the language of the audio and displays it in the UI:

- **UI**: Displays in the Transcription Quality expander

#### Translation to English (Default)

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

**Supported languages:** All languages Whisper supports (99+)



## Results Storage

After each evaluation, results are **automatically saved** to the `results/` folder with timestamps to preserve evaluation history:

### UI Results

- **Format**: Human-readable text file
- **Location**: `results/<filename>_results_YYYYMMDD_HHMMSS.txt`
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

</details>

<details>
<summary>Feedback for Submitters</summary>

### Feedback for Submitters

In addition to numeric scores, the evaluator generates **qualitative feedback** for each video:

- **2 Strengths**: Specific areas where the demo excelled (2-3 sentences each)
- **2 Areas for Improvement**: Actionable suggestions for enhancement (2-3 sentences each)
- **Adaptive Tone**:
  - **Congratulatory** tone for passing videos (score ≥ 6.5)
  - **Supportive** tone for videos needing revision (score < 6.5)

This feedback is designed to help submitters understand their performance and improve future demos.

</details>

<details>
<summary>Cost Optimization</summary>

### Cost Optimization

**Free/Local Components:**

- Whisper (transcription): Open-source, runs locally
- ffmpeg: Free audio/video processing
- OpenCV: Free frame extraction
- Streamlit: Free UI framework

**Paid/Cloud Components (Optional):**

- OpenAI GPT-4o: ~$2.50 per 1M input tokens, $10 per 1M output tokens
- Anthropic Claude: ~$3 per 1M input tokens, $15 per 1M output tokens
- Vision APIs: ~$0.01-0.05 per image
- Whisper API: 0,006$ per min of audio

**Recommended Strategy:**

1. Process all videos locally with Whisper (free)
2. Use fallback heuristic scoring (free)
3. Only call paid LLM APIs for:
   - Low-confidence transcripts (< 80% average confidence)
   - Human-flagged videos requiring deeper analysis
   - Final review/top submissions

</details>

<details>
<summary>Testing</summary>

### Testing

```bash
# Run unit tests
pytest -q

# Run end-to-end demo
python test_data/run_end_to_end_demo.py
```

</details>

<details>
<summary>Documentation</summary>

### Documentation

Additional documentation is available in the `docs/` folder.