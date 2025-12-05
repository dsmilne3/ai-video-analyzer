# Transcription Quality Reporting

**Date:** October 9, 2025  
**Feature:** Whisper quality metrics surfaced to users

---

## Overview

The video evaluator now provides **comprehensive transcription quality metrics** to help users understand the reliability of the Whisper transcription. This addresses the need to know whether poor evaluation scores are due to content issues or transcription problems.

---

## What Was Added

### Quality Metrics Captured

Whisper provides three key metrics per segment:

1. **`avg_logprob`** - Average log probability
   - Range: ~-1.5 to 0 (higher is better)
   - Indicates Whisper's confidence in the transcription
2. **`compression_ratio`** - Text compression ratio
   - Normal range: 1.2 to 2.0
   - Values > 2.5 indicate possible repetition or hallucination
3. **`no_speech_prob`** - Probability of no speech
   - Range: 0 to 1 (lower is better)
   - Indicates likelihood the segment contains silence/noise

### Calculated Summary Metrics

The system calculates overall quality from all segments:

- **`avg_confidence`** - Overall confidence (0-100%)
  - Derived from avg_logprob, normalized to percentage
  - \>80% = high confidence, 60-80% = medium, <60% = low
- **`speech_percentage`** - Percentage of audio containing speech
  - Inverse of no_speech_prob
  - \>85% = excellent, 70-85% = good, <70% = may have issues
- **`avg_compression_ratio`** - Average text compression
  - <2.0 = good, 2.0-2.5 = acceptable, \>2.5 = may have repetition
- **`quality_rating`** - Overall assessment
  - **HIGH** 🟢: confidence ≥80%, speech ≥85%, compression <2.0
  - **MEDIUM** 🟡: confidence ≥60%, speech ≥70%
  - **LOW** 🔴: below medium thresholds
- **`warnings`** - List of potential issues
  - Low confidence warning
  - High compression warning
  - Low speech detection warning

---

## Example Output

### Streamlit UI Output

The web interface displays transcription quality metrics prominently:

- **Quality Badge:** 🟢 HIGH / 🟡 MEDIUM / 🔴 LOW with color coding
- **Detailed Metrics:** Confidence percentage, speech detection percentage, compression ratio
- **Warnings:** Expandable section showing any quality warnings
- **Quality Impact:** Note about how transcription quality affects evaluation reliability

Example display:

```
Transcription Quality: 🟢 HIGH
  Confidence: 91.8%
  Speech Detection: 96.7%
  Compression Ratio: 1.48
```

### JSON Output

```json
{
  "quality": {
    "avg_confidence": 91.8,
    "avg_compression_ratio": 1.48,
    "speech_percentage": 96.7,
    "quality_rating": "high",
    "warnings": [],
    "details": {
      "avg_logprob": -0.123,
      "num_segments": 23
    }
  }
}
```

### With Warnings (Example)

```
Transcription Quality: 🟡 MEDIUM
  Confidence: 72.3%
  Speech Detection: 81.5%
  Compression Ratio: 2.1

  ⚠️  Quality Warnings:
     - Low speech detection - audio may contain long silences or background noise
```

---

## Streamlit UI Display

The web interface shows quality metrics prominently:

```
🎤 Transcription Quality

┌──────────────┬──────────────┬───────────────────┐
│ Quality      │ Confidence   │ Speech Detection  │
│ 🟢 HIGH      │ 91.8%        │ 96.7%             │
└──────────────┴──────────────┴───────────────────┘

⚠️ Quality Warnings:
  (none for high quality transcriptions)

📊 View Detailed Quality Metrics ▼
  Compression Ratio: 1.48
  Segments Analyzed: 23
  Average Log Probability: -0.123
```

---

## Code Changes

### Modified Files

1. **`src/video_evaluator.py`** (+70 lines)

   - Updated `transcribe_with_timestamps()` to capture quality metrics
   - Added `_calculate_transcription_quality()` method
   - Added `quality` field to result dictionary

2. **`pages/2_Analyze_Video.py`** (+37 lines)

   - Added quality metrics section in results display
   - Color-coded quality rating badges
   - Three-column layout for key metrics
   - Expandable detailed metrics and warnings

---

## Benefits

### For Users

✅ **Trust in Results**: Know if low scores are due to poor transcription  
✅ **Audio Quality Feedback**: Understand if re-recording with better audio would help  
✅ **Transparency**: See exactly how confident the system is  
✅ **Actionable**: Warnings provide specific guidance

### For Reviewers

✅ **Quality Assurance**: Identify transcriptions that need manual review  
✅ **Escalation Logic**: Use quality metrics to route to human reviewers  
✅ **Audit Trail**: Document transcription quality alongside evaluation  
✅ **Debugging**: Distinguish between content and transcription issues

