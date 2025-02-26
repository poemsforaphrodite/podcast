import logging
from openai import OpenAI
from src.config.settings import OPENAI_API_KEY, WHISPER_MODEL

logger = logging.getLogger(__name__)

class OpenAIService:
    def __init__(self):
        self.client = OpenAI(api_key=OPENAI_API_KEY)
    
    def transcribe_audio(self, audio_file_path):
        """
        Transcribe audio using OpenAI's Whisper model.
        
        Args:
            audio_file_path (str): Path to the audio file
            
        Returns:
            str: Transcribed text or error message
        """
        try:
            with open(audio_file_path, "rb") as audio_file:
                transcript = self.client.audio.transcriptions.create(
                    file=audio_file,
                    model=WHISPER_MODEL,
                    response_format="text"
                )
            logger.info("Audio transcription completed successfully")
            return transcript
            
        except Exception as e:
            error_msg = f"Transcription failed: {str(e)}"
            logger.error(error_msg)
            return error_msg
    
    def format_json_response(self, raw_response):
        """
        Use GPT to format raw response into valid JSON.
        
        Args:
            raw_response (str): Raw API response to format
            
        Returns:
            dict: Formatted JSON response
        """
        try:
            system_prompt = """You are a JSON formatting assistant. Extract the YouTube video information from the provided response and return it as a JSON object with these fields:
            - title: The title of the YouTube video
            - channel: The name of the YouTube channel
            - channelLink: The link to the YouTube channel
            - url: The direct URL to the YouTube video
            
            Look for this information in the entire response, including any thinking process or analysis. Return only the JSON object."""
            
            user_prompt = f"Here's the complete response. Please extract the video information and return it as JSON:\n{raw_response}"
            
            completion = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            formatted_response = completion.choices[0].message.content
            logger.info("Successfully formatted JSON response")
            
            # Ensure all required fields are present
            required_fields = ['title', 'channel', 'channelLink', 'url']
            formatted_dict = eval(formatted_response)
            for field in required_fields:
                if field not in formatted_dict:
                    formatted_dict[field] = ""
                    
            return formatted_dict
            
        except Exception as e:
            error_msg = f"Error in GPT formatting: {str(e)}"
            logger.error(error_msg)
            return {
                "title": "",
                "channel": "",
                "channelLink": "",
                "url": "",
                "error": str(e)
            }

# Initialize the service
openai_service = OpenAIService() 