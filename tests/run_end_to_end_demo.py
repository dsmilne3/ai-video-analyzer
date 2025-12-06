#!/usr/bin/env python3
"""
End-to-end demo of the video evaluator without requiring ffmpeg/whisper.
This shows the rubric evaluation, highlights, and summary generation.
"""
import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.video_evaluator import VideoEvaluator, AIProvider
import json

def test_evaluator_without_real_audio():
    """Test the evaluator using mock transcript (no audio transcription needed)."""
    print("="*60)
    print("DEMO: Video Evaluator End-to-End Test")
    print("="*60)
    print()
    
    # Initialize evaluator (API key loaded from .env)
    evaluator = VideoEvaluator(
        rubric_path="default",
        provider=AIProvider.ANTHROPIC, 
        enable_vision=False
    )
    
    # Sample transcript (simulating what would come from Whisper)
    sample_transcript = """
    Welcome to this demo of our new dashboard feature. 
    As you can see on the screen, we've redesigned the main interface 
    to make it more intuitive. Let me walk you through the key improvements.
    
    First, the navigation menu is now on the left side, which gives us more 
    vertical space for the main content area. You can see here that we have 
    quick access to reports, analytics, and settings.
    
    Next, I'll show you how to create a new report. Simply click the plus 
    button, select your data source, and choose the visualization type. 
    The system automatically generates a preview, as you can see here.
    
    Finally, let's talk about the new collaboration features. Team members 
    can now leave comments directly on reports, and you'll get real-time 
    notifications when someone mentions you.
    
    This new dashboard reduces the time to create reports by approximately 
    40 percent compared to the old interface, based on our internal testing.
    Thank you for watching this demo.
    """
    
    # Mock segments (simulating Whisper output with timestamps)
    mock_segments = [
        {'start': 0.0, 'end': 5.2, 'text': 'Welcome to this demo of our new dashboard feature.', 'words': []},
        {'start': 5.2, 'end': 10.5, 'text': "As you can see on the screen, we've redesigned the main interface", 'words': []},
        {'start': 10.5, 'end': 13.8, 'text': 'to make it more intuitive. Let me walk you through the key improvements.', 'words': []},
    ]
    
    print("Sample transcript:")
    print(sample_transcript[:200] + "...")
    print()
    
    # Test summarization
    print("Generating summary...")
    summary = evaluator.summarize_transcript(sample_transcript)
    print(f"Summary: {summary}")
    print()
    
    # Test highlights
    print("Picking highlights...")
    highlights = evaluator.pick_highlights(mock_segments, top_k=2)
    print(f"Highlights ({len(highlights)} segments):")
    for h in highlights:
        print(f"  [{h['start']:.1f}s - {h['end']:.1f}s]: {h['text'][:60]}...")
    print()
    
    # Test evaluation with rubric
    print("Evaluating with rubric (fallback mode, no LLM)...")
    evaluation = evaluator.evaluate_transcript_with_rubric(
        sample_transcript, 
        segments=mock_segments
    )
    
    print("Evaluation Results:")
    print(json.dumps(evaluation, indent=2))
    print()
    
    # Test qualitative feedback generation
    print("Generating qualitative feedback (fallback mode, no LLM)...")
    feedback = evaluator.generate_qualitative_feedback(
        sample_transcript,
        evaluation,
        visual_analysis=None
    )
    
    print("Feedback Results:")
    print(f"Tone: {feedback.get('tone', 'unknown').upper()}")
    print()
    print("Strengths:")
    for i, strength in enumerate(feedback.get('strengths', []), 1):
        print(f"  {i}. {strength.get('title')}")
        print(f"     {strength.get('description')}")
        print()
    print("Areas for Improvement:")
    for i, improvement in enumerate(feedback.get('improvements', []), 1):
        print(f"  {i}. {improvement.get('title')}")
        print(f"     {improvement.get('description')}")
        print()
    
    print("="*60)
    print("✓ End-to-end test completed successfully!")
    print("="*60)
    print()
    print("Next steps to enable full functionality:")
    print("1. Install ffmpeg: brew install ffmpeg")
    print("2. Set API keys in environment:")
    print("   export API_KEY=your-openai-or-anthropic-key")
    print("3. Run with real video files:")
    print("   python cli/evaluate_video.py path/to/video.mp4 --provider anthropic")
    print()

if __name__ == '__main__':
    test_evaluator_without_real_audio()
