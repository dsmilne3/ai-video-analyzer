# Results Saving Feature

## Overview

The video evaluator now **automatically saves results** to the `results/` folder after each evaluation, making it easy to review, share, and archive evaluation outputs.

## Implementation

### Core Function: `save_results()`

Located in `src/video_evaluator.py`, this function handles result persistence:

```python
def save_results(result: Dict[str, Any], input_filename: str, output_format: str = 'txt') -> str:
    """Save evaluation results to the results/ folder with timestamp to prevent overwrites."""
```

**Features**:

- Creates `results/` directory if it doesn't exist
- Generates timestamped filename: `<filename>_results_YYYYMMDD_HHMMSS.{txt|json}`
- Supports two formats: human-readable text and machine-readable JSON
- Prevents overwrites by using unique timestamps
- Returns the path to the saved file

### UI Integration

**File**: `app/reviewer.py`

The Streamlit UI saves both text and JSON formats:

```python
# Save results to file
saved_txt_path = save_results(res, original_filename, output_format='txt')
saved_json_path = save_results(res, original_filename, output_format='json')

# Provide download buttons
st.download_button("📄 Download Text Report", data=txt_content, ...)
st.download_button("📊 Download JSON Data", data=json_content, ...)
```

**User Experience**:

1. Upload/enter URL and evaluate video in UI
2. View formatted results in browser
3. Results automatically saved to `results/`
4. Download buttons for both text and JSON reports
5. Success message: `💾 Results saved to results/ folder`

## File Formats

### Text Format (.txt)

**Purpose**: Human-readable format for review and sharing

**Structure**:

```
======================================================================
DEMO VIDEO EVALUATION RESULTS
======================================================================

Status: 🟢 PASS
Overall Score: 7.5/10
Summary: ...

Transcription Quality: HIGH
  Confidence: 91.8%
  Speech Detection: 96.7%
  Compression Ratio: 1.48

----------------------------------------------------------------------
FEEDBACK (SUPPORTIVE TONE)
----------------------------------------------------------------------

✓ STRENGTHS:
1. Technical Accuracy
   ...

→ AREAS FOR IMPROVEMENT:
1. Completeness
   ...

----------------------------------------------------------------------
FULL TRANSCRIPT
----------------------------------------------------------------------
...

----------------------------------------------------------------------
FULL JSON OUTPUT
----------------------------------------------------------------------
{...}
```

### JSON Format (.json)

**Purpose**: Machine-readable format for programmatic access

**Current Status**: ⚠️ **Disabled** - JSON export is currently disabled in the UI for simplicity. The infrastructure still exists in the codebase.

**To Re-enable**: See `REMINDER_JSON_EXPORT.md` for use cases (dashboards, APIs, bulk analysis) and step-by-step instructions.

**Structure** (when enabled):

```json
{
  "transcript": "...",
  "language": "en",
  "quality": {...},
  "evaluation": {...},
  "feedback": {...}
}
```

## Directory Structure

```
results/
├── .gitignore              # Ignores *.txt files
├── README.md               # Documentation about results
├── video1_results_20251010_130222.txt      # Saved evaluations (git-ignored)
├── video2_results_20251010_143015.txt
└── ...
```

**Note**: Filenames now include timestamps to prevent overwrites.

## Privacy & Version Control

**Git Ignore Configuration**: `results/.gitignore`

```gitignore
# Ignore all result files
*.txt
*.json

# Keep the directory structure
!.gitignore
```

**Why git-ignore results?**:

- Evaluation outputs contain full transcripts and detailed feedback
- Demo content may be proprietary or confidential
- Prevents repository bloat
- Results are project-specific and don't need version control

**What IS tracked**:

- `.gitignore` file
- `README.md` documentation
- Directory structure

## Use Cases

### 1. Share Feedback with Demo Submitters

```bash
# Send text file via email/Slack
cat results/partner_demo_results.txt
```

The text format is designed to be easily readable and includes:

- Clear status and score
- Supportive feedback tone
- Actionable improvement suggestions

### 2. Batch Analysis

```python
import json
import glob

# Load all evaluations
results = []
for file in glob.glob("results/*_results.json"):
    with open(file) as f:
        results.append(json.load(f))

# Analyze trends
pass_rate = sum(1 for r in results
                if r['evaluation']['overall']['pass_status'] == 'pass') / len(results)
print(f"Pass rate: {pass_rate:.1%}")
```

### 3. Archive Historical Results

```bash
# Create monthly archives
mkdir -p archives/2025-10
mv results/*_results.* archives/2025-10/
```

### 4. Compare Before/After

In the Streamlit UI:

1. **First evaluation:** Upload `demo_v1.wav`, evaluate, note the timestamp
2. **Make improvements** to the demo
3. **Second evaluation:** Upload the improved version, evaluate
4. **Compare:** View both timestamped result files in the `results/` directory

## Documentation Updates

### README.md

Added "Results Storage" section documenting:

- Auto-save functionality
- File formats and locations
- UI behavior
- Example usage

### Project Structure

Updated to include:

```
├── results/                  # Auto-saved evaluation results (git-ignored)
│   └── .gitignore            # Keeps results private
```

### results/README.md

Created comprehensive documentation covering:

- File naming conventions
- Format specifications
- Git ignore strategy
- Use cases and examples
- Privacy considerations

## Testing

### UI Test

```bash
# Start UI
streamlit run app/reviewer.py

# Upload test_data/realistic_demo.wav
# Evaluate with default rubric
# Verify:
#   - Success message: "💾 Results saved to results/ folder"
#   - Download buttons for text and JSON
#   - Both files created in results/
```

**Expected**: Text and JSON files with complete evaluation output

## Benefits

### For Users

- **Permanent records** - Don't lose evaluation results
- **No overwrites** - Timestamped files preserve all evaluation history
- **Easy sharing** - Text format designed for submitters
- **Automation** - JSON format for batch processing
- **Comparison** - Compare multiple versions easily across timestamps
- **Track progress** - See improvements over multiple evaluation runs

### For Development

- **Privacy** - Results stay local (git-ignored)
- **Testing** - Saved outputs for comparison
- **Debugging** - Full evaluation data preserved
- **Analytics** - JSON format enables trend analysis
- **History** - Complete record of all test runs

### For Operations

- **Archival** - Historical record of evaluations with timestamps
- **Auditing** - Complete evaluation history, never lost
- **Reporting** - Aggregate statistics across evaluations
- **Quality control** - Track evaluation patterns over time
- **Trend analysis** - Compare results across multiple runs

## Future Enhancements

Potential improvements for the results system:

1. **Configurable output directory** - Allow users to specify save location
2. **Automatic archival** - Move old results to dated folders
3. **Results dashboard** - Web UI to browse all saved evaluations
4. **Export formats** - Add PDF, CSV, or Excel export options
5. **Cloud sync** - Optional backup to S3/GCS
6. **Comparison tool** - Side-by-side comparison of two evaluations
7. **Statistics dashboard** - Aggregate metrics across all results

## Conclusion

The results saving feature provides a complete solution for persisting evaluation outputs in both human-readable and machine-readable formats. It integrates seamlessly with the UI workflow, respects privacy through git-ignore, and enables a wide range of use cases from simple sharing to complex analytics.

**Key Achievements**:
✅ Automatic save after every evaluation  
✅ Two formats (text for humans, JSON for machines)  
✅ Privacy-first (git-ignored by default)  
✅ UI integration  
✅ User notifications and download options  
✅ Comprehensive documentation  
✅ Ready for production use
