"""Comprehensive unit tests for VideoEvaluator.

Tests cover:
- Happy paths for core functionality
- Input validation and error handling
- Rubric format variations (flat vs. hierarchical)
- Results persistence
- Provider switching
- Transcription components
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, mock_open
from src.video_evaluator import (
    VideoEvaluator, 
    AIProvider, 
    validate_rubric, 
    load_rubric,
    save_results,
    list_available_rubrics,
    DEFAULT_RUBRIC
)


# ============================================================================
# HAPPY PATH TESTS
# ============================================================================

def test_video_evaluator_initialization_defaults():
    """Test VideoEvaluator can be initialized with minimal parameters."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    assert evaluator.rubric is not None
    assert evaluator.provider == AIProvider.OPENAI
    assert evaluator.enable_vision is False
    assert evaluator.whisper_model is not None  # Should have fallback model


def test_video_evaluator_initialization_with_all_params():
    """Test VideoEvaluator initialization with all parameters specified."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        api_key="test-key-123",
        provider=AIProvider.ANTHROPIC,
        verbose=True,
        enable_vision=True,
        translate_to_english=True
    )
    assert evaluator.api_key == "test-key-123"
    assert evaluator.provider == AIProvider.ANTHROPIC
    assert evaluator.verbose is True
    assert evaluator.enable_vision is True
    assert evaluator.translate_to_english is True


def test_evaluate_transcript_basic():
    """Test basic transcript evaluation produces expected structure."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    transcript = "This is a comprehensive demo showing all key features clearly."
    result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])
    
    assert 'scores' in result
    assert 'overall' in result
    assert isinstance(result['scores'], dict)
    assert isinstance(result['overall'], dict)


def test_list_available_rubrics():
    """Test listing available rubrics returns expected format."""
    rubrics = list_available_rubrics()
    
    assert isinstance(rubrics, list)
    assert len(rubrics) > 0
    
    for rubric in rubrics:
        assert 'name' in rubric
        assert 'filename' in rubric
        assert 'description' in rubric


# ============================================================================
# INPUT VALIDATION TESTS (HIGH PRIORITY)
# ============================================================================

def test_validate_rubric_missing_required_keys():
    """Test validation fails when rubric is missing required keys."""
    invalid_rubric = {
        "criteria": [],
        "scale": {"min": 1, "max": 10}
        # Missing 'thresholds' and 'overall_method'
    }
    
    is_valid, error = validate_rubric(invalid_rubric)
    assert is_valid is False
    assert error is not None
    assert "required" in error.lower() or "keys" in error.lower()


def test_validate_rubric_empty_criteria():
    """Test validation fails with empty criteria list."""
    invalid_rubric = {
        "criteria": [],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0}
    }
    
    is_valid, error = validate_rubric(invalid_rubric)
    assert is_valid is False
    assert "criteria" in error.lower()


def test_validate_rubric_duplicate_criterion_ids():
    """Test validation fails with duplicate criterion IDs."""
    invalid_rubric = {
        "criteria": [
            {"id": "clarity", "label": "Clarity", "desc": "Clear", "weight": 0.5},
            {"id": "clarity", "label": "Clarity 2", "desc": "Clear", "weight": 0.5}
        ],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0}
    }
    
    is_valid, error = validate_rubric(invalid_rubric)
    assert is_valid is False
    assert "duplicate" in error.lower()


def test_validate_rubric_invalid_weights():
    """Test validation fails when weights don't sum to 1.0."""
    invalid_rubric = {
        "criteria": [
            {"id": "clarity", "label": "Clarity", "desc": "Clear", "weight": 0.3},
            {"id": "completeness", "label": "Complete", "desc": "Complete", "weight": 0.3}
            # Weights sum to 0.6, not 1.0
        ],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0}
    }
    
    is_valid, error = validate_rubric(invalid_rubric)
    assert is_valid is False
    assert "sum" in error.lower() or "1.0" in error


