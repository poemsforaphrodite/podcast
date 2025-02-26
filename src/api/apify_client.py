import logging
from apify_client import ApifyClient
from src.config.settings import APIFY_API_TOKEN, DEFAULT_MAX_RESULTS

logger = logging.getLogger(__name__)

class ApifyService:
    def __init__(self):
        self.client = ApifyClient(APIFY_API_TOKEN)
        
    def search_youtube_podcasts(self, query, max_results=DEFAULT_MAX_RESULTS):
        """
        Search for YouTube podcasts with enhanced error handling.
        """
        actor_input = {
            "searchQueries": [query],
            "maxResults": max_results,
            "videoType": "video",
            "sortingOrder": "relevance",
            "dateFilter": "month"
        }
        
        try:
            run = self.client.actor("h7sDV53CddomktSi5").call(run_input=actor_input)
            items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            
            # Ensure all items have a URL
            for item in items:
                if 'url' not in item:
                    video_id = item.get('id', '')
                    item['url'] = f"https://www.youtube.com/watch?v={video_id}"
            
            logger.info(f"Found {len(items)} YouTube results for query: {query}")
            return items
            
        except Exception as e:
            logger.error(f"YouTube search failed: {str(e)}")
            return []

    def search_instagram_posts(self, username, max_results=DEFAULT_MAX_RESULTS):
        """
        Search for Instagram posts with enhanced error handling.
        """
        actor_input = {
            "directUrls": [f"https://www.instagram.com/{username}"],
            "resultsType": "stories",
            "resultsLimit": max_results
        }
        
        try:
            logger.info(f"Searching Instagram posts for username: {username}")
            run = self.client.actor("shu8hvrXbJbY3Eb9W").call(run_input=actor_input)
            items = self.client.dataset(run["defaultDatasetId"]).list_items().items
            logger.info(f"Found {len(items)} Instagram posts for {username}")
            return items
            
        except Exception as e:
            logger.error(f"Instagram search failed for {username}: {str(e)}")
            return []

# Initialize the service
apify_service = ApifyService() 