import logging
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import SystemMessage, HumanMessage
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from src.api.apify_client import apify_service
from src.services.analysis_service import analyze_selected_posts
from src.config.settings import OPENAI_API_KEY

logger = logging.getLogger(__name__)

def create_instagram_search_tool():
    """Create a tool for Instagram post search."""
    def search_instagram(username: str, max_results: int = 10) -> str:
        if username.startswith('{') and username.endswith('}'):
            # This is a template string that wasn't properly formatted
            logger.warning(f"Received template string instead of actual username: {username}")
            return "Error: Invalid username format. Please provide an actual Instagram username."
        
        logger.info(f"Searching Instagram posts for username: {username}")
        results = apify_service.search_instagram_posts(username, max_results)
        
        if not results:
            return f"No posts found for username: {username}"
        
        # Return simplified version of posts for the agent
        simplified_results = []
        for post in results:
            simplified_results.append({
                'id': post.get('id', ''),
                'caption': post.get('caption', '')[:200] + ('...' if post.get('caption', '') else ''),
                'likesCount': post.get('likesCount', 0),
                'commentsCount': post.get('commentsCount', 0),
                'hasVideo': bool(post.get('videoUrl')),
                'timestamp': post.get('timestamp', '')
            })
        
        return str(simplified_results)
    
    return Tool(
        name="search_instagram",
        description="Search for Instagram posts from a specific username",
        func=search_instagram
    )

def create_analysis_tool(method: str):
    """Create a tool for analyzing posts using a specific method."""
    def analyze_posts(selected_ids: list, all_posts: list = None) -> str:
        if not all_posts:
            return f"Error: No posts provided for {method} analysis"
        
        if not selected_ids or not isinstance(selected_ids, list):
            return f"Error: Invalid post IDs for {method} analysis. Please provide a list of post IDs."
        
        # Filter to only posts with IDs in selected_ids
        if isinstance(selected_ids[0], str):  # If we're given string IDs
            posts_to_analyze = [post for post in all_posts if post.get('id') in selected_ids]
        else:
            # If we're given numeric indices instead
            try:
                indices = [int(idx) for idx in selected_ids if str(idx).isdigit()]
                posts_to_analyze = [all_posts[idx] for idx in indices if 0 <= idx < len(all_posts)]
            except (ValueError, IndexError):
                return f"Error: Invalid post indices for {method} analysis"
        
        if not posts_to_analyze:
            return f"No matching posts found for {method} analysis with IDs: {selected_ids}"
        
        try:
            # Get IDs of posts we're actually analyzing
            ids_to_analyze = [post.get('id') for post in posts_to_analyze]
            results = analyze_selected_posts(all_posts, ids_to_analyze, method)
            return str(results)
        except Exception as e:
            logger.error(f"Error in {method} analysis: {str(e)}")
            return f"Error performing {method} analysis: {str(e)}"
    
    return Tool(
        name=f"analyze_{method.lower()}",
        description=f"Analyze selected posts using {method} method. Requires two parameters: selected_ids (list of post IDs to analyze) and all_posts (list of all post objects).",
        func=analyze_posts
    )

