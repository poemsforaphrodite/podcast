import pytest
from unittest.mock import MagicMock, patch
import os
from src.services.video_service import download_video

@pytest.fixture
def mock_response():
    """Mock response for requests."""
    mock = MagicMock()
    mock.headers = {"content-length": "1048576"}  # 1MB
    mock.iter_content.return_value = [b"test content"]
    return mock

def test_download_video_success(mock_requests, mock_response):
    """Test successful video download."""
    mock_requests.get.return_value = mock_response
    
    file_path, error = download_video("https://example.com/video.mp4")
    
    assert error is None
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) > 0
    os.unlink(file_path)

def test_download_video_size_limit(mock_requests):
    """Test video size limit check."""
    mock_response = MagicMock()
    mock_response.headers = {"content-length": str(100 * 1024 * 1024)}  # 100MB
    mock_requests.get.return_value = mock_response
    
    file_path, error = download_video("https://example.com/video.mp4", max_size_mb=50)
    
    assert file_path is None
    assert "exceeds limit" in error

def test_download_video_request_error(mock_requests):
    """Test video download request error."""
    mock_requests.get.side_effect = Exception("Network Error")
    
    file_path, error = download_video("https://example.com/video.mp4")
    
    assert file_path is None
    assert "Unexpected error while downloading video" in error
    assert "Network Error" in error

def test_download_video_no_content_length(mock_requests):
    """Test video download with no content length header."""
    mock_response = MagicMock()
    mock_response.headers = {}
    mock_response.iter_content.return_value = [b"test content"]
    mock_requests.get.return_value = mock_response
    
    file_path, error = download_video("https://example.com/video.mp4")
    
    assert error is None
    assert os.path.exists(file_path)
    os.unlink(file_path)

def test_download_video_empty_response(mock_requests):
    """Test video download with empty response."""
    mock_response = MagicMock()
    mock_response.headers = {"content-length": "0"}
    mock_response.iter_content.return_value = []
    mock_requests.get.return_value = mock_response
    
    file_path, error = download_video("https://example.com/video.mp4")
    
    assert error is None
    assert os.path.exists(file_path)
    assert os.path.getsize(file_path) == 0
    os.unlink(file_path) 