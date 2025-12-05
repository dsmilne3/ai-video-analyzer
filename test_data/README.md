# Test Data - Realistic Demo Audio

This directory contains pre-generated test audio for the demo video analyzer.

## Files Included

### 🎤 Audio File (Pre-Generated)

**`realistic_demo.wav`** (4.7 MB) - Ready to use!

- ~90 seconds of synthetic speech simulating a product demo
- Contains realistic content: features, metrics, value propositions
- High transcription quality (91.8% confidence)
- Pre-generated and committed to repository

### 📄 Documentation

**`realistic_demo_script.md`**

- Original script used to generate the audio
- Shows the intended demo content

**`realistic_demo_transcript.md`**

- Actual Whisper transcription results
- Quality analysis and comparison with original

**`realistic_demo_transcript.txt`**

- Plain text version of the transcription
- Easy to use in scripts

### 🔧 Other Files

**`run_end_to_end_demo.py`** - End-to-end testing script with real API calls

---

## Quick Start

### Test the Full Pipeline

```bash
# From project root - test with pre-generated audio
python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai
```

**Expected output:**

- Transcription Quality: 🟢 HIGH (91.8% confidence)
- Overall Score: Evaluated on 6 criteria
- Feedback: 2 strengths + 2 improvements
- Transcript: ~1,970 characters

### View Audio Content

```bash
# View original demo script
cat test_data/realistic_demo_script.md

# View actual transcription
cat test_data/realistic_demo_transcript.txt
```

---

## Demo Content

The audio contains a realistic product demo covering:

1. **Introduction** - Speaker introduction and overview
2. **Dashboard Interface** - Layout and navigation features
3. **Report Creation** - Data sources (SQL, REST APIs, CSV)
4. **Visualizations** - Chart types and previews
5. **Collaboration** - Comments and notifications
6. **Performance** - Metrics (40% improvement, 3s vs 15s)
7. **Export Features** - PDF, Excel, PowerPoint
8. **Summary** - Key benefits and call-to-action

This mirrors what a real partner demo video would contain!

---

## Why Pre-Generated Audio?

✅ **Immediate testing** - No setup required  
✅ **Consistent results** - Same audio every time  
✅ **Realistic content** - Actual speech, not tones  
✅ **Full pipeline test** - Exercises transcription, evaluation, feedback  
✅ **Committed to repo** - No generation steps needed

The audio file is included in the repo so you can test the system immediately after cloning!

---

## Using in Tests

### Command Line

```bash
# Basic evaluation
python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai

# With different provider
python cli/evaluate_video.py test_data/realistic_demo.wav --provider anthropic
```

### Python API

```python
from src.video_evaluator import VideoEvaluator, AIProvider

evaluator = VideoEvaluator(provider=AIProvider.OPENAI)
result = evaluator.process("test_data/realistic_demo.wav", is_url=False, enable_vision=False)

print(f"Quality: {result['quality']['quality_rating']}")
print(f"Score: {result['evaluation']['overall']['weighted_score']:.1f}/10")
```

### Streamlit UI

```bash
streamlit run Home.py
# Upload test_data/realistic_demo.wav
```

---

## Transcription Quality

The pre-generated audio produces excellent transcription quality:

- **Confidence:** 91.8% (HIGH)
- **Speech Detection:** 96.7%
- **Compression Ratio:** 1.48 (good)
- **Segments:** 23 timestamped segments
- **Language:** English (en)
- **Warnings:** None

This makes it ideal for testing the evaluation and feedback systems!
