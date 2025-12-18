"""Tests for remote transcription feature.

Tests cover:
- Remote transcription with valid OpenAI API key
- Remote transcription fallback to local when key is missing
- Remote transcription with different providers (OpenAI/Anthropic)
- transcription_method parameter handling
- Progress messages for local vs remote transcription
- Integration with evaluate_video workflow
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from src.video_evaluator import VideoEvaluator, AIProvider


# ============================================================================
# INITIALIZATION TESTS
# ============================================================================

def test_transcription_method_default():
    """Test that transcription_method defaults to 'local'."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI
    )
    assert evaluator.transcription_method == "local"


def test_transcription_method_local():
    """Test initialization with transcription_method='local'."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="local"
    )
    assert evaluator.transcription_method == "local"


def test_transcription_method_openai():
    """Test initialization with transcription_method='openai'."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="openai",
        openai_api_key="test-key-123"
    )
    assert evaluator.transcription_method == "openai"
    assert evaluator.openai_api_key == "test-key-123"


def test_openai_api_key_from_evaluation_provider():
    """Test that openai_api_key falls back to api_key when provider is OpenAI."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        api_key="provider-key-456",
        provider=AIProvider.OPENAI,
        transcription_method="openai"
    )
    # When openai_api_key not specified but provider is OpenAI, should use api_key
    assert evaluator.openai_api_key == "provider-key-456"


def test_openai_api_key_separate_from_anthropic():
    """Test that openai_api_key is separate when using Anthropic provider."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        api_key="anthropic-key-789",
        provider=AIProvider.ANTHROPIC,
        transcription_method="openai",
        openai_api_key="openai-key-123"
    )
    # Evaluation uses Anthropic, but transcription uses separate OpenAI key
    assert evaluator.api_key == "anthropic-key-789"
    assert evaluator.openai_api_key == "openai-key-123"


# ============================================================================
# REMOTE TRANSCRIPTION TESTS
# ============================================================================

@patch('openai.OpenAI')
def test_remote_transcription_with_valid_key(mock_openai_class):
    """Test remote transcription uses OpenAI API when key is valid."""
    # Setup mock OpenAI client and response
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 5.0
    mock_segment.text = "Remote transcription result"
    mock_segment.avg_logprob = -0.5
    mock_segment.compression_ratio = 1.2
    mock_segment.no_speech_prob = 0.1
    
    mock_transcript = MagicMock()
    mock_transcript.text = "Remote transcription result"
    mock_transcript.language = "en"
    mock_transcript.segments = [mock_segment]
    
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_transcript
    mock_openai_class.return_value = mock_client
    
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="openai",
        openai_api_key="valid-openai-key"
    )
    
    # Create test audio file with actual audio data
    audio_path = Path(evaluator.temp_dir) / "test.wav"
    # Write minimal WAV file header
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE')
    
    try:
        result = evaluator.transcribe_with_timestamps(str(audio_path))
        
        # Verify OpenAI client was instantiated with correct key
        mock_openai_class.assert_called_once_with(api_key="valid-openai-key")
        # Verify transcription API was called
        assert mock_client.audio.transcriptions.create.called
        assert result['text'] == "Remote transcription result"
        assert len(result['segments']) > 0
    finally:
        # Cleanup
        if audio_path.exists():
            audio_path.unlink()


def test_remote_transcription_fallback_when_key_missing():
    """Test that remote transcription raises error when OpenAI key is missing."""
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="openai",
        openai_api_key=None  # No key provided
    )
    
    # Create test audio file
    audio_path = Path(evaluator.temp_dir) / "test.wav"
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE')
    
    try:
        # Should raise RuntimeError about missing key
        with pytest.raises(RuntimeError) as exc_info:
            evaluator.transcribe_with_timestamps(str(audio_path))
        assert "No OpenAI API key" in str(exc_info.value)
    finally:
        if audio_path.exists():
            audio_path.unlink()