### For System

✅ **Automatic Escalation**: Low quality → flag for human review  
✅ **Cost Optimization**: High quality → trust LLM evaluation  
✅ **Metrics Tracking**: Monitor transcription performance over time  
✅ **Continuous Improvement**: Identify problematic audio types

---

## Interpreting Metrics

### Confidence Levels

| Confidence | Meaning                   | Action                            |
| ---------- | ------------------------- | --------------------------------- |
| 90-100%    | Excellent - Very reliable | Trust fully                       |
| 80-89%     | High - Generally reliable | Use confidently                   |
| 60-79%     | Medium - Mostly reliable  | Review key sections               |
| 40-59%     | Low - May have errors     | Manual review needed              |
| 0-39%      | Very low - Likely errors  | Re-record or manual transcription |

### Speech Detection

| Speech % | Meaning   | Common Causes                  |
| -------- | --------- | ------------------------------ |
| 95-100%  | Excellent | Clean audio, continuous speech |
| 85-94%   | Good      | Normal pauses, good audio      |
| 70-84%   | Fair      | Long pauses, background noise  |
| 50-69%   | Poor      | Silent sections, music, noise  |
| 0-49%    | Very poor | Mostly non-speech audio        |

### Compression Ratio

| Ratio   | Meaning    | Interpretation          |
| ------- | ---------- | ----------------------- |
| 1.0-1.5 | Excellent  | Natural, varied speech  |
| 1.5-2.0 | Good       | Normal repetition       |
| 2.0-2.5 | Acceptable | Some repetitive content |
| 2.5-3.0 | Warning    | May contain loops       |
| >3.0    | Problem    | Likely hallucination    |

---

## Use Cases

### 1. Automatic Escalation

```python
result = evaluator.process("video.mp4", is_url=False, enable_vision=False)

if result['quality']['quality_rating'] == 'low':
    # Route to human reviewer
    send_to_manual_review(result)
elif result['quality']['avg_confidence'] < 70:
    # Flag for spot-check
    flag_for_review(result)
else:
    # Trust automated evaluation
    process_normally(result)
```

### 2. User Feedback

```python
quality = result['quality']

if quality['warnings']:
    print("⚠️  Your audio quality could be improved:")
    for warning in quality['warnings']:
        print(f"  - {warning}")
    print("\nTips for better results:")
    print("  • Use a good microphone")
    print("  • Record in a quiet environment")
    print("  • Speak clearly and at a steady pace")
```

### 3. Batch Processing

```python
for video in video_batch:
    result = evaluator.process(video)

    # Log quality for analysis
    log_quality_metrics(
        video_id=video.id,
        confidence=result['quality']['avg_confidence'],
        rating=result['quality']['quality_rating']
    )

    # Generate report
    if result['quality']['quality_rating'] != 'high':
        add_to_review_queue(video, result)
```

---

## Future Enhancements

Potential improvements:

- [ ] Per-segment quality visualization (timeline view)
- [ ] Historical quality trends per partner
- [ ] Automatic audio enhancement suggestions
- [ ] Integration with audio quality pre-check tools
- [ ] Machine learning to improve quality thresholds
- [ ] Custom quality thresholds per use case

---

## Technical Details

### Quality Calculation Algorithm

```python
# Convert logprob (-1.5 to 0) to confidence (0 to 100)
confidence = max(0, min(100, (avg_logprob + 1.5) * 66.67))

# Calculate speech percentage
speech_percentage = (1 - avg_no_speech) * 100

# Determine quality rating
if confidence >= 80 and speech_percentage >= 85 and compression < 2.0:
    rating = 'high'
elif confidence >= 60 and speech_percentage >= 70:
    rating = 'medium'
else:
    rating = 'low'
```

### Warning Thresholds

```python
if avg_confidence < 50:
    warnings.append('Low transcription confidence')

if avg_compression > 2.5:
    warnings.append('High compression ratio - may contain repetitions')

if speech_percentage < 70:
    warnings.append('Low speech detection - may contain silences/noise')
```

---

## Related Documentation

- [README.md](../README.md) - Main project documentation
- [FEEDBACK_FEATURE.md](FEEDBACK_FEATURE.md) - Qualitative feedback
- [REALISTIC_TEST_AUDIO.md](REALISTIC_TEST_AUDIO.md) - Test audio generation

---

## Summary

✅ **Feature successfully implemented**  
✅ **Quality metrics captured from Whisper**  
✅ **Summary metrics calculated**  
✅ **Streamlit UI enhanced**  
✅ **Warnings generated for issues**  
✅ **No breaking changes**

Users now have full visibility into transcription quality, enabling them to trust high-quality transcriptions and identify problematic cases that need attention!
