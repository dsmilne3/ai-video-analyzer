# Quick Start Guide

## What You Have Now

A complete AI-powered demo video evaluation system with:

- ✅ Local Whisper transcription (free, privacy-preserving)
- ✅ Rubric scoring with JSON output
- ✅ Multimodal alignment checks
- ✅ Auto-summaries and highlights
- ✅ CLI and web UI (Streamlit)
- ✅ Test tools and data for pipeline validation

## To Use It Right Now

### Option 1: Test with Demo (No Setup Required)

```bash
source .venv/bin/activate
python test_data/run_end_to_end_demo.py
```

**What it shows:** Rubric evaluation, highlights, summary generation

### Option 2: Process Real Videos (Requires ffmpeg)

1. **Install ffmpeg** (one-time, 5-10 min):

   ```bash
   brew install ffmpeg
   ```

2. **Process a video:**

   Use the Streamlit UI to upload files or enter URLs for analysis.

3. **Use a specific rubric** (sales-demo, technical-demo, or default):

   Select the desired rubric from the dropdown in the Streamlit UI sidebar.

4. **With vision analysis:**

   Check the "Enable visual alignment checks" box in the Streamlit UI.

5. **Keep original language (disable default translation):**

   Uncheck the "Translate to English" box in the Streamlit UI.

### Option 3: Use Web Interface

```bash
source .venv/bin/activate
streamlit run Home.py
```

Then open the URL in your browser. The UI supports:

- **File Upload**: Upload local video/audio files (MP4, MOV, AVI, MKV, MP3, WAV, M4A)
- **URL Input**: Analyze videos from YouTube, Vimeo, or direct video links
- **Rubric Selection**: Choose evaluation rubric from dropdown
- **Vision Analysis**: Optional checkbox for video frame analysis
- **Translation**: Optional checkbox to translate non-English audio to English
- **Auto-save**: Results automatically saved to `results/` folder with timestamps
- **Download**: Download text report after analysis

## Multiple Rubric Support

The system supports different evaluation rubrics for different demo types. Each rubric defines criteria, weights, and thresholds optimized for specific use cases.

```bash
# List all available rubrics with descriptions
python cli/evaluate_video.py --list-rubrics

# Use a specific rubric
python cli/evaluate_video.py video.mp4 --rubric sales-demo --provider openai

# Use default rubric (if --rubric not specified)
python cli/evaluate_video.py video.mp4 --provider openai
```

**In Streamlit UI:** Select rubric from the dropdown before clicking "Analyze"

**Available rubrics** are stored in the `rubrics/` directory. See `rubrics/README.md` for details on existing rubrics and how to create custom ones.

## What Each Score Means

| Score   | Meaning    | Action                      |
| ------- | ---------- | --------------------------- |
| 8-10    | Excellent  | ✅ Publish as-is            |
| 6.5-7.9 | Good       | ✅ Pass with minor notes    |
| 5.0-6.4 | Needs work | ⚠️ Revise before publishing |
| < 5.0   | Poor       | ❌ Re-record required       |

**Note:** Specific thresholds may vary by rubric. Use `--list-rubrics` to see thresholds for each rubric.

## Key Features

### Language Support

**Automatic Language Detection:**

- Whisper automatically detects 99+ languages
- Detected language shown in CLI and UI results
- Works with Spanish, French, German, Japanese, Chinese, and many more

**Translation to English (Default):**

- **Enabled by default** for consistent English evaluations
- **CLI**: Use `--no-translate` flag to disable
- **UI**: "Translate to English" is checked by default (uncheck to disable)
- Uses Whisper's built-in translation (free, local, high quality)
- Shows "ES → 🌐 Translated to English" in results
- Maintains technical term accuracy

### URL Support

Analyze videos directly from URLs without downloading:

- **YouTube**: Enter URL in the Streamlit UI
- **Vimeo**: Enter URL in the Streamlit UI
- **Direct Links**: Any direct video URL (MP4, etc.)

The system automatically downloads and processes videos from URLs, with automatic cleanup after analysis.

### Auto-Save Results

Every evaluation is automatically saved with a timestamp:

- **Location**: `results/` folder
- **Format**: `<filename>_results_YYYYMMDD_HHMMSS.txt`
- **No Overwrites**: Each run creates a new file, preserving history
- **CLI**: Results saved automatically after analysis
- **UI**: Results saved + download button provided

### CLI Pagination

Long outputs in the CLI are automatically paginated through `less` (or `more`):

- Navigate with arrow keys, space, Page Up/Down
- Search with `/` (in less)
- Quit with `q`
- Pipe-friendly: `python cli/evaluate_video.py video.mp4 --provider openai > output.txt` skips pagination

### Progress Reporting

The UI shows progress in the terminal where Streamlit is running:

- Download progress (when using URLs)
- Transcription status
- Frame analysis (when vision enabled)
- AI evaluation progress
- Completion notification

**Note**: All progress messages appear in the terminal, not in the browser UI.

## Rubric Quick Reference

The system supports multiple evaluation rubrics stored in `rubrics/` directory. Each rubric defines:

- Evaluation criteria and their weights
- Pass/revise/fail thresholds
- Specific focus areas (e.g., technical accuracy, business value, engagement)

**Commands:**

- Use the Streamlit UI sidebar to select rubrics and view their details

**See:** `rubrics/README.md` for complete rubric documentation and custom rubric creation.

## Cost Control

**Free Tier (Current Setup)**

- Transcription: Whisper (local)
- Scoring: Heuristic fallback
- Cost: $0 per video

**Paid Tier (Optional)**

- Transcription: Whisper (local) - still free
- Scoring: OpenAI GPT-4o or Anthropic Claude
- Cost: ~$0.01-0.05 per 5-min video

**Vision Tier (Optional)**

- Everything above + frame analysis
- Cost: ~$0.10-0.30 per 5-min video

## Typical Workflow

```
Partner submits video
        ↓
Run evaluator (local Whisper + heuristic scoring)
        ↓
Review in Streamlit UI
        ↓
If score < 6.0 or flagged: re-run with LLM for detailed analysis
        ↓
Share results with partner
```

## Common Commands

```bash
# Activate environment
source .venv/bin/activate

# Launch UI
streamlit run Home.py

# Run tests
pytest -q
```

## Troubleshooting

**Error: "No module named 'whisper'"**

- Solution: `source .venv/bin/activate`

**Error: "ffmpeg not found"**

- Solution: `brew install ffmpeg` (takes 5-10 min)

**Error: API key issues**

- Solution: `export API_KEY=your-key` or pass `--api-key` flag

**Slow transcription**

- Whisper runs on CPU by default
- For faster processing: use a Mac with Apple Silicon, or enable GPU acceleration:
  - **Docker**: Run `./run_gpu.sh` for automatic GPU detection
  - **Native**: GPU acceleration available on NVIDIA/AMD GPUs and Apple Silicon

## Next Steps

1. **List available rubrics** with `--list-rubrics` to see evaluation options
2. **Test on 3-5 real demo videos** with appropriate rubrics
3. **Choose or create rubric** that matches your demo evaluation needs (see `rubrics/README.md`)
4. **Gather feedback** from your team on scoring accuracy
5. **Set up escalation** (process all locally, LLM only for borderline cases)
6. **Build dashboard** to track scores over time

## Get Help

- See `README.md` for full documentation
- See `IMPLEMENTATION_SUMMARY.md` for technical details
- Run demo: `python test_data/run_end_to_end_demo.py`
- Check tests: `pytest -q`

---

**You're all set!** The system is functional and ready to evaluate demo videos.
