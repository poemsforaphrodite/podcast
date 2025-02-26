import logging
from supabase import create_client
from src.config.settings import SUPABASE_URL, SUPABASE_KEY

logger = logging.getLogger(__name__)

def get_supabase_client():
    """Initialize Supabase client with error handling."""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be provided")
        
        client = create_client(SUPABASE_URL, SUPABASE_KEY)
        logger.info("Supabase client initialized successfully")
        return client
    
    except Exception as e:
        logger.error(f"Failed to initialize Supabase client: {str(e)}")
        return None

# Initialize the client
supabase = get_supabase_client() 