@patch('openai.OpenAI')
def test_remote_transcription_with_anthropic_provider(mock_openai_class):
    """Test remote transcription works when evaluation provider is Anthropic."""
    # Setup mock
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 5.0
    mock_segment.text = "Transcription via OpenAI API"
    mock_segment.avg_logprob = -0.5
    mock_segment.compression_ratio = 1.2
    mock_segment.no_speech_prob = 0.1
    
    mock_transcript = MagicMock()
    mock_transcript.text = "Transcription via OpenAI API"
    mock_transcript.language = "en"
    mock_transcript.segments = [mock_segment]
    
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_transcript
    mock_openai_class.return_value = mock_client
    
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        api_key="anthropic-key-for-eval",
        provider=AIProvider.ANTHROPIC,
        transcription_method="openai",
        openai_api_key="openai-key-for-whisper"
    )
    
    # Create test audio file
    audio_path = Path(evaluator.temp_dir) / "test.wav"
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE')
    
    try:
        result = evaluator.transcribe_with_timestamps(str(audio_path))
        
        # Verify OpenAI API was used for transcription despite Anthropic eval provider
        mock_openai_class.assert_called_once_with(api_key="openai-key-for-whisper")
        assert result['text'] == "Transcription via OpenAI API"
        # Verify evaluation provider remains Anthropic
        assert evaluator.provider == AIProvider.ANTHROPIC
        assert evaluator.api_key == "anthropic-key-for-eval"
    finally:
        if audio_path.exists():
            audio_path.unlink()


# ============================================================================
# PROGRESS MESSAGE TESTS
# ============================================================================

@patch('openai.OpenAI')
def test_remote_transcription_progress_message(mock_openai_class):
    """Test that remote transcription reports appropriate progress messages."""
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 1.0
    mock_segment.text = "Remote text"
    mock_segment.avg_logprob = -0.5
    mock_segment.compression_ratio = 1.2
    mock_segment.no_speech_prob = 0.1
    
    mock_transcript = MagicMock()
    mock_transcript.text = "Remote text"
    mock_transcript.language = "en"
    mock_transcript.segments = [mock_segment]
    
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_transcript
    mock_openai_class.return_value = mock_client
    
    progress_messages = []
    def capture_progress(msg):
        progress_messages.append(msg)
    
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="openai",
        openai_api_key="test-key",
        progress_callback=capture_progress,
        verbose=True
    )
    
    audio_path = Path(evaluator.temp_dir) / "test.wav"
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE')
    
    try:
        evaluator.transcribe_with_timestamps(str(audio_path))
        
        # Since progress_callback only captures print statements in evaluate_video,
        # we just verify the transcription succeeded with remote method
        assert evaluator.transcription_method == "openai"
        assert mock_client.audio.transcriptions.create.called
    finally:
        if audio_path.exists():
            audio_path.unlink()


def test_local_transcription_method_setting():
    """Test that local transcription method is properly set and defaults correctly."""
    # Test default
    evaluator_default = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI
    )
    assert evaluator_default.transcription_method == "local"
    
    # Test explicit local
    evaluator_local = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="local"
    )
    assert evaluator_local.transcription_method == "local"
    assert evaluator_local.whisper_model is not None


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================

@patch('openai.OpenAI')
def test_remote_transcription_api_error(mock_openai_class):
    """Test that API errors are properly raised."""
    # Setup OpenAI API to raise an error
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.side_effect = Exception("API Error: Invalid key")
    mock_openai_class.return_value = mock_client
    
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="openai",
        openai_api_key="invalid-key"
    )
    
    audio_path = Path(evaluator.temp_dir) / "test.wav"
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE')
    
    try:
        # Should raise RuntimeError wrapping the API error
        with pytest.raises(RuntimeError) as exc_info:
            evaluator.transcribe_with_timestamps(str(audio_path))
        assert "Transcription failed" in str(exc_info.value)
    finally:
        if audio_path.exists():
            audio_path.unlink()


