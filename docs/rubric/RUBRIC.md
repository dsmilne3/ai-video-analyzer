# Evaluation Rubric Configuration

The evaluation rubric is configured in `rubric.json` at the project root.

## File Structure

```json
{
  "criteria": [...],
  "scale": {"min": 1, "max": 10},
  "overall_method": "weighted_mean",
  "thresholds": {"pass": 6.5, "revise": 5.0}
}
```

## Criteria

Each criterion must have:

- **id**: Unique identifier (snake_case)
- **label**: Display name
- **desc**: Description shown to the AI evaluator
- **weight**: Importance factor (all weights should sum to 1.0)

### Current Criteria

| ID                     | Label                | Description                                      | Weight |
| ---------------------- | -------------------- | ------------------------------------------------ | ------ |
| `technical_accuracy`   | Technical Accuracy   | Correctness of technical claims and explanations | 0.30   |
| `clarity`              | Clarity              | How easy the explanation is to follow            | 0.25   |
| `completeness`         | Completeness         | Coverage of key features and flows               | 0.20   |
| `production_quality`   | Production Quality   | Audio clarity and pacing                         | 0.05   |
| `value_demonstration`  | Value Demonstration  | Articulation of business/customer value          | 0.15   |
| `multimodal_alignment` | Multimodal Alignment | Transcript and visuals are consistent            | 0.05   |

**Total weight: 1.00** (weights must sum to exactly 1.0)

## Scoring Scale

- **Minimum**: 1 (Poor)
- **Maximum**: 10 (Excellent)

Each criterion is scored on this 1-10 scale, then combined using weighted averaging.

## Pass/Fail Thresholds

The overall weighted score determines the pass status:

| Status     | Threshold             |
| ---------- | --------------------- |
| **Pass**   | Score ≥ 6.5           |
| **Revise** | Score ≥ 5.0 and < 6.5 |
| **Fail**   | Score < 5.0           |

## Modifying the Rubric

1. Edit `rubric.json` directly
2. Ensure all weights sum to 1.0
3. Keep criterion IDs unique and in snake_case
4. Test your changes: `python cli/evaluate_video.py test_data/realistic_demo.wav --provider openai`

## Automatic Validation

The system automatically validates `rubric.json` on load and checks for:

✅ **Required fields**: All top-level keys and criterion fields present  
✅ **Weight sum**: All criterion weights sum to 1.0 (±0.01 tolerance)  
✅ **Unique IDs**: No duplicate criterion IDs  
✅ **Valid ranges**: Weights between 0 and 1, thresholds properly ordered  
✅ **Correct types**: Numbers are numbers, strings are strings, etc.

**If validation fails**, you'll see a warning message and the system will use the built-in default rubric instead.

### Common Validation Errors

| Error                                               | Cause                               | Fix                               |
| --------------------------------------------------- | ----------------------------------- | --------------------------------- |
| "Criterion weights must sum to 1.0"                 | Weights don't add up to exactly 1.0 | Adjust weights so they sum to 1.0 |
| "Duplicate criterion ID: xyz"                       | Two criteria have the same ID       | Make IDs unique                   |
| "Missing required keys"                             | Missing top-level keys              | Add missing fields                |
| "revise threshold must be less than pass threshold" | Thresholds in wrong order           | Make sure revise < pass           |

### Example: Adding a New Criterion

```json
{
  "id": "engagement",
  "label": "Engagement",
  "desc": "How engaging and compelling the demo is for the audience",
  "weight": 0.05
}
```

**Remember to adjust other weights so the total still equals 1.0!**

### Example: Changing Thresholds

Make passing stricter:

```json
"thresholds": {
  "pass": 7.5,
  "revise": 6.0
}
```

Make passing easier:

```json
"thresholds": {
  "pass": 6.0,
  "revise": 4.5
}
```

## Fallback Behavior

If `rubric.json` is missing or invalid, the system will:

1. Print a warning message
2. Use the default rubric built into `src/video_evaluator.py`
3. Continue functioning normally

This ensures the tool always works even if the rubric file is accidentally deleted.

## Version Control

The `rubric.json` file is tracked in git, so you can:

- See rubric changes over time
- Revert to previous versions
- Share rubric updates with your team
- Create branches for experimental rubric variations
