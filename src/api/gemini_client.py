import logging
import os
import time
import requests
from src.config.settings import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

def gemini_process_video(video_path):
    """
    Process video content using Google's Gemini API.
    
    Args:
        video_path (str): Path to the video file
        
    Returns:
        dict: Analysis results or error information
    """
    try:
        if not os.path.exists(video_path):
            return {"error": f"Video file not found: {video_path}"}

        API_KEY = GEMINI_API_KEY
        BASE_URL = "https://generativelanguage.googleapis.com"
        UPLOAD_ENDPOINT = f"{BASE_URL}/upload/v1beta/files?key={API_KEY}"
        GENERATE_ENDPOINT = f"{BASE_URL}/v1beta/models/{GEMINI_MODEL}:generateContent?key={API_KEY}"

        mime_type = "video/mp4"
        display_name = "Podcast Analysis Video"
        num_bytes = os.path.getsize(video_path)

        # Initialize upload
        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(num_bytes),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json"
        }
        metadata = {"file": {"display_name": display_name}}

        response = requests.post(UPLOAD_ENDPOINT, headers=headers, json=metadata)
        upload_url = response.headers.get("x-goog-upload-url")
        if not upload_url:
            raise Exception("Failed to initiate upload session")

        # Upload video
        with open(video_path, "rb") as f:
            video_data = f.read()

        upload_headers = {
            "Content-Length": str(num_bytes),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize"
        }
        upload_response = requests.post(upload_url, headers=upload_headers, data=video_data)
        upload_response.raise_for_status()
        upload_result = upload_response.json()
        file_uri = upload_result["file"]["uri"]

        # Wait for processing
        time.sleep(10)

        # Generate content analysis
        prompt = """Please analyze this video and return the information in the following JSON format:
        {
            "title": "The title of the YouTube video",
            "channel": "The name of the YouTube channel",
            "channelLink": "The link to the YouTube channel",
            "url": "The direct URL to the YouTube video"
        }
        
        If any field cannot be determined, use an empty string."""

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"file_data": {"file_uri": file_uri, "mime_type": mime_type}}
                    ]
                }
            ],
            "generation_config": {
                "maxOutputTokens": 1024,
                "temperature": 0.5,
                "topP": 0.8
            }
        }
        
        generate_headers = {"Content-Type": "application/json"}
        gen_response = requests.post(GENERATE_ENDPOINT, headers=generate_headers, json=payload)
        gen_response.raise_for_status()
        gen_result = gen_response.json()

        analysis_text = (gen_result.get("candidates", [{}])[0]
                                .get("content", {})
                                .get("parts", [{}])[0]
                                .get("text", "No analysis returned"))

        logger.info("Video analysis completed successfully")
        return {"raw_response": analysis_text}

    except Exception as e:
        error_msg = f"Error in Gemini processing: {str(e)}"
        logger.error(error_msg)
        return {"error": error_msg} 