def test_validate_rubric_invalid_scale():
    """Test validation fails with invalid scale (min >= max)."""
    invalid_rubric = {
        "criteria": [
            {"id": "clarity", "label": "Clarity", "desc": "Clear", "weight": 1.0}
        ],
        "scale": {"min": 10, "max": 1},  # Invalid: min > max
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0}
    }
    
    is_valid, error = validate_rubric(invalid_rubric)
    assert is_valid is False
    assert "scale" in error.lower() and "max" in error.lower()


def test_validate_rubric_invalid_thresholds():
    """Test validation fails when revise threshold >= pass threshold."""
    invalid_rubric = {
        "criteria": [
            {"id": "clarity", "label": "Clarity", "desc": "Clear", "weight": 1.0}
        ],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 5.0, "revise": 7.0}  # Invalid: revise > pass
    }
    
    is_valid, error = validate_rubric(invalid_rubric)
    assert is_valid is False
    assert "threshold" in error.lower()


def test_validate_rubric_valid_old_format():
    """Test validation passes for valid old (flat) format rubric."""
    valid_rubric = {
        "criteria": [
            {"id": "clarity", "label": "Clarity", "desc": "Clear", "weight": 0.5},
            {"id": "completeness", "label": "Complete", "desc": "Complete", "weight": 0.5}
        ],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0}
    }
    
    is_valid, error = validate_rubric(valid_rubric)
    assert is_valid is True
    assert error is None


def test_validate_rubric_valid_new_format():
    """Test validation passes for valid new (hierarchical) format rubric."""
    valid_rubric = {
        "rubric_id": "test-rubric",
        "name": "Test Rubric",
        "version": "1.0",
        "categories": [
            {
                "category_id": "content",
                "label": "Content Quality",
                "weight": 1.0,
                "max_points": 10,
                "criteria": [
                    {"criterion_id": "clarity", "label": "Clarity", "max_points": 5},
                    {"criterion_id": "depth", "label": "Depth", "max_points": 5}
                ]
            }
        ],
        "scale": {"min": 0, "max": 10},
        "thresholds": {"pass": 7, "revise": 5}
    }
    
    is_valid, error = validate_rubric(valid_rubric)
    assert is_valid is True
    assert error is None


def test_evaluate_empty_transcript():
    """Test evaluation handles empty transcript gracefully."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    result = evaluator.evaluate_transcript_with_rubric("", segments=[])
    
    # Should still produce a valid result structure, even if scores are low/heuristic
    assert 'scores' in result
    assert 'overall' in result


def test_evaluate_very_short_transcript():
    """Test evaluation handles very short transcript."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    result = evaluator.evaluate_transcript_with_rubric("Hello.", segments=[])
    
    assert 'scores' in result
    assert 'overall' in result


# ============================================================================
# ERROR HANDLING TESTS (HIGH PRIORITY)
# ============================================================================

def test_load_rubric_nonexistent_file():
    """Test load_rubric falls back to default when file doesn't exist."""
    rubric = load_rubric("nonexistent-rubric-xyz123")
    
    # Should fall back to default rubric
    assert rubric is not None
    assert "criteria" in rubric
    assert rubric == DEFAULT_RUBRIC


def test_load_rubric_invalid_json():
    """Test load_rubric handles malformed JSON gracefully."""
    # Create a temporary invalid rubric file in the rubrics directory
    rubrics_dir = Path(__file__).parent.parent / "rubrics"
    invalid_rubric_path = rubrics_dir / "test_invalid_temp.json"
    
    try:
        with open(invalid_rubric_path, 'w') as f:
            f.write("{invalid json content")
        
        # Try to load it - should fall back to default
        rubric = load_rubric("test_invalid_temp")
        
        # Should fall back to DEFAULT_RUBRIC
        assert rubric is not None
        assert rubric == DEFAULT_RUBRIC
    finally:
        if invalid_rubric_path.exists():
            invalid_rubric_path.unlink()


