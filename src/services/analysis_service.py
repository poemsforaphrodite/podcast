import logging
import os
from src.api.perplexity_api import perplexity_search
from src.api.openai_client import openai_service
from src.api.gemini_client import gemini_process_video
from src.services.video_service import download_video

logger = logging.getLogger(__name__)

def analyze_selected_posts(posts, selected_ids, method):
    """
    Analyze selected posts using the specified method.
    
    Args:
        posts (list): List of all posts
        selected_ids (list): List of selected post IDs
        method (str): Analysis method to use (Caption/Transcription/Gemini)
        
    Returns:
        list: Analysis results for each selected post
    """
    results = []
    
    for post in posts:
        if post['id'] in selected_ids:
            try:
                if method == "Caption":
                    logger.debug(f"Analyzing caption for post {post['id']}")
                    prompt = """
                    From this Instagram caption: '{}', find the exact YouTube podcast/channel and return the response in JSON format with the following fields: title, channel, channel link, the exact youtube url for the podcast/channel, we want full video of the podcast. 
                    """
                    result = perplexity_search(
                        post.get('caption', ''),
                        prompt
                    )
                    
                    if 'raw_response' in result:
                        # Format the response using GPT
                        formatted_info = openai_service.format_json_response(str(result))
                        results.append({
                            "post_id": post['id'],
                            "raw_response": formatted_info
                        })
                    else:
                        results.append({
                            "post_id": post['id'],
                            "raw_response": {"error": "No valid response"}
                        })
                
                elif method == "Transcription" and post.get('videoUrl'):
                    video_path, error = download_video(post['videoUrl'])
                    if error:
                        results.append({
                            "post_id": post['id'],
                            "raw_response": {"error": error}
                        })
                        continue
                        
                    try:
                        transcript = openai_service.transcribe_audio(video_path)
                        prompt = """
                        Given podcast transcription: '{}', find YouTube link/channel and return the response in JSON format with the following fields:
                        - title: The title of the YouTube video
                        - channel: The name of the YouTube channel
                        - channelLink: The link to the YouTube channel
                        - url: The direct URL to the YouTube video
                        
                        If any field cannot be determined, use an empty string.
                        """
                        result = perplexity_search(transcript, prompt)
                        formatted_info = openai_service.format_json_response(str(result))
                        results.append({
                            "post_id": post['id'],
                            "raw_response": formatted_info
                        })
                    finally:
                        if os.path.exists(video_path):
                            os.unlink(video_path)
                
                elif method == "Gemini" and post.get('videoUrl'):
                    video_path, error = download_video(post['videoUrl'])
                    if error:
                        results.append({
                            "post_id": post['id'],
                            "raw_response": {"error": error}
                        })
                        continue
                        
                    try:
                        result = gemini_process_video(video_path)
                        formatted_info = openai_service.format_json_response(str(result))
                        results.append({
                            "post_id": post['id'],
                            "raw_response": formatted_info
                        })
                    finally:
                        if os.path.exists(video_path):
                            os.unlink(video_path)
                
            except Exception as e:
                error_msg = f"Error processing post {post['id']}: {str(e)}"
                logger.error(error_msg)
                results.append({
                    "post_id": post['id'],
                    "raw_response": {
                        "error": error_msg
                    }
                })
    
    return results 