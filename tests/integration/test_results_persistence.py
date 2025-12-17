"""Integration: Results persistence – timestamped filenames and reloadability.
"""
import os
import json
import time
import pytest
from pathlib import Path

pytestmark = pytest.mark.integration

from src.video_evaluator import VideoEvaluator, AIProvider, save_results


def test_results_persistence_unique_and_readable():
    evaluator = VideoEvaluator(rubric_path="sample-rubric", provider=AIProvider.OPENAI, enable_vision=False)
    result = evaluator.evaluate_transcript_with_rubric("Persistence demo.", segments=[])
    result['submitter'] = {"first_name": "Persist", "last_name": "Test", "partner_name": "AI"}

    path1 = save_results(result, 'persist_demo.mp4', 'json')
    time.sleep(1)
    path2 = save_results(result, 'persist_demo.mp4', 'json')

    try:
        assert path1 != path2
        for p in (path1, path2):
            assert os.path.exists(p)
            with open(p, 'r') as f:
                loaded = json.load(f)
            assert loaded.get('submitter', {}).get('first_name') == 'Persist'
    finally:
        for p in (path1, path2):
            if os.path.exists(p):
                os.unlink(p)
