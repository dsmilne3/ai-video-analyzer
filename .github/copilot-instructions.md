# AI Coding Agent Instructions for AI Video Analyzer

## Project Overview

This is a Python-based AI video evaluation system that transcribes demo videos using Whisper, evaluates them against configurable rubrics using LLMs (OpenAI/Anthropic), and generates qualitative feedback. Architecture follows a local-first approach: Whisper handles transcription/translation locally (free), while LLM APIs are used only for rubric evaluation.

## Key Components

- **`src/video_evaluator.py`**: Core VideoEvaluator class handling transcription, evaluation, and feedback generation
- **`Home.py`**: Streamlit app entry point
- **`pages/2_Analyze_Video.py`**: Main video analysis interface with rubric management
- **`rubrics/`**: JSON rubric definitions (see `rubrics/sample-rubric.json` for hierarchical format)
- **`results/`**: Auto-saved evaluation outputs with timestamps (git-ignored)

## Development Workflow

1. **Setup**: `pip install -r requirements.txt` + `brew install ffmpeg`
2. **Check dependencies**: `python check_dependencies.py`
3. **Run tests**: `pytest -q`
4. **UI development**: `streamlit run Home.py`
5. **Rubric management**: Use the sidebar in the Streamlit UI for creating, editing, and managing rubrics

## Rubric System

- **Formats**: Support both flat criteria arrays (legacy) and hierarchical categories (preferred)
- **Validation**: Use `validate_rubric()` from `src/video_evaluator.py` before loading
- **Loading**: `load_rubric("rubric_name")` automatically handles path resolution and fallbacks
- **Evaluation**: New format uses point-based scoring per category; old format uses weighted mean

## Common Patterns

- **Translation**: Enabled by default; Whisper translates non-English audio to English for consistent evaluation
- **Vision analysis**: Optional frame extraction + multimodal alignment checks (non-feature-specific)
- **Progress reporting**: Use `progress_callback` for UI updates
- **Error handling**: Graceful fallback to heuristic scoring when LLM APIs fail
- **Feedback generation**: 2 strengths + 2 improvements with adaptive tone (congratulatory/supportive)
- **Results saving**: `save_results()` creates timestamped files, never overwrites

## Testing

- **Unit tests**: `tests/test_evaluator.py` mocks LLM calls for evaluation/feedback testing
- **Integration**: `test_data/run_end_to_end_demo.py` for full pipeline validation
- **Mock transcription**: When Whisper unavailable, returns `"(mock) transcribed text from audio"`

## Gotchas

- **API keys**: Required for LLM evaluation; set via `OPENAI_API_KEY`/`ANTHROPIC_API_KEY` or `--api-key`
- **ffmpeg dependency**: Critical for video processing; check with `subprocess.run(['ffmpeg', '-version'])`
- **MPS placement**: Selective GPU memory placement for Apple Silicon (see `_move_model_to_mps_selective()`)
- **URL processing**: yt-dlp downloads to temp directory; cleanup downloaded files after processing
- **Rubric thresholds**: Point-based for new format (e.g., pass: 35/50); percentage-based for old format
