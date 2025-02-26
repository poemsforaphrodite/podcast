import pytest
import os
import tempfile
from unittest.mock import MagicMock

@pytest.fixture
def mock_env(monkeypatch):
    """Mock environment variables for testing."""
    env_vars = {
        "SUPABASE_URL": "https://test.supabase.co",
        "SUPABASE_KEY": "test-key",
        "APIFY_API_TOKEN": "test-token",
        "OPENAI_API_KEY": "test-key",
        "PERPLEXITY_API_KEY": "test-key",
        "GEMINI_API_KEY": "test-key"
    }
    for key, value in env_vars.items():
        monkeypatch.setenv(key, value)
    return env_vars

@pytest.fixture
def sample_video_file():
    """Create a temporary video file for testing."""
    with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as tmp_file:
        tmp_file.write(b"dummy video content")
        tmp_file.flush()
        yield tmp_file.name
    os.unlink(tmp_file.name)

@pytest.fixture
def mock_requests(monkeypatch):
    """Mock requests library for testing."""
    mock = MagicMock()
    mock.post.return_value.status_code = 200
    mock.post.return_value.json.return_value = {"success": True}
    monkeypatch.setattr("requests.post", mock.post)
    monkeypatch.setattr("requests.get", mock.get)
    return mock

@pytest.fixture
def sample_instagram_post():
    """Sample Instagram post data for testing."""
    return {
        "id": "test123",
        "caption": "Check out my latest podcast episode on YouTube!",
        "timestamp": "2024-02-26T12:00:00Z",
        "likesCount": 100,
        "commentsCount": 50,
        "videoUrl": "https://example.com/video.mp4"
    }

@pytest.fixture
def sample_youtube_result():
    """Sample YouTube search result for testing."""
    return {
        "title": "Test Podcast Episode",
        "channelName": "Test Channel",
        "viewCount": "1000",
        "duration": "1:00:00",
        "date": "2024-02-26",
        "url": "https://youtube.com/watch?v=test123"
    } 