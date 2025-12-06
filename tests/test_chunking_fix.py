#!/usr/bin/env python3
"""
Test script to verify chunking evaluation fixes.
Run with: python test_chunking_fix.py
Make sure to set API keys in .env file first.
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dotenv import load_dotenv
from src.video_evaluator import VideoEvaluator, AIProvider

# Load environment variables
load_dotenv()

def test_chunking_fix():
    """Test that chunking evaluation works without falling back to heuristic scoring."""

    # Check for API keys
    openai_key = os.getenv('OPENAI_API_KEY')
    anthropic_key = os.getenv('ANTHROPIC_API_KEY')

    # Choose provider - force OpenAI for testing
    provider = AIProvider.OPENAI
    api_key = openai_key

    if not api_key:
        print("❌ OPENAI_API_KEY not found in .env file")
        return False

    print(f"🔑 Using {provider.value} API")

    # Create evaluator with verbose logging to see what's happening
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",  # This has >10 criteria, triggers chunking
        api_key=api_key,
        provider=provider,
        verbose=True,  # Enable verbose to see chunking behavior
        enable_vision=False
    )

    # Use a longer transcript that would trigger chunking
    transcript = """
    Welcome to this comprehensive demo of our new dashboard feature. As you can see on the screen, we've redesigned the main interface to make it more intuitive and user-friendly. Let me walk you through the key improvements we've made.

    First, the navigation menu is now on the left side, which gives us more vertical space for the main content area. You can see here that we have quick access to reports, analytics, and settings. This new layout allows users to navigate more efficiently between different sections of the application.

    Next, I'll show you how to create a new report. Simply click the plus button in the top right corner, select your data source from the dropdown menu, and choose the visualization type that best fits your needs. The system automatically generates a preview of your report, as you can see here on the screen.

    One of the most powerful features is the advanced filtering system. You can filter by date ranges, user segments, geographic locations, and custom metrics. The filters are applied in real-time, so you can see the results update instantly as you make changes.

    Let me demonstrate the collaboration features. Team members can now leave comments directly on reports, tag colleagues for review, and share insights through integrated chat. This makes it much easier to work together on data analysis projects.

    Finally, let's talk about the new export capabilities. You can export your reports in multiple formats including PDF, Excel, and PowerPoint. The exports maintain all the formatting and interactivity of the original dashboard.

    This demo has shown you the key features of our redesigned dashboard. We're confident that these improvements will significantly enhance your productivity and data analysis capabilities.
    """ * 3  # Make it long enough to potentially trigger chunking

    print(f"📝 Transcript length: {len(transcript)} characters")
    print("🔄 Starting evaluation...")

    try:
        result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])

        # Check if we got real AI evaluation or fallback
        has_real_scores = False
        for criterion_id, score_data in result.get('scores', {}).items():
            if score_data.get('note') != 'Auto-generated conservative score':
                has_real_scores = True
                break

        if has_real_scores:
            print("✅ SUCCESS: Got real AI evaluation scores (not fallback)")
            print(f"📊 Overall score: {result.get('overall', {}).get('total_points', 'N/A')}/{result.get('overall', {}).get('max_points', 'N/A')}")
            return True
        else:
            print("❌ FAILED: Still getting fallback heuristic scores")
            print("💡 This means the chunking evaluation is still failing despite API success")
            return False

    except Exception as e:
        print(f"❌ ERROR: Evaluation failed with exception: {e}")
        return False

if __name__ == "__main__":
    success = test_chunking_fix()
    sys.exit(0 if success else 1)