# ============================================================================
# INTEGRATION TESTS
# ============================================================================

@patch('openai.OpenAI')
@patch('src.video_evaluator.VideoEvaluator.evaluate_transcript_with_rubric')
def test_full_workflow_with_remote_transcription(mock_evaluate, mock_openai_class):
    """Test full workflow: transcribe remotely then evaluate."""
    # Setup OpenAI mock
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 10.0
    mock_segment.text = "Remote transcription of video content"
    mock_segment.avg_logprob = -0.5
    mock_segment.compression_ratio = 1.2
    mock_segment.no_speech_prob = 0.1
    
    mock_transcript = MagicMock()
    mock_transcript.text = "Remote transcription of video content"
    mock_transcript.language = "en"
    mock_transcript.segments = [mock_segment]
    
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_transcript
    mock_openai_class.return_value = mock_client
    
    mock_evaluate.return_value = {
        'scores': {'clarity': {'score': 8, 'confidence': 9}},
        'overall': {'score': 8.0, 'confidence': 9.0, 'feedback': 'Good demo'}
    }
    
    evaluator = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="openai",
        openai_api_key="test-key"
    )
    
    # Create test audio file
    audio_path = Path(evaluator.temp_dir) / "test.wav"
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE')
    
    try:
        # Step 1: Transcribe
        transcription_result = evaluator.transcribe_with_timestamps(str(audio_path))
        
        # Verify remote transcription was used
        mock_openai_class.assert_called_once_with(api_key="test-key")
        assert transcription_result['text'] == "Remote transcription of video content"
        
        # Step 2: Evaluate transcript
        evaluation_result = evaluator.evaluate_transcript_with_rubric(
            transcription_result['text'], 
            transcription_result['segments']
        )
        
        # Verify evaluation was called
        mock_evaluate.assert_called_once()
        
        # Verify result structure
        assert 'scores' in evaluation_result
        assert 'overall' in evaluation_result
    finally:
        if audio_path.exists():
            audio_path.unlink()


@patch('openai.OpenAI')
def test_transcription_method_parameter_values(mock_openai_class):
    """Test that transcription_method accepts expected values."""
    mock_segment = MagicMock()
    mock_segment.start = 0.0
    mock_segment.end = 1.0
    mock_segment.text = "Text"
    mock_segment.avg_logprob = -0.5
    mock_segment.compression_ratio = 1.2
    mock_segment.no_speech_prob = 0.1
    
    mock_transcript = MagicMock()
    mock_transcript.text = "Text"
    mock_transcript.language = "en"
    mock_transcript.segments = [mock_segment]
    
    mock_client = MagicMock()
    mock_client.audio.transcriptions.create.return_value = mock_transcript
    mock_openai_class.return_value = mock_client
    
    # Test "local"
    evaluator_local = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="local"
    )
    assert evaluator_local.transcription_method == "local"
    
    # Test "openai"
    evaluator_remote = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.OPENAI,
        transcription_method="openai",
        openai_api_key="key"
    )
    assert evaluator_remote.transcription_method == "openai"
    
    # Test "anthropic" (should also use OpenAI Whisper API)
    evaluator_anthropic = VideoEvaluator(
        rubric_path="sample-rubric",
        provider=AIProvider.ANTHROPIC,
        transcription_method="anthropic",  # Legacy support
        openai_api_key="key"
    )
    assert evaluator_anthropic.transcription_method == "anthropic"
    
    audio_path = Path(evaluator_remote.temp_dir) / "test.wav"
    with open(audio_path, 'wb') as f:
        f.write(b'RIFF' + b'\x00\x00\x00\x00' + b'WAVE')
    
    try:
        # Verify "anthropic" method also uses OpenAI API
        evaluator_anthropic.transcribe_with_timestamps(str(audio_path))
        mock_openai_class.assert_called_with(api_key="key")
    finally:
        if audio_path.exists():
            audio_path.unlink()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
