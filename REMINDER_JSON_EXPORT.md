# Reminder: JSON Export Feature

**Date**: October 11, 2025  
**Status**: Removed for simplicity

## Context

JSON export functionality was removed from the video analyzer to simplify the output. Currently, only text files are saved to the `results/` folder.

## Why JSON Export Might Be Useful Later

If you want to implement any of these features, consider re-adding JSON export:

### 1. **Trend Analysis**

- Track how demo scores improve over time
- Identify common weak areas across multiple submissions
- Generate reports showing score distributions by criterion

### 2. **Dashboard Integration**

- Build a web dashboard showing evaluation metrics
- Create visualizations of score trends
- Display aggregated statistics across all evaluations

### 3. **Automated Reporting**

- Generate weekly/monthly summary reports
- Email stakeholders with score breakdowns
- Create comparative analysis between teams or time periods

### 4. **Third-Party Integration**

- Feed evaluation data into project management tools
- Sync scores with training systems
- Export to business intelligence tools

### 5. **Bulk Processing**

- Programmatically process multiple evaluation results
- Batch analysis of historical evaluations
- Data mining for patterns and insights

### 6. **API Development**

- Build an API endpoint that returns structured evaluation data
- Allow other systems to query evaluation results
- Enable automated workflows based on scores

## How to Re-Enable JSON Export

The infrastructure is already in place in `src/video_evaluator.py`:

```python
# In the save_results() function, it already supports both formats:
save_results(result, filename, output_format='txt')  # Text only
save_results(result, filename, output_format='json')  # Add this back for JSON
```

### Quick Steps:

1. **Update UI** (`pages/2_Analyze_Video.py`):

   ```python
   # Add back JSON saving
   saved_json_path = save_results(res, original_filename, output_format='json')

   # Add back JSON download button
   with open(saved_json_path, 'r') as f:
       json_content = f.read()
   st.download_button(
       label="📊 Download JSON Data",
       data=json_content,
       file_name=f"{original_filename.split('.')[0]}_results.json",
       mime="application/json"
   )
   ```

2. **Update .gitignore** (`results/.gitignore`):

   ```
   # Ignore all result files
   *.txt
   *.json  # Add this back
   ```

3. **Update CLI** (if desired) (`cli/evaluate_video.py`):
   ```python
   # Add JSON saving
   saved_json_path = save_results(result, args.file, output_format='json')
   ```

## Current State

- ✅ Text files saved with timestamps (`filename_results_YYYYMMDD_HHMMSS.txt`)
- ✅ Text download button in UI
- ❌ JSON export disabled (both UI and file saving)
- ❌ JSON download button removed from UI

## Decision Point

When you need any of the use cases listed above, revisit this reminder and re-enable JSON export. The code is already structured to support it with minimal changes.

---

**Note**: You can delete this file if you decide JSON export is never needed, or keep it as a reference for future enhancements.
