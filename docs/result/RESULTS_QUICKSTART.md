# Quick Reference: Results Saving

## What Was Implemented

✅ **Automatic results saving** to `results/` folder after each evaluation  
✅ **Timestamped filenames** to prevent overwrites and preserve history  
✅ **Two formats**: Human-readable text (.txt) and machine-readable JSON (.json)  
✅ **UI integration**: Download buttons for both formats and save confirmation  
✅ **Privacy**: Results folder is git-ignored

## File Locations

### UI (Streamlit)

- **Saved formats**: Text AND JSON
- **Locations**:
  - `results/<filename>_results_YYYYMMDD_HHMMSS.txt`
  - `results/<filename>_results_YYYYMMDD_HHMMSS.json`
- **Plus**: Download buttons in the UI for immediate access

## Quick Usage

### UI

```bash
# Start UI
streamlit run Home.py

# 1. Upload video/audio or provide URL
# 2. Configure evaluation settings (rubric, provider, etc.)
# 3. Click "Evaluate Video"
# 4. See results displayed
# 5. See: "💾 Results saved to results/ folder"
# 6. Click download buttons for text or JSON formats
```

## File Structure

### Text Format (.txt)

- Complete evaluation results
- Feedback section (strengths + improvements)
- Full transcript
- Quality metrics
- JSON output at the end

### JSON Format (.json)

- Same data as text, but in JSON structure
- Perfect for programmatic access
- Includes all evaluation details

## Key Files Modified

1. **src/video_evaluator.py**

   - Added `save_results()` function
   - Handles both text and JSON formats

2. **app/reviewer.py**

   - Imports `save_results`
   - Saves both formats automatically
   - Adds download buttons for user access

3. **results/** (new directory)

   - `.gitignore` - ignores result files
   - `README.md` - comprehensive documentation

4. **README.md**
   - Added "Results Storage" section
   - Updated project structure

## Documentation Created

1. **results/README.md** - Complete results documentation
2. **RESULTS_FEATURE.md** - Implementation details and use cases
3. **README.md** - User-facing documentation updated

## Testing Performed

✅ UI saves both text and JSON results correctly  
✅ File naming convention works with timestamps  
✅ Git ignore configuration in place  
✅ Confirmation messages display properly  
✅ Download buttons work for both formats

## What Users See

### UI Output (after evaluation)

```
✅ Success message: "💾 Results saved to results/ folder"
📄 [Download Text Report] button
📊 [Download JSON Data] button
```

## Privacy & Git

The `results/.gitignore` file ensures:

- All `.txt` files are ignored
- All `.json` files are ignored
- Only `.gitignore` and `README.md` are tracked
- Results stay local and private

## Benefits

- **Never lose results** - Auto-saved every time
- **Easy sharing** - Send text file to submitters
- **Automation ready** - JSON format for scripts
- **Archive friendly** - Move old results to dated folders
- **Privacy first** - Not committed to git

---

**Status**: ✅ Complete and tested  
**Ready for**: Production use