def test_evaluator_missing_api_key_uses_heuristic():
    """Test evaluator can initialize and produce results without API key."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        api_key=None,  # No API key
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    transcript = "This is a demo showing features."
    result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])
    
    # Should still produce results (may use heuristic or have API key from env)
    assert 'scores' in result
    assert 'overall' in result
    
    # Verify result structure is valid
    assert isinstance(result['scores'], dict)
    assert isinstance(result['overall'], dict)
    assert len(result['scores']) > 0


def test_evaluator_api_failure_fallback():
    """Test evaluator handles API failures gracefully."""
    # Mock the LLM client to simulate API failure
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        api_key="invalid-key-that-will-fail",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    # Mock the llm client to raise an exception
    if hasattr(evaluator, 'llm') and evaluator.llm:
        mock_client = MagicMock()
        mock_client.chat.completions.create.side_effect = Exception("API Error")
        
        # Patch the client creation
        with patch.object(evaluator.llm, 'OpenAI', return_value=mock_client):
            transcript = "This demo shows features clearly."
            result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])
            
            # Should fall back to heuristic or handle gracefully
            assert 'scores' in result
            assert 'overall' in result
    else:
        # If no LLM client, just verify it can still produce results
        transcript = "This demo shows features clearly."
        result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])
        assert 'scores' in result
        assert 'overall' in result


# ============================================================================
# RUBRIC FORMAT TESTS (HIGH PRIORITY)
# ============================================================================

def test_evaluate_with_flat_rubric():
    """Test evaluation works with flat (old format) rubric."""
    flat_rubric_json = {
        "criteria": [
            {"id": "clarity", "label": "Clarity", "desc": "Clear explanation", "weight": 0.6},
            {"id": "completeness", "label": "Completeness", "desc": "Complete coverage", "weight": 0.4}
        ],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0}
    }
    
    # Create temporary rubric file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False, dir='rubrics') as f:
        json.dump(flat_rubric_json, f)
        temp_rubric_name = Path(f.name).stem
    
    try:
        evaluator = VideoEvaluator(
            rubric_path=temp_rubric_name,
            provider=AIProvider.OPENAI,
            enable_vision=False
        )
        
        result = evaluator.evaluate_transcript_with_rubric(
            "Demo shows clear and complete features.",
            segments=[]
        )
        
        assert 'scores' in result
        assert 'overall' in result
        # Old format uses weighted_mean method
        assert result['overall'].get('method') in ['weighted_mean', 'heuristic']
    finally:
        os.unlink(f'rubrics/{temp_rubric_name}.json')


def test_evaluate_with_hierarchical_rubric():
    """Test evaluation works with hierarchical (new format) rubric."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",  # This is hierarchical format
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    result = evaluator.evaluate_transcript_with_rubric(
        "Demo shows all features in depth.",
        segments=[]
    )
    
    assert 'scores' in result
    assert 'overall' in result


def test_rubric_with_single_criterion():
    """Test rubric validation and evaluation with single criterion."""
    single_criterion_rubric = {
        "criteria": [
            {"id": "quality", "label": "Overall Quality", "desc": "Quality", "weight": 1.0}
        ],
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.0, "revise": 4.0}
    }
    
    is_valid, error = validate_rubric(single_criterion_rubric)
    assert is_valid is True
    assert error is None


def test_rubric_with_many_criteria():
    """Test rubric with many criteria (triggers chunking in evaluation)."""
    # Create rubric with 15 criteria to trigger chunking
    criteria = []
    weight = 1.0 / 15
    for i in range(15):
        criteria.append({
            "id": f"criterion_{i}",
            "label": f"Criterion {i}",
            "desc": f"Description {i}",
            "weight": weight
        })
    
    many_criteria_rubric = {
        "criteria": criteria,
        "scale": {"min": 1, "max": 10},
        "overall_method": "weighted_mean",
        "thresholds": {"pass": 6.5, "revise": 5.0}
    }
    
    is_valid, error = validate_rubric(many_criteria_rubric)
    assert is_valid is True
    assert error is None