class SpecificAgentService:
    def __init__(self):
        # LLM for evaluation with JSON response format
        self.eval_llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            response_format={"type": "json_object"}
        )
        
        # LLM for analysis agent without JSON constraint
        self.analysis_llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY
        )
        
        # Create tools for different analysis methods
        self.tools = [
            create_instagram_search_tool(),
            create_analysis_tool("Caption"),
            create_analysis_tool("Transcription"),
            create_analysis_tool("Gemini")
        ]
        
        # Evaluation system prompt
        self.eval_system_prompt = """You are an Instagram post analysis expert. Your task is to evaluate posts and determine if they are satisfactory for podcast discovery.
        You MUST respond with a JSON object containing exactly these fields:
        {
            "satisfied": boolean,
            "reason": string explaining your decision,
            "selected_posts": list of post IDs that seem most relevant to podcast discovery
        }
        
        Consider these criteria:
        1. Relevance to podcast content
        2. Recency of posts
        3. Engagement metrics (likes, comments)
        4. Presence of video content
        5. Quality of captions
        
        If the posts don't contain enough podcast-related content, return satisfied=false to fetch more posts from this account."""
        
        # Evaluation prompt template
        self.eval_prompt = """Evaluate these Instagram posts for the username: "{username}"

Posts:
{posts}

Analyze the posts and provide your evaluation in the required JSON format.
Remember to be specific about why the posts are or aren't satisfactory for podcast discovery."""
        
        # Agent prompt for analysis
        agent_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are an AI agent specialized in discovering podcasts through social media analysis. "
                "Your task is to analyze Instagram posts using different methods to find podcast content. "
                "\n\nYou have these tools available:"
                "\n1. search_instagram - Search for Instagram posts from a username"
                "\n2. analyze_caption - Analyze post captions for podcast references"
                "\n3. analyze_transcription - For posts with video, get and analyze transcriptions"
                "\n4. analyze_gemini - Use advanced analysis on posts"
                "\n\nFollow these steps:"
                "\n1. For any posts with podcast-related content in the caption, analyze the caption"
                "\n2. For posts with video content, use transcription and Gemini analysis"
                "\n3. Combine results from all analysis methods used"
                "\n4. Return a structured list of findings about podcasts mentioned in the posts"
                "\n\nYou will be given the username and a list of selected post IDs to analyze."
            )),
            HumanMessage(content=(
                "Analyze these Instagram posts for username: {username}\n"
                "Selected post IDs: {selected_posts}\n"
                "The selected_posts variable contains a list of post IDs that have been identified as potentially containing podcast content.\n"
                "The all_posts variable contains the full post objects for these posts.\n"
                "Your task is to analyze these posts using the available tools and return information about any podcasts mentioned."
            )),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        self.agent = create_openai_functions_agent(
            llm=self.analysis_llm,
            prompt=agent_prompt,
            tools=self.tools
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=len(self.tools) * 2
        )
    
    def evaluate_posts(self, username: str, posts: list) -> dict:
        """
        Evaluate Instagram posts and determine if more posts should be fetched.
        """
        try:
            # Format posts for better readability
            formatted_posts = []
            for p in posts:
                formatted_posts.append({
                    'id': p.get('id', ''),
                    'caption': p.get('caption', '')[:200] + '...',  # Truncate long captions
                    'likesCount': p.get('likesCount', 0),
                    'commentsCount': p.get('commentsCount', 0),
                    'hasVideo': bool(p.get('videoUrl')),
                    'timestamp': p.get('timestamp', '')
                })
            
            # Create messages for the chat
            messages = [
                {"role": "system", "content": self.eval_system_prompt},
                {"role": "user", "content": self.eval_prompt.format(
                    username=username,
                    posts=formatted_posts
                )}
            ]
            
            # Get evaluation from LLM
            response = self.eval_llm.invoke(messages)
            
            # Parse the JSON response
            if hasattr(response, 'content'):
                import json
                evaluation = json.loads(response.content)
                
                # Validate response format
                required_fields = ['satisfied', 'reason', 'selected_posts']
                if all(field in evaluation for field in required_fields):
                    return evaluation
                
                logger.error("Invalid response format from LLM")
            
            return {
                "satisfied": True,
                "reason": "Could not properly evaluate posts",
                "selected_posts": []
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate posts: {str(e)}")
            return {
                "satisfied": True,
                "reason": f"Error in evaluation: {str(e)}",
                "selected_posts": []
            }
    
    def analyze_channel(self, username: str, max_posts: int = 10) -> tuple:
        """
        Analyze a channel's Instagram posts to find podcast content.
        If initial posts are not satisfactory, fetch more posts from the same account.
        
        Args:
            username (str): Instagram username to analyze
            max_posts (int): Initial number of posts to fetch
            
        Returns:
            tuple: (all_posts, analysis_results, evaluation)
        """
        try:
            # First batch of posts
            initial_posts = apify_service.search_instagram_posts(username, max_posts)
            if not initial_posts:
                logger.warning(f"No posts found for username: {username}")
                return [], [], None
            
            # Evaluate the initial posts
            evaluation = self.evaluate_posts(username, initial_posts)
            all_posts = initial_posts
            
            # If not satisfied, fetch more posts from the same account
            if not evaluation["satisfied"]:
                logger.info(f"Initial {max_posts} posts not satisfactory, fetching more posts...")
                
                # Try fetching double the number of posts
                try:
                    more_posts = apify_service.search_instagram_posts(username, max_posts * 2)
                    if more_posts:
                        # Add only new posts that weren't in the initial batch
                        seen_ids = {post['id'] for post in all_posts}
                        new_posts = [post for post in more_posts if post['id'] not in seen_ids]
                        if new_posts:
                            all_posts.extend(new_posts)
                            logger.info(f"Found {len(new_posts)} additional posts")
                            # Re-evaluate with all posts
                            evaluation = self.evaluate_posts(username, all_posts)
                except Exception as e:
                    logger.error(f"Error fetching additional posts: {str(e)}")
            
            # If we have selected posts, analyze them
            analysis_results = []
            if evaluation["selected_posts"] and len(evaluation["selected_posts"]) > 0:
                try:
                    # Get the actual selected posts objects
                    post_ids = evaluation["selected_posts"]
                    selected_posts = [post for post in all_posts if post.get('id') in post_ids]
                    
                    if not selected_posts:
                        logger.warning(f"No matching posts found for selected IDs: {post_ids}")
                        return all_posts, [], evaluation
                    
                    # Create a structured result for each post
                    post_analyses = {}
                    
                    # First analyze captions for all posts
                    logger.info(f"Analyzing captions for {len(selected_posts)} posts")
                    caption_tool = next((t for t in self.tools if t.name == "analyze_caption"), None)
                    if caption_tool:
                        caption_results = caption_tool.func(selected_ids=post_ids, all_posts=all_posts)
                        try:
                            if caption_results.startswith('[') and caption_results.endswith(']'):
                                parsed_results = eval(caption_results)
                                if parsed_results:
                                    # Map caption results to posts by ID
                                    for result in parsed_results:
                                        post_id = result.get('post_id')
                                        if post_id:
                                            if post_id not in post_analyses:
                                                post_analyses[post_id] = {'caption_analysis': None, 'transcription_analysis': None, 'gemini_analysis': None}
                                            post_analyses[post_id]['caption_analysis'] = result
                        except Exception as e:
                            logger.error(f"Error parsing caption results: {str(e)}")
                    
                    # Then analyze videos if present
                    video_posts = [post for post in selected_posts if post.get('videoUrl')]
                    if video_posts:
                        logger.info(f"Analyzing {len(video_posts)} video posts")
                        video_ids = [post.get('id') for post in video_posts]
                        
                        # Transcription analysis
                        transcription_tool = next((t for t in self.tools if t.name == "analyze_transcription"), None)
                        if transcription_tool:
                            trans_results = transcription_tool.func(selected_ids=video_ids, all_posts=all_posts)
                            try:
                                if trans_results.startswith('[') and trans_results.endswith(']'):
                                    parsed_results = eval(trans_results)
                                    if parsed_results:
                                        # Map transcription results to posts by ID
                                        for result in parsed_results:
                                            post_id = result.get('post_id')
                                            if post_id:
                                                if post_id not in post_analyses:
                                                    post_analyses[post_id] = {'caption_analysis': None, 'transcription_analysis': None, 'gemini_analysis': None}
                                                post_analyses[post_id]['transcription_analysis'] = result
                            except Exception as e:
                                logger.error(f"Error parsing transcription results: {str(e)}")
                        
                        # Gemini analysis
                        gemini_tool = next((t for t in self.tools if t.name == "analyze_gemini"), None)
                        if gemini_tool:
                            gemini_results = gemini_tool.func(selected_ids=video_ids, all_posts=all_posts)
                            try:
                                if gemini_results.startswith('[') and gemini_results.endswith(']'):
                                    parsed_results = eval(gemini_results)
                                    if parsed_results:
                                        # Map Gemini results to posts by ID
                                        for result in parsed_results:
                                            post_id = result.get('post_id')
                                            if post_id:
                                                if post_id not in post_analyses:
                                                    post_analyses[post_id] = {'caption_analysis': None, 'transcription_analysis': None, 'gemini_analysis': None}
                                                post_analyses[post_id]['gemini_analysis'] = result
                            except Exception as e:
                                logger.error(f"Error parsing Gemini results: {str(e)}")
                    
                    # Create the final combined results with post details
                    for post in selected_posts:
                        post_id = post.get('id')
                        if post_id in post_analyses:
                            # Extract raw_response data from each analysis
                            caption_data = {}
                            if post_analyses[post_id].get('caption_analysis'):
                                if isinstance(post_analyses[post_id]['caption_analysis'].get('raw_response'), dict):
                                    caption_data = post_analyses[post_id]['caption_analysis'].get('raw_response', {})
                                elif isinstance(post_analyses[post_id]['caption_analysis'].get('raw_response'), str):
                                    try:
                                        import json
                                        caption_data = json.loads(post_analyses[post_id]['caption_analysis'].get('raw_response'))
                                    except:
                                        caption_data = {"analysis": post_analyses[post_id]['caption_analysis'].get('raw_response', 'No caption analysis')}
                            
                            transcription_data = {}
                            if post_analyses[post_id].get('transcription_analysis'):
                                if isinstance(post_analyses[post_id]['transcription_analysis'].get('raw_response'), dict):
                                    transcription_data = post_analyses[post_id]['transcription_analysis'].get('raw_response', {})
                                elif isinstance(post_analyses[post_id]['transcription_analysis'].get('raw_response'), str):
                                    try:
                                        import json
                                        transcription_data = json.loads(post_analyses[post_id]['transcription_analysis'].get('raw_response'))
                                    except:
                                        transcription_data = {"analysis": post_analyses[post_id]['transcription_analysis'].get('raw_response', 'No transcription available')}
                            
                            gemini_data = {}
                            if post_analyses[post_id].get('gemini_analysis'):
                                if isinstance(post_analyses[post_id]['gemini_analysis'].get('raw_response'), dict):
                                    gemini_data = post_analyses[post_id]['gemini_analysis'].get('raw_response', {})
                                elif isinstance(post_analyses[post_id]['gemini_analysis'].get('raw_response'), str):
                                    try:
                                        import json
                                        gemini_data = json.loads(post_analyses[post_id]['gemini_analysis'].get('raw_response'))
                                    except:
                                        gemini_data = {"analysis": post_analyses[post_id]['gemini_analysis'].get('raw_response', 'No Gemini analysis')}

                            # Compile podcast data from all sources for the summary table
                            youtube_links = []
                            for data_source in [caption_data, transcription_data, gemini_data]:
                                if data_source and isinstance(data_source, dict):
                                    podcast_entry = {}
                                    if 'title' in data_source:
                                        podcast_entry['title'] = data_source.get('title', '')
                                    if 'channel' in data_source:
                                        podcast_entry['channel'] = data_source.get('channel', '')
                                    if 'channelLink' in data_source:
                                        podcast_entry['channelLink'] = data_source.get('channelLink', '')
                                    if 'url' in data_source:
                                        podcast_entry['url'] = data_source.get('url', '')
                                    
                                    if podcast_entry and any(podcast_entry.values()):
                                        if podcast_entry not in youtube_links:
                                            youtube_links.append(podcast_entry)
                            
                            # Create a comprehensive result entry
                            result_entry = {
                                'post_id': post_id,
                                'instagram_post': {
                                    'username': username,
                                    'url': post.get('url', ''),
                                    'caption': post.get('caption', '')[:300] + ('...' if len(post.get('caption', '')) > 300 else ''),
                                    'likesCount': post.get('likesCount', 0),
                                    'commentsCount': post.get('commentsCount', 0),
                                    'timestamp': post.get('timestamp', ''),
                                    'videoUrl': post.get('videoUrl', '')
                                },
                                'caption_analysis': caption_data.get('analysis', '') if 'analysis' in caption_data else str(caption_data),
                                'transcription_analysis': transcription_data.get('analysis', '') if 'analysis' in transcription_data else str(transcription_data),
                                'gemini_analysis': gemini_data.get('analysis', '') if 'analysis' in gemini_data else str(gemini_data),
                                'youtube_links': youtube_links
                            }
                            
                            # Add extra fields from caption analysis if they exist
                            for source_data in [caption_data, transcription_data, gemini_data]:
                                for key, value in source_data.items():
                                    if key not in ['analysis', 'post_id', 'raw_response'] and value and key not in result_entry:
                                        result_entry[key] = value
                            
                            analysis_results.append(result_entry)
                        else:
                            # Post was selected but no analysis was done
                            analysis_results.append({
                                'post_id': post_id,
                                'instagram_post': {
                                    'username': username,
                                    'url': post.get('url', ''),
                                    'caption': post.get('caption', '')[:300] + ('...' if len(post.get('caption', '')) > 300 else ''),
                                    'likesCount': post.get('likesCount', 0),
                                    'commentsCount': post.get('commentsCount', 0),
                                    'timestamp': post.get('timestamp', ''),
                                    'videoUrl': post.get('videoUrl', '')
                                },
                                'caption_analysis': 'No podcast content found in caption',
                                'transcription_analysis': 'No transcription available',
                                'gemini_analysis': 'No Gemini analysis available'
                            })
                    
                    # If we got no results from direct tool calls, try the agent as a fallback
                    if not analysis_results:
                        logger.info("No results from direct tool calls, trying agent")
                        
                        # Format posts for the agent to use directly
                        formatted_posts = []
                        for post in selected_posts:
                            formatted_posts.append({
                                'id': post.get('id', ''),
                                'url': post.get('url', ''),
                                'caption': post.get('caption', '')[:300] + ('...' if len(post.get('caption', '')) > 300 else ''),
                                'likesCount': post.get('likesCount', 0),
                                'commentsCount': post.get('commentsCount', 0),
                                'hasVideo': bool(post.get('videoUrl')),
                                'timestamp': post.get('timestamp', ''),
                                'videoUrl': post.get('videoUrl', '')
                            })
                        
                        # Create a simple message to analyze without using tools
                        messages = [
                            {"role": "system", "content": "You are a podcast discovery expert. Analyze these Instagram posts and extract any podcast-related information."},
                            {"role": "user", "content": f"Username: {username}\n\nPosts: {formatted_posts}\n\nAnalyze these posts and extract any mentions of podcasts, episodes, or podcast-related content. Return your findings in a structured list format."}
                        ]
                        
                        response = self.analysis_llm.invoke(messages)
                        if hasattr(response, 'content') and response.content:
                            # Create a fallback analysis for each post
                            for post in selected_posts:
                                analysis_results.append({
                                    'post_id': post.get('id'),
                                    'instagram_post': {
                                        'username': username,
                                        'url': post.get('url', ''),
                                        'caption': post.get('caption', '')[:300] + ('...' if len(post.get('caption', '')) > 300 else ''),
                                        'likesCount': post.get('likesCount', 0),
                                        'commentsCount': post.get('commentsCount', 0),
                                        'timestamp': post.get('timestamp', ''),
                                        'videoUrl': post.get('videoUrl', '')
                                    },
                                    'analysis': response.content,
                                    'caption_analysis': 'See combined analysis',
                                    'transcription_analysis': 'See combined analysis',
                                    'gemini_analysis': 'See combined analysis'
                                })
                except Exception as e:
                    logger.error(f"Error in post analysis: {str(e)}")
            
            return all_posts, analysis_results, evaluation
            
        except Exception as e:
            logger.error(f"Channel analysis failed: {str(e)}")
            return [], [], None 