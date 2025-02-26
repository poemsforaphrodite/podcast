import logging
import requests
from src.config.settings import PERPLEXITY_API_KEY, PERPLEXITY_MODEL

logger = logging.getLogger(__name__)

def perplexity_search(input_text, prompt_template):
    """
    Call Perplexity API with enhanced error handling and debugging.
    
    Args:
        input_text (str): The text to analyze
        prompt_template (str): The prompt template to use
        
    Returns:
        dict: API response or error information
    """
    logger.debug(f"Input text: {input_text}")
    
    try:
        if not input_text or not prompt_template:
            return {
                "error": "Missing required input",
                "details": "Both input_text and prompt_template are required"
            }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {PERPLEXITY_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": PERPLEXITY_MODEL,
                "messages": [
                    {"role": "system", "content": "Return JSON response"},
                    {"role": "user", "content": prompt_template.format(input_text)}
                ]
            },
            timeout=60
        )
        
        response.raise_for_status()
        
        if not response.text.strip():
            return {
                "error": "Empty API response",
                "details": "The API returned an empty response",
                "status_code": response.status_code
            }
        
        result = response.json()
        logger.debug(f"Raw API Response: {result}")
        raw_text = result["choices"][0]["message"]["content"]
        
        return {
            "raw_response": raw_text
        }
    
    except requests.exceptions.Timeout:
        error_msg = "API timeout after 60 seconds"
        logger.error(error_msg)
        return {
            "error": "API timeout",
            "details": error_msg
        }
    except requests.exceptions.RequestException as e:
        error_msg = f"API request failed: {str(e)}"
        logger.error(error_msg)
        return {
            "error": "API request failed",
            "details": error_msg
        }
    except Exception as e:
        error_msg = f"Unexpected error: {str(e)}"
        logger.error(error_msg)
        return {
            "error": "Unexpected error",
            "details": error_msg,
            "raw_response": response.text if 'response' in locals() else None
        } 