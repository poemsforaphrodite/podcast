import pytest
from unittest.mock import MagicMock, patch
from src.api.apify_client import ApifyService

@pytest.fixture
def mock_apify():
    """Mock Apify client for testing."""
    with patch('src.api.apify_client.ApifyClient') as mock:
        mock_client = MagicMock()
        mock.return_value = mock_client
        yield mock_client

@pytest.fixture
def apify_service(mock_apify, mock_env):
    """Create ApifyService instance with mocked client."""
    return ApifyService()

def test_search_youtube_podcasts_success(apify_service, mock_apify, sample_youtube_result):
    """Test successful YouTube podcast search."""
    mock_dataset = MagicMock()
    mock_dataset.list_items.return_value.items = [sample_youtube_result]
    mock_apify.dataset.return_value = mock_dataset
    mock_apify.actor.return_value.call.return_value = {"defaultDatasetId": "test"}
    
    results = apify_service.search_youtube_podcasts("test query")
    
    assert len(results) == 1
    assert results[0]["title"] == sample_youtube_result["title"]
    assert results[0]["url"] == sample_youtube_result["url"]
    mock_apify.actor.assert_called_once()

def test_search_youtube_podcasts_no_url(apify_service, mock_apify):
    """Test YouTube search with missing URL."""
    result_without_url = {"id": "test123", "title": "Test Video"}
    mock_dataset = MagicMock()
    mock_dataset.list_items.return_value.items = [result_without_url]
    mock_apify.dataset.return_value = mock_dataset
    mock_apify.actor.return_value.call.return_value = {"defaultDatasetId": "test"}
    
    results = apify_service.search_youtube_podcasts("test query")
    
    assert len(results) == 1
    assert results[0]["url"] == "https://www.youtube.com/watch?v=test123"

def test_search_youtube_podcasts_failure(apify_service, mock_apify):
    """Test YouTube search failure."""
    mock_apify.actor.return_value.call.side_effect = Exception("API Error")
    
    results = apify_service.search_youtube_podcasts("test query")
    
    assert len(results) == 0
    mock_apify.actor.assert_called_once()

def test_search_instagram_posts_success(apify_service, mock_apify, sample_instagram_post):
    """Test successful Instagram post search."""
    mock_dataset = MagicMock()
    mock_dataset.list_items.return_value.items = [sample_instagram_post]
    mock_apify.dataset.return_value = mock_dataset
    mock_apify.actor.return_value.call.return_value = {"defaultDatasetId": "test"}
    
    results = apify_service.search_instagram_posts("testuser")
    
    assert len(results) == 1
    assert results[0]["id"] == sample_instagram_post["id"]
    assert results[0]["caption"] == sample_instagram_post["caption"]
    mock_apify.actor.assert_called_once()

def test_search_instagram_posts_failure(apify_service, mock_apify):
    """Test Instagram search failure."""
    mock_apify.actor.return_value.call.side_effect = Exception("API Error")
    
    results = apify_service.search_instagram_posts("testuser")
    
    assert len(results) == 0
    mock_apify.actor.assert_called_once() 