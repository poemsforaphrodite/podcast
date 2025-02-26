import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# API Keys and URLs
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
APIFY_API_TOKEN = os.getenv("APIFY_API_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
PERPLEXITY_API_KEY = os.getenv("PERPLEXITY_API_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# App Configuration
APP_TITLE = "Podcast Trend Finder"
APP_ICON = "🎙️"
DEFAULT_MAX_RESULTS = 10
MAX_VIDEO_SIZE_MB = 50

# API Configuration
PERPLEXITY_MODEL = "sonar-pro"
WHISPER_MODEL = "whisper-1"
GEMINI_MODEL = "gemini-1.5-flash"

# Default Instagram Channels
DEFAULT_CHANNELS = [
    "neuroglobe",
    "biohackyourselfmedia",
    "longevity2.0"
]

# Analysis Methods
ANALYSIS_METHODS = ["Caption", "Transcription", "Gemini"] 