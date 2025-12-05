# Reminder: Rubric Helper Script

**Date Created**: October 10, 2025  
**Reminder Date**: October 17, 2025 (one week)

## Context

You asked about creating custom rubrics and whether to use equal weights when a rubric doesn't have initial weights. Equal weight distribution (1.0 ÷ number of criteria) was confirmed as a good approach.

## Helper Script Idea

Create a tool to make rubric creation easier with these features:

### 1. Interactive Rubric Creation

- Prompt for rubric name and description
- Ask how many criteria to add
- For each criterion, collect name and description
- Automatically calculate equal weights (1.0 ÷ number of criteria)
- Adjust the last weight to ensure perfect 1.0 sum (handling rounding)

### 2. Templates

- Offer templates (e.g., "sales demo", "technical demo", "training video")
- Pre-fill common criteria for each template
- Allow customization of template criteria

### 3. Validation

- Check that weights sum to exactly 1.0
- Ensure criterion names are unique
- Validate JSON structure before saving

### 4. Output

- Save to `rubrics/` directory with `.json` extension
- Pretty-print JSON for readability
- Display a summary of the created rubric

## Example Usage

```bash
# Interactive mode
python tools/create_rubric.py

# Quick mode with template
python tools/create_rubric.py --template sales --name my-sales-rubric

# Specify number of criteria upfront
python tools/create_rubric.py --criteria 5 --name custom-rubric
```

## Benefits

- No need to manually calculate equal weights
- Don't have to remember the exact JSON structure
- No worry about rounding errors in weights
- Automatic validation that everything sums to 1.0

## Next Steps

If you want to implement this:

1. Create `tools/` directory
2. Create `tools/create_rubric.py` script
3. Add argparse for CLI arguments
4. Implement interactive prompts
5. Add templates for common use cases
6. Test with various criteria counts

---

**Note**: You can delete this file once you've seen the reminder or if you decide not to implement this feature.