# ============================================================================
# RESULTS PERSISTENCE TESTS (MEDIUM PRIORITY)
# ============================================================================

def test_save_results_json_format():
    """Test save_results creates JSON file with correct structure."""
    result_data = {
        'submitter': {
            'first_name': 'John',
            'last_name': 'Doe',
            'partner_name': 'TestPartner'
        },
        'evaluation': {
            'scores': {'clarity': {'score': 8, 'note': 'Good'}},
            'overall': {'weighted_score': 8.0, 'pass_status': 'pass'}
        },
        'transcript': 'Test transcript'
    }
    
    output_path = save_results(result_data, 'test_video.mp4', 'json')
    
    try:
        assert os.path.exists(output_path)
        assert output_path.endswith('.json')
        
        # Verify file contents
        with open(output_path, 'r') as f:
            saved_data = json.load(f)
        
        assert saved_data['submitter']['first_name'] == 'John'
        assert saved_data['evaluation']['overall']['pass_status'] == 'pass'
    finally:
        if os.path.exists(output_path):
            os.unlink(output_path)


def test_save_results_no_overwrite():
    """Test save_results uses timestamps to avoid overwriting."""
    result_data = {
        'submitter': {
            'first_name': 'Jane',
            'last_name': 'Smith',
            'partner_name': 'Partner1'
        },
        'evaluation': {
            'scores': {},
            'overall': {'weighted_score': 7.0}
        }
    }
    
    # Save twice
    path1 = save_results(result_data, 'demo.mp4', 'json')
    
    # Small delay to ensure different timestamp
    import time
    time.sleep(1)
    
    path2 = save_results(result_data, 'demo.mp4', 'json')
    
    try:
        assert path1 != path2, "Timestamps should make filenames unique"
        assert os.path.exists(path1)
        assert os.path.exists(path2)
    finally:
        for path in [path1, path2]:
            if os.path.exists(path):
                os.unlink(path)


def test_save_results_creates_directory():
    """Test save_results creates results directory if it doesn't exist."""
    import shutil
    
    results_dir = Path(__file__).parent.parent / "results"
    
    # Temporarily rename results dir if it exists
    backup_exists = results_dir.exists()
    if backup_exists:
        backup_dir = results_dir.parent / "results_backup_temp"
        if backup_dir.exists():
            shutil.rmtree(backup_dir)
        shutil.move(str(results_dir), str(backup_dir))
    
    try:
        result_data = {
            'submitter': {
                'first_name': 'Test',
                'last_name': 'User',
                'partner_name': 'TestCo'
            },
            'evaluation': {'scores': {}, 'overall': {}}
        }
        
        output_path = save_results(result_data, 'test.mp4', 'json')
        
        assert results_dir.exists(), "Results directory should be created"
        assert os.path.exists(output_path)
        
        os.unlink(output_path)
    finally:
        # Restore original results directory
        if backup_exists:
            if results_dir.exists():
                shutil.rmtree(results_dir)
            shutil.move(str(backup_dir), str(results_dir))


# ============================================================================
# PROVIDER SWITCHING TESTS (MEDIUM PRIORITY)
# ============================================================================

def test_initialize_with_openai_provider():
    """Test VideoEvaluator initializes correctly with OpenAI provider."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    assert evaluator.provider == AIProvider.OPENAI


def test_initialize_with_anthropic_provider():
    """Test VideoEvaluator initializes correctly with Anthropic provider."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.ANTHROPIC,
        enable_vision=False
    )
    
    assert evaluator.provider == AIProvider.ANTHROPIC


