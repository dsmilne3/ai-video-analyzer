"""Integration: Provider handling – heuristic fallback vs real clients.
"""
import os
import pytest
from unittest.mock import MagicMock, patch

pytestmark = pytest.mark.integration

from src.video_evaluator import VideoEvaluator, AIProvider


def test_no_api_key_heuristic_fallback():
    evaluator = VideoEvaluator(rubric_path="sample-rubric", api_key=None, provider=AIProvider.OPENAI, enable_vision=False)
    result = evaluator.evaluate_transcript_with_rubric("Provider path demo.", segments=[])
    assert 'scores' in result and 'overall' in result


def test_openai_api_failure_graceful():
    evaluator = VideoEvaluator(rubric_path="sample-rubric", api_key="test-key", provider=AIProvider.OPENAI, enable_vision=False)
    if hasattr(evaluator, 'llm') and evaluator.llm:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        with patch.object(evaluator.llm, 'OpenAI', return_value=mock_client):
            result = evaluator.evaluate_transcript_with_rubric("Failure demo.", segments=[])
            assert 'scores' in result and 'overall' in result
    else:
        # If client not available, still produce result
        result = evaluator.evaluate_transcript_with_rubric("Failure demo.", segments=[])
        assert 'scores' in result and 'overall' in result
