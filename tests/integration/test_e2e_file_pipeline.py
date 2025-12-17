"""Integration test: local file → transcription → evaluation → feedback → save results.
Single-user, sequential flow.
"""
import os
import json
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

from src.video_evaluator import VideoEvaluator, AIProvider, save_results


def test_e2e_file_pipeline(tmp_path):
    # Prepare a small transcript to bypass real audio processing
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False,
        verbose=False
    )

    transcript = "Demo clearly shows login, dashboard, and reporting features."
    result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])

    assert 'overall' in result
    assert 'scores' in result

    # Simulate submitter info expected by save_results
    result['submitter'] = {
        'first_name': 'Integration',
        'last_name': 'Test',
        'partner_name': 'AI'
    }

    out_path = save_results(result, 'integration_demo.mp4', 'json')
    assert os.path.exists(out_path)

    with open(out_path, 'r') as f:
        saved = json.load(f)
    assert saved.get('submitter', {}).get('first_name') == 'Integration'

    # Cleanup
    os.unlink(out_path)
