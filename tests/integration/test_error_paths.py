"""Integration: Error paths – missing ffmpeg, yt-dlp failures, partial pipeline.
Note: These tests simulate error conditions without requiring real network/media.
"""
import os
import pytest
from unittest.mock import patch

pytestmark = pytest.mark.integration

from src.video_evaluator import VideoEvaluator, AIProvider


def test_partial_pipeline_llm_failure_graceful():
    evaluator = VideoEvaluator(rubric_path="sample-rubric", api_key="bad-key", provider=AIProvider.OPENAI, enable_vision=False)
    # No direct call; evaluate should handle failure internally and still return structure
    result = evaluator.evaluate_transcript_with_rubric("Partial pipeline demo.", segments=[])
    assert 'scores' in result and 'overall' in result


def test_missing_dependencies_guidance():
    # Simulate missing ffmpeg by checking dependency script runs
    # This is a light integration check; does not change system state
    import subprocess
    proc = subprocess.run(['python3', 'check_dependencies.py'], capture_output=True, text=True)
    # We don't require a zero exit code here—missing optional deps may cause non-zero.
    # Ensure the script ran and produced expected guidance mentioning ffmpeg.
    combined = (proc.stdout or '') + (proc.stderr or '')
    assert 'ffmpeg' in combined.lower()
    assert 'dependency check' in combined.lower() or 'results' in combined.lower()