def test_both_providers_produce_valid_results():
    """Test both OpenAI and Anthropic providers produce valid result structures."""
    transcript = "This demo clearly shows all main features with good pacing."
    
    for provider in [AIProvider.OPENAI, AIProvider.ANTHROPIC]:
        evaluator = VideoEvaluator(
            rubric_path="sample-rubric",
            provider=provider,
            enable_vision=False
        )
        
        result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])
        
        assert 'scores' in result, f"{provider.value} should produce scores"
        assert 'overall' in result, f"{provider.value} should produce overall"
        assert isinstance(result['scores'], dict)


# ============================================================================
# TRANSCRIPTION COMPONENT TESTS (MEDIUM PRIORITY)
# ============================================================================

def test_whisper_model_loaded():
    """Test Whisper model is loaded (or fallback is available)."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    assert evaluator.whisper_model is not None
    assert evaluator.whisper_model_name is not None


def test_translation_enabled_flag():
    """Test translate_to_english flag is set correctly."""
    evaluator_with_translation = VideoEvaluator(
        rubric_path="sample-rubric",
        translate_to_english=True,
        enable_vision=False
    )
    
    evaluator_without_translation = VideoEvaluator(
        rubric_path="sample-rubric",
        translate_to_english=False,
        enable_vision=False
    )
    
    assert evaluator_with_translation.translate_to_english is True
    assert evaluator_without_translation.translate_to_english is False


def test_vision_enabled_flag():
    """Test enable_vision flag is set correctly."""
    evaluator_with_vision = VideoEvaluator(
        rubric_path="sample-rubric",
        enable_vision=True
    )
    
    evaluator_without_vision = VideoEvaluator(
        rubric_path="sample-rubric",
        enable_vision=False
    )
    
    assert evaluator_with_vision.enable_vision is True
    assert evaluator_without_vision.enable_vision is False


def test_supported_formats_defined():
    """Test supported audio and video formats are defined."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        enable_vision=False
    )
    
    assert hasattr(evaluator, 'SUPPORTED_VIDEO_FORMATS')
    assert hasattr(evaluator, 'SUPPORTED_AUDIO_FORMATS')
    assert '.mp4' in evaluator.SUPPORTED_VIDEO_FORMATS
    assert '.mp3' in evaluator.SUPPORTED_AUDIO_FORMATS


def test_temp_directory_created():
    """Test temporary directory is created for processing."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        enable_vision=False
    )
    
    assert hasattr(evaluator, 'temp_dir')
    assert evaluator.temp_dir is not None
    assert os.path.exists(evaluator.temp_dir)


# ============================================================================
# EDGE CASES
# ============================================================================

def test_transcript_with_special_characters():
    """Test evaluation handles transcripts with Unicode and special characters."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        enable_vision=False
    )
    
    transcript = """
    This demo shows features with special chars: 
    émojis 😀🎉, ñoñ-ÄßÇII çhàrãçtêrß, and symbols: ©®™€£¥
    """
    
    result = evaluator.evaluate_transcript_with_rubric(transcript, segments=[])
    
    assert 'scores' in result
    assert 'overall' in result


def test_verbose_mode():
    """Test verbose mode enables additional logging."""
    evaluator_verbose = VideoEvaluator(
        rubric_path="sample-rubric",
        verbose=True,
        enable_vision=False
    )
    
    evaluator_quiet = VideoEvaluator(
        rubric_path="sample-rubric",
        verbose=False,
        enable_vision=False
    )
    
    assert evaluator_verbose.verbose is True
    assert evaluator_quiet.verbose is False


def test_progress_callback():
    """Test progress_callback can be set."""
    callback_called = []
    
    def test_callback(message):
        callback_called.append(message)
    
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        progress_callback=test_callback,
        enable_vision=False
    )
    
    assert evaluator.progress_callback is not None
    
    # Test callback works
    if evaluator.progress_callback:
        evaluator.progress_callback("Test message")
        assert len(callback_called) > 0
        assert "Test message" in callback_called


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
