# Evaluation Rubrics

This directory contains JSON-based rubrics for evaluating demo videos. Each rubric defines categories with nested criteria, weights, and thresholds for different types of demonstrations.

The system includes automatic versioning and backup functionality to prevent data loss and enable easy rollback to previous versions.

## New Hierarchical Format

As of version 1.0, rubrics use a hierarchical structure with categories containing related criteria. This provides better organization and more detailed scoring breakdowns.

### Key Changes from Old Format:

- **Categories**: Rubrics are organized into logical categories (e.g., "Content Quality", "Presentation")
- **Point-based Scoring**: Each criterion has max points instead of weights
- **Versioning**: Rubrics include `rubric_id` and `version` fields with automatic backup system
- **Category Breakdowns**: Results show scores by category for better analysis

## Available Rubrics

### 📋 default.json

**Name:** Default Rubric  
**Version:** 1.0  
**Description:** Balanced rubric for general partner demo videos

**Categories:**

#### 📂 Content Quality (80% weight, 40 points max)

- Technical Accuracy (12 points) - Correctness of technical claims and explanations
- Clarity (10 points) - How easy the explanation is to follow
- Completeness (8 points) - Coverage of key features and flows
- Value Demonstration (10 points) - Articulation of business/customer value

#### 📂 Presentation (20% weight, 10 points max)

- Production Quality (5 points) - Audio clarity and pacing
- Multimodal Alignment (5 points) - Transcript and visuals are consistent

**Thresholds:**

- Pass: ≥32 points
- Revise: ≥25 points

### 💼 sales-demo.json

**Name:** Sales Demo Rubric  
**Version:** 1.0  
**Description:** Optimized for customer-facing sales demonstrations

**Categories:**

#### 📂 Sales Impact (55% weight, 28 points max)

- Value Demonstration (18 points) - Clear articulation of business value and ROI
- Engagement (10 points) - How compelling and engaging the presentation is

#### 📂 Content Delivery (35% weight, 17 points max)

- Clarity (12 points) - How easy the explanation is to follow for non-technical audience
- Completeness (5 points) - Coverage of key features relevant to the sales pitch

#### 📂 Presentation (10% weight, 5 points max)

- Production Quality (5 points) - Audio clarity, pacing, and professional presentation

**Thresholds:**

- Pass: ≥35 points (higher bar for sales demos)
- Revise: ≥28 points

### 🔧 technical-demo.json

**Name:** Technical Demo Rubric  
**Version:** 1.0  
**Description:** Optimized for technical partner demos and deep-dive presentations

**Categories:**

#### 📂 Technical Depth (75% weight, 38 points max)

- Technical Accuracy (20 points) - Correctness and depth of technical claims and explanations
- Completeness (13 points) - Thorough coverage of technical features and implementation details
- Code Quality (5 points) - Quality of code examples and technical demonstrations

#### 📂 Communication (20% weight, 10 points max)

- Clarity (10 points) - How easy complex technical concepts are to understand

#### 📂 Presentation (5% weight, 2 points max)

- Production Quality (2 points) - Audio clarity and pacing

**Thresholds:**

- Pass: ≥35 points (higher bar for technical accuracy)
- Revise: ≥28 points

## Usage

### CLI

```bash
# List available rubrics
python cli/evaluate_video.py --list-rubrics

# Use a specific rubric
python cli/evaluate_video.py video.mp4 --rubric sales-demo

# Default rubric (if not specified)
python cli/evaluate_video.py video.mp4
```

### Rubric Management

Use the interactive rubric helper script to manage rubrics:

```bash
# Create a new rubric interactively
python rubric_helper.py create

# List all available rubrics
python rubric_helper.py list

# Show details of a specific rubric
python rubric_helper.py show sales-demo

# Edit an existing rubric (creates automatic backup)
python rubric_helper.py edit sales-demo

# List all versions of a rubric
python rubric_helper.py versions sales-demo

# Restore a rubric to a previous version
python rubric_helper.py restore sales-demo 1.0

# Validate a rubric file
python rubric_helper.py validate sales-demo
```

### Streamlit UI

The UI provides a dropdown menu to select from available rubrics. The default rubric is pre-selected. Results now show category breakdowns alongside overall scores.

### Python API

```python
from src.video_evaluator import VideoEvaluator, AIProvider

# Use a specific rubric
evaluator = VideoEvaluator(
    provider=AIProvider.OPENAI,
    rubric_name="sales-demo"
)

# List available rubrics
from src.video_evaluator import list_available_rubrics
rubrics = list_available_rubrics()
for rubric in rubrics:
    print(f"{rubric['name']}: {rubric['description']}")
```

## Creating Custom Rubrics

Use the interactive rubric helper script to create new rubrics:

```bash
python rubric_helper.py create
```

The script will guide you through creating a hierarchical rubric with categories and criteria.

### Manual Creation

To create a custom rubric manually, add a new JSON file to this directory following this structure:

