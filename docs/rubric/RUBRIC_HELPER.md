# Rubric Helper Script

A utility script to create, validate, and manage evaluation rubrics for the video analyzer.

## Features

- **Create new rubrics** interactively with guided prompts
- **Validate existing rubrics** for correctness and completeness
- **List all available rubrics** with descriptions
- **Show detailed rubric information** including criteria and weights
- **Edit existing rubrics** with options to modify criteria, thresholds, etc.

## Usage

### Create a New Rubric

```bash
python rubric_helper.py create
```

Follow the interactive prompts to define:

- Rubric name and description
- Scoring scale (min/max values)
- Pass/fail thresholds
- Evaluation criteria with weights

### Validate a Rubric

```bash
python rubric_helper.py validate <filename>
```

Checks that the rubric follows the required structure and constraints.

### List Available Rubrics

```bash
python rubric_helper.py list
```

Shows all rubrics in the `rubrics/` directory.

### Show Rubric Details

```bash
python rubric_helper.py show <rubric_name>
```

Displays complete information about a specific rubric.

### Edit an Existing Rubric

```bash
python rubric_helper.py edit <rubric_name>
```

Interactive editor to modify rubric properties, add/remove criteria, etc.

## Rubric Structure

Rubrics are JSON files with this structure:

```json
{
  "name": "Rubric Name",
  "description": "Brief description",
  "criteria": [
    {
      "id": "criterion_id",
      "label": "Display Name",
      "desc": "Detailed description",
      "weight": 0.25
    }
  ],
  "scale": {
    "min": 1,
    "max": 10
  },
  "overall_method": "weighted_mean",
  "thresholds": {
    "pass": 7.0,
    "revise": 5.0
  }
}
```

## Validation Rules

- All required fields must be present
- Criterion weights must sum to 1.0
- Scale min must be less than max
- Revise threshold must be less than pass threshold
- Criterion IDs must be unique

## Examples

Create a rubric for product demos:

```bash
python rubric_helper.py create
# Name: Product Demo Rubric
# Description: For evaluating product demonstration videos
# ...follow prompts...
```

Validate the default rubric:

```bash
python rubric_helper.py validate default
```

Edit the sales demo rubric:

```bash
python rubric_helper.py edit sales-demo
```
