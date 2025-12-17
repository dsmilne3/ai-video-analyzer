"""Integration: Rubric lifecycle – create/import, validate, list, evaluate.
"""
import os
import json
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

from src.video_evaluator import VideoEvaluator, AIProvider, validate_rubric, list_available_rubrics


def test_rubric_lifecycle(tmp_path):
    rubrics_dir = Path(__file__).parent.parent.parent / 'rubrics'

    # Create a valid flat rubric and write to rubrics dir
    rubric_data = {
        "criteria": [
            {"id": "clarity", "label": "Clarity", "desc": "Clear explanation", "weight": 0.5},
            {"id": "completeness", "label": "Completeness", "desc": "Coverage", "weight": 0.5}
        ],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0},
        "status": "current",
        "name": "Lifecycle Test Rubric",
        "description": "Integration lifecycle rubric"
    }
    is_valid, err = validate_rubric(rubric_data)
    assert is_valid, f"Rubric should be valid: {err}"

    temp_name = 'integration_lifecycle_rubric'
    temp_path = rubrics_dir / f"{temp_name}.json"
    with open(temp_path, 'w') as f:
        json.dump(rubric_data, f)

    try:
        # List should include our rubric
        available = list_available_rubrics()
        names = [r['filename'] for r in available]
        assert temp_name in names

        # Use rubric in evaluation
        evaluator = VideoEvaluator(rubric_path=temp_name, provider=AIProvider.OPENAI, enable_vision=False)
        result = evaluator.evaluate_transcript_with_rubric("Lifecycle demo transcript.", segments=[])
        assert 'overall' in result and 'scores' in result
    finally:
        if temp_path.exists():
            os.unlink(temp_path)