```json
{
  "rubric_id": "my-custom-rubric",
  "version": "1.0",
  "name": "My Custom Rubric",
  "description": "Description of when to use this rubric",
  "categories": [
    {
      "category_id": "content_quality",
      "label": "Content Quality",
      "weight": 0.8,
      "max_points": 40,
      "criteria": [
        {
          "criterion_id": "technical_accuracy",
          "label": "Technical Accuracy",
          "desc": "Correctness of technical claims and explanations",
          "max_points": 12
        }
      ]
    }
  ],
  "scale": {
    "min": 0,
    "max": 50
  },
  "overall_method": "total_points",
  "thresholds": {
    "pass": 35,
    "revise": 28
  }
}
```

### Requirements:

- All category weights must sum to 1.0
- Each category must have: `category_id`, `label`, `weight`, `max_points`, `criteria`
- Each criterion must have: `criterion_id`, `label`, `desc`, `max_points`
- Category `max_points` should equal the sum of its criteria `max_points`
- Thresholds: `revise` must be < `pass`
- Scale: `min` should be 0, `max` should equal total possible points

### Tips:

- Use snake_case for category and criterion IDs (e.g., `technical_accuracy`)
- Higher category weights emphasize that category more in the overall score
- Adjust thresholds based on your quality standards
- Different demo types may warrant different passing scores
- Use the rubric helper script for easier creation: `python rubric_helper.py create`

## Versioning and Backup System

The rubric system includes automatic versioning and backup functionality to prevent data loss and enable rollback to previous versions.

### Automatic Backups

- **When editing**: Every edit automatically creates a timestamped backup in `rubrics/versions/`
- **Backup naming**: `filename.v{major}.{minor}.{timestamp}.json` (e.g., `sales-demo.v1.0.20251021_143022.json`)
- **Version increment**: All edits increment the minor version (e.g., `1.0` → `1.1` → `1.2`)

### Version Management Commands

```bash
# View all versions of a rubric (current + backups)
python rubric_helper.py versions sales-demo

# Example output:
📋 Versions for rubric 'sales-demo':
============================================================
📄 Version 1.2
   File: sales-demo.json

💾 Version 1.1 (20251021_143022)
   File: sales-demo.v1.1.20251021_143022.json

💾 Version 1.0 (20251021_140000)
   File: sales-demo.v1.0.20251021_140000.json

# Restore to a specific version
python rubric_helper.py restore sales-demo 1.0
```

### Versioning Behavior

- **Minor increments only**: All edits are treated as minor version changes (no major version changes)
- **Automatic**: Version numbers increment automatically when editing - no manual version management needed
- **Safe rollback**: Restore any previous version without losing current work
- **Timestamped backups**: Each backup includes the exact date/time it was created

### Best Practices

- **Regular editing**: Edit rubrics frequently as needed - backups are automatic
- **Version checking**: Use `versions` command to see edit history before major changes
- **Safe experimentation**: Test changes knowing you can always restore to previous versions
- **Backup retention**: Old versions are kept indefinitely unless manually deleted

## Versioning and Backup System

The rubric system includes automatic versioning and backup functionality to prevent data loss and enable rollback to previous versions.

### Automatic Backups

- **When editing**: Every edit automatically creates a timestamped backup in `rubrics/versions/`
- **Backup naming**: `filename.v{major}.{minor}.{timestamp}.json` (e.g., `sales-demo.v1.0.20251021_143022.json`)
- **Version increment**: All edits increment the minor version (e.g., `1.0` → `1.1` → `1.2`)

### Version Management Commands

```bash
# View all versions of a rubric (current + backups)
python rubric_helper.py versions sales-demo

# Example output:
📋 Versions for rubric 'sales-demo':
============================================================
📄 Version 1.2
   File: sales-demo.json

💾 Version 1.1 (20251021_143022)
   File: sales-demo.v1.1.20251021_143022.json

💾 Version 1.0 (20251021_140000)
   File: sales-demo.v1.0.20251021_140000.json

# Restore to a specific version
python rubric_helper.py restore sales-demo 1.0
```

### Versioning Behavior

- **Minor increments only**: All edits are treated as minor version changes (no major version changes)
- **Automatic**: Version numbers increment automatically when editing - no manual version management needed
- **Safe rollback**: Restore any previous version without losing current work
- **Timestamped backups**: Each backup includes the exact date/time it was created

### Best Practices

- **Regular editing**: Edit rubrics frequently as needed - backups are automatic
- **Version checking**: Use `versions` command to see edit history before major changes
- **Safe experimentation**: Test changes knowing you can always restore to previous versions
- **Backup retention**: Old versions are kept indefinitely unless manually deleted

## Validation

The system automatically validates rubrics when they're loaded. Invalid rubrics will fall back to the default rubric with a warning message.

Common validation errors:

- Weights don't sum to 1.0
- Missing required fields
- Duplicate criterion IDs
- Invalid threshold values (revise >= pass)

## File Naming

Rubric files should:

- Use `.json` extension
- Use kebab-case for filenames (e.g., `sales-demo.json`)
- Be descriptive of the rubric's purpose
- Avoid spaces in filenames

The filename (without `.json`) is used with the `--rubric` parameter.
