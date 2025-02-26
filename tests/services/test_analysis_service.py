import pytest
from unittest.mock import MagicMock, patch
from src.services.analysis_service import analyze_selected_posts

@pytest.fixture
def mock_services():
    """Mock all dependent services."""
    with patch('src.services.analysis_service.perplexity_search') as mock_perplexity, \
         patch('src.services.analysis_service.openai_service') as mock_openai, \
         patch('src.services.analysis_service.gemini_process_video') as mock_gemini, \
         patch('src.services.analysis_service.download_video') as mock_download:
        yield {
            'perplexity': mock_perplexity,
            'openai': mock_openai,
            'gemini': mock_gemini,
            'download': mock_download
        }

def test_analyze_caption(mock_services, sample_instagram_post):
    """Test caption analysis method."""
    mock_services['perplexity'].return_value = {"raw_response": "test response"}
    mock_services['openai'].format_json_response.return_value = {
        "title": "Test Video",
        "channel": "Test Channel",
        "channelLink": "https://youtube.com/channel",
        "url": "https://youtube.com/watch"
    }
    
    results = analyze_selected_posts(
        [sample_instagram_post],
        [sample_instagram_post['id']],
        "Caption"
    )
    
    assert len(results) == 1
    assert results[0]["post_id"] == sample_instagram_post['id']
    assert "title" in results[0]["raw_response"]
    mock_services['perplexity'].assert_called_once()
    mock_services['openai'].format_json_response.assert_called_once()

def test_analyze_transcription(mock_services, sample_instagram_post):
    """Test transcription analysis method."""
    mock_services['download'].return_value = ("test_path", None)
    mock_services['openai'].transcribe_audio.return_value = "test transcript"
    mock_services['perplexity'].return_value = {"raw_response": "test response"}
    mock_services['openai'].format_json_response.return_value = {
        "title": "Test Video",
        "channel": "Test Channel",
        "channelLink": "https://youtube.com/channel",
        "url": "https://youtube.com/watch"
    }
    
    results = analyze_selected_posts(
        [sample_instagram_post],
        [sample_instagram_post['id']],
        "Transcription"
    )
    
    assert len(results) == 1
    assert results[0]["post_id"] == sample_instagram_post['id']
    assert "title" in results[0]["raw_response"]
    mock_services['openai'].transcribe_audio.assert_called_once()
    mock_services['perplexity'].assert_called_once()

def test_analyze_gemini(mock_services, sample_instagram_post):
    """Test Gemini analysis method."""
    mock_services['download'].return_value = ("test_path", None)
    mock_services['gemini'].return_value = {"raw_response": "test response"}
    mock_services['openai'].format_json_response.return_value = {
        "title": "Test Video",
        "channel": "Test Channel",
        "channelLink": "https://youtube.com/channel",
        "url": "https://youtube.com/watch"
    }
    
    results = analyze_selected_posts(
        [sample_instagram_post],
        [sample_instagram_post['id']],
        "Gemini"
    )
    
    assert len(results) == 1
    assert results[0]["post_id"] == sample_instagram_post['id']
    assert "title" in results[0]["raw_response"]
    mock_services['gemini'].assert_called_once()

def test_analyze_download_error(mock_services, sample_instagram_post):
    """Test analysis with video download error."""
    mock_services['download'].return_value = (None, "Download error")
    
    results = analyze_selected_posts(
        [sample_instagram_post],
        [sample_instagram_post['id']],
        "Transcription"
    )
    
    assert len(results) == 1
    assert results[0]["post_id"] == sample_instagram_post['id']
    assert "error" in results[0]["raw_response"]
    mock_services['openai'].transcribe_audio.assert_not_called()

def test_analyze_service_error(mock_services, sample_instagram_post):
    """Test analysis with service error."""
    mock_services['perplexity'].side_effect = Exception("Service error")
    
    results = analyze_selected_posts(
        [sample_instagram_post],
        [sample_instagram_post['id']],
        "Caption"
    )
    
    assert len(results) == 1
    assert results[0]["post_id"] == sample_instagram_post['id']
    assert "error" in results[0]["raw_response"] 