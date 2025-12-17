"""Provider Live Opt-In: runs only when a valid API key and client are available.
Checks structure of results using live LLM provider.
"""
import os
import pytest

pytestmark = [pytest.mark.integration, pytest.mark.provider_live]

from src.video_evaluator import VideoEvaluator, AIProvider


def test_provider_live_happy_path():
    # Determine provider based on available env and installed client
    provider = None
    api_key = None

    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    if openai_key:
        try:
            import openai  # noqa: F401
            provider = AIProvider.OPENAI
            api_key = openai_key
        except Exception:
            pass
    if provider is None and anthropic_key:
        try:
            import anthropic  # noqa: F401
            provider = AIProvider.ANTHROPIC
            api_key = anthropic_key
        except Exception:
            pass

    if provider is None or api_key is None:
        pytest.skip("No usable provider/client available for live test")

    evaluator = VideoEvaluator(rubric_path="sample-rubric", api_key=api_key, provider=provider, enable_vision=False)
    result = evaluator.evaluate_transcript_with_rubric("Live provider test transcript.", segments=[])

    assert 'scores' in result
    assert 'overall' in result
