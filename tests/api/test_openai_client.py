import pytest
from unittest.mock import MagicMock, patch
from src.api.openai_client import OpenAIService

@pytest.fixture
def mock_openai():
    """Mock OpenAI client for testing."""
    with patch('src.api.openai_client.OpenAI') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def openai_service(mock_openai, mock_env):
    """Create OpenAIService instance with mocked client."""
    return OpenAIService()

def test_transcribe_audio_success(openai_service, mock_openai, sample_video_file):
    """Test successful audio transcription."""
    expected_transcript = "This is a test transcript"
    mock_openai.audio.transcriptions.create.return_value = expected_transcript
    
    result = openai_service.transcribe_audio(sample_video_file)
    
    assert result == expected_transcript
    mock_openai.audio.transcriptions.create.assert_called_once()

def test_transcribe_audio_failure(openai_service, mock_openai, sample_video_file):
    """Test audio transcription failure."""
    mock_openai.audio.transcriptions.create.side_effect = Exception("API Error")
    
    result = openai_service.transcribe_audio(sample_video_file)
    
    assert "Transcription failed" in result
    mock_openai.audio.transcriptions.create.assert_called_once()

def test_format_json_response_success(openai_service, mock_openai):
    """Test successful JSON response formatting."""
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='{"title": "Test Video", "channel": "Test Channel", "channelLink": "https://youtube.com/channel", "url": "https://youtube.com/watch"}'
            )
        )
    ]
    mock_openai.chat.completions.create.return_value = mock_completion
    
    result = openai_service.format_json_response("raw response text")
    
    assert result["title"] == "Test Video"
    assert result["channel"] == "Test Channel"
    assert result["channelLink"] == "https://youtube.com/channel"
    assert result["url"] == "https://youtube.com/watch"
    mock_openai.chat.completions.create.assert_called_once()

def test_format_json_response_missing_fields(openai_service, mock_openai):
    """Test JSON response formatting with missing fields."""
    mock_completion = MagicMock()
    mock_completion.choices = [
        MagicMock(
            message=MagicMock(
                content='{"title": "Test Video"}'
            )
        )
    ]
    mock_openai.chat.completions.create.return_value = mock_completion
    
    result = openai_service.format_json_response("raw response text")
    
    assert result["title"] == "Test Video"
    assert result["channel"] == ""
    assert result["channelLink"] == ""
    assert result["url"] == ""

def test_format_json_response_failure(openai_service, mock_openai):
    """Test JSON response formatting failure."""
    mock_openai.chat.completions.create.side_effect = Exception("API Error")
    
    result = openai_service.format_json_response("raw response text")
    
    assert result["error"] == "API Error"
    assert result["title"] == ""
    assert result["channel"] == ""
    assert result["channelLink"] == ""
    assert result["url"] == "" 