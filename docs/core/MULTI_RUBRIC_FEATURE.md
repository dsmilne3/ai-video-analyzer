# Multi-Rubric Support Feature

**Status:** ✅ Fully Implemented  
**Date:** October 10, 2025

## Overview

The demo video analyzer now supports multiple evaluation rubrics optimized for different types of demonstrations. Users can select from pre-configured rubrics or create custom ones based on their needs.

## Features Implemented

### 1. Three Pre-Built Rubrics

#### 📋 Default Rubric (`rubrics/default.json`)

- **Use Case:** General partner demo videos
- **Emphasis:** Balanced across all dimensions
- **Pass Threshold:** ≥ 6.5/10
- **Criteria:** Technical Accuracy (30%), Clarity (25%), Completeness (20%), Value Demonstration (15%), Production Quality (5%), Multimodal Alignment (5%)

#### 💼 Sales Demo Rubric (`rubrics/sales-demo.json`)

- **Use Case:** Customer-facing sales demonstrations
- **Emphasis:** Business value and engagement
- **Pass Threshold:** ≥ 7.0/10 (higher bar)
- **Criteria:** Value Demonstration (35%), Clarity (25%), Engagement (20%), Production Quality (10%), Completeness (10%)

#### 🔧 Technical Demo Rubric (`rubrics/technical-demo.json`)

- **Use Case:** Technical partner demos and deep-dive presentations
- **Emphasis:** Technical accuracy and completeness
- **Pass Threshold:** ≥ 7.0/10 (higher bar)
- **Criteria:** Technical Accuracy (40%), Completeness (25%), Clarity (20%), Code Quality (10%), Production Quality (5%)

### 2. UI Enhancements

The Streamlit web interface provides:

- **Rubric Dropdown:** Select from available rubrics in the sidebar before analysis
- **Description Display:** Shows rubric description and criteria below selection
- **Default Selection:** Default rubric pre-selected
- **Dynamic Evaluation:** Results adapt to selected rubric

**UI includes:**

- Selected rubric name during analysis
- Feedback based on rubric-specific criteria
- Scores for rubric-defined dimensions

### 3. Streamlit UI Enhancements

- **Rubric Dropdown:** Select from available rubrics before analysis
- **Description Display:** Shows rubric description below selection
- **Default Selection:** Default rubric pre-selected
- **Dynamic Evaluation:** Results adapt to selected rubric

### 4. Python API Support

```python
from src.video_evaluator import VideoEvaluator, AIProvider, list_available_rubrics

# List available rubrics
rubrics = list_available_rubrics()
for rubric in rubrics:
    print(f"{rubric['name']}: {rubric['description']}")

# Use specific rubric
evaluator = VideoEvaluator(
    provider=AIProvider.OPENAI,
    rubric_name="sales-demo"
)
result = evaluator.process("video.mp4", is_url=False, enable_vision=False)
```

### 5. Custom Rubric Support

Users can create custom rubrics by adding JSON files to the `rubrics/` directory. The system:

- ✅ Automatically discovers new rubric files
- ✅ Validates rubric structure
- ✅ Falls back to default on validation errors
- ✅ Supports any number of criteria
- ✅ Allows custom weights and thresholds

See `rubrics/README.md` for detailed instructions.

## Technical Implementation

### Core Changes

1. **`src/video_evaluator.py`**

   - `load_rubric(rubric_name)` - Loads specific rubric by name
   - `list_available_rubrics()` - Returns all available rubrics with metadata
   - `VideoEvaluator.__init__(rubric_name)` - Accepts rubric parameter
   - Changed all `RUBRIC` references to `self.rubric` for instance-specific rubrics
   - Dynamic LLM prompt generation based on rubric criteria

2. **`pages/2_Analyze_Video.py`**

   - Added rubric selection dropdown in sidebar
   - Displays rubric description and criteria
   - Passes selected rubric to evaluator

### Backward Compatibility

- ✅ Existing code without rubric parameter uses "default" rubric
- ✅ Old `rubric.json` location still supported (falls back if rubrics/ not found)
- ✅ All existing API calls work without modification
- ✅ Default rubric matches original hardcoded criteria

## Validation

The system validates rubrics on load:

- Weights must sum to 1.0 (within 0.01 tolerance)
- Required fields: criteria, scale, overall_method, thresholds
- Each criterion must have: id, label, desc, weight
- No duplicate criterion IDs
- Thresholds: revise < pass
- Scale: min < max

Invalid rubrics trigger a warning and fall back to default.

## Documentation Updates

Updated the following files:

- ✅ `README.md` - Added rubrics section, updated examples
- ✅ `QUICKSTART.md` - Added rubric selection examples, updated commands
- ✅ `rubrics/README.md` - Complete rubric documentation
- ✅ Project structure diagrams updated

## Testing

Verified functionality:

- ✅ `--list-rubrics` displays all rubrics correctly
- ✅ Default rubric evaluation matches original behavior
- ✅ Sales demo rubric emphasizes value demonstration (35% weight)
- ✅ Technical rubric emphasizes technical accuracy (40% weight)
- ✅ Custom rubric validation works correctly
- ✅ UI dropdown populates and selects correctly
- ✅ Feedback adapts to rubric-specific criteria

## Usage Examples

### Scenario 1: Sales Team Demo Review

In the Streamlit UI:

1. Select "sales-demo" rubric from the sidebar dropdown
2. Upload or provide URL for `sales_pitch.mp4`
3. Choose OpenAI provider
4. Click "Evaluate Video"

**Result:** Emphasizes business value (35%), engagement (20%), and clarity (25%)

### Scenario 2: Technical Partnership Review

In the Streamlit UI:

1. Select "technical-demo" rubric from the sidebar dropdown
2. Upload or provide URL for `technical_demo.mp4`
3. Choose OpenAI provider
4. Click "Evaluate Video"

**Result:** Emphasizes technical accuracy (40%), completeness (25%), and code quality (10%)

### Scenario 3: General Partner Demo

In the Streamlit UI:

1. Use default rubric (pre-selected)
2. Upload or provide URL for `partner_demo.mp4`
3. Choose OpenAI provider
4. Click "Evaluate Video"

**Result:** Balanced evaluation across all standard criteria

## Benefits

1. **Flexibility:** Different rubrics for different demo types
2. **Customization:** Easy to create custom rubrics for specific needs
3. **Clarity:** Clear feedback based on relevant criteria
4. **Standards:** Higher pass thresholds for sales/technical demos
5. **Extensibility:** System adapts to any number of criteria automatically

## Future Enhancements

Potential improvements:

- [ ] Rubric versioning and history tracking
- [ ] Per-rubric feedback templates
- [ ] Rubric analytics (average scores per criterion)
- [ ] UI rubric editor
- [ ] Export/import rubrics
- [ ] Team-specific rubric collections

## Migration Notes

**Existing users:** No action required. The default rubric matches the original hardcoded behavior.

**New users:** Choose appropriate rubric based on demo type:

- Sales demos → `sales-demo`
- Technical demos → `technical-demo`
- General demos → `default` (or omit --rubric)

---

**Implementation Complete:** All features working and documented. System tested with multiple rubrics and verified to produce appropriate feedback for each demo type.
