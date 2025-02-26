import logging
import tempfile
import requests
from src.config.settings import MAX_VIDEO_SIZE_MB

logger = logging.getLogger(__name__)

def download_video(url, max_size_mb=MAX_VIDEO_SIZE_MB):
    """
    Download video with size limit and error handling.
    Returns:
        tuple: (file_path, error_message)
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        content_length = int(response.headers.get('content-length', 0))
        file_size_mb = content_length / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            error_msg = f"Video size ({file_size_mb:.1f}MB) exceeds limit ({max_size_mb}MB)"
            logger.warning(error_msg)
            return None, error_msg
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            logger.info(f"Video downloaded successfully to {tmp_file.name}")
            return tmp_file.name, None
            
    except requests.exceptions.RequestException as e:
        error_msg = f"Failed to download video: {str(e)}"
        logger.error(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"Unexpected error while downloading video: {str(e)}"
        logger.error(error_msg)
        return None, error_msg 