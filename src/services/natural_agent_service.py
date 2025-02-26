import logging
from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.schema.messages import AIMessage, HumanMessage, SystemMessage
from langchain.tools import Tool
from langchain_openai import ChatOpenAI
from src.api.apify_client import apify_service
from src.config.settings import OPENAI_API_KEY

logger = logging.getLogger(__name__)

def create_youtube_search_tool():
    """Create a tool for YouTube search using the Apify service."""
    def search_youtube(query: str, max_results: int = 10) -> str:
        results = apify_service.search_youtube_podcasts(query, max_results)
        return str(results)
    
    return Tool(
        name="search_youtube",
        description="Search for YouTube podcasts with given query",
        func=search_youtube
    )

class NaturalAgentService:
    def __init__(self):
        # LLM for evaluation with JSON response format
        self.eval_llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY,
            response_format={"type": "json_object"}
        )
        
        # LLM for search agent without JSON format constraint
        self.search_llm = ChatOpenAI(
            temperature=0.7,
            model="gpt-4o-mini",
            api_key=OPENAI_API_KEY
        )
        
        self.tools = [create_youtube_search_tool()]
        
        # Evaluation system prompt
        self.eval_system_prompt = """You are a podcast search expert. Your task is to evaluate search results and determine if they are satisfactory.
        You MUST respond with a JSON object containing exactly these fields:
        {
            "satisfied": boolean,
            "reason": string explaining your decision,
            "suggested_queries": list of alternative search queries if not satisfied (empty list if satisfied)
        }
        
        Consider these criteria:
        1. Relevance to the search intent
        2. Variety of content and perspectives
        3. Credibility of the channels
        4. Video quality and engagement metrics
        
        Be specific in your reasoning and suggest targeted alternative queries if needed."""
        
        # Evaluation prompt template
        self.eval_prompt = """Evaluate these YouTube podcast search results for the query: "{query}"

Search Results:
{results}

Analyze the results and provide your evaluation in the required JSON format.
Remember to be specific about why the results are or aren't satisfactory."""
        
        # Agent prompt for refined searches
        agent_prompt = ChatPromptTemplate.from_messages([
            SystemMessage(content=(
                "You are an AI agent specialized in finding relevant podcast content. "
                "Your task is to try different search queries and combine the best results. "
                "For each suggested query:\n"
                "1. Use the search_youtube tool to find results\n"
                "2. Evaluate the relevance and quality of results\n"
                "3. Keep track of the best results you find\n\n"
                "After trying all queries, return a list of the most relevant and high-quality results. "
                "Ensure you maintain variety while focusing on relevance to the original query."
            )),
            MessagesPlaceholder(variable_name="chat_history"),
            HumanMessage(content=(
                "Find the best podcast results for the original query: {input}\n"
                "Try these alternative queries: {alternative_queries}\n"
                "Return a list of the most relevant results you find."
            )),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
        
        self.agent = create_openai_functions_agent(
            llm=self.search_llm,  # Use the non-JSON format LLM for the agent
            prompt=agent_prompt,
            tools=self.tools
        )
        
        self.agent_executor = AgentExecutor(
            agent=self.agent,
            tools=self.tools,
            verbose=True,
            max_iterations=len(self.tools) * 2  # Allow more iterations for multiple searches
        )
    
    def evaluate_results(self, query: str, results: list) -> dict:
        """
        Have the LLM evaluate search results and suggest alternative queries if needed.
        """
        try:
            # Format results for better readability
            formatted_results = []
            for r in results:
                formatted_results.append({
                    'title': r.get('title', ''),
                    'channel': r.get('channelName', ''),
                    'views': r.get('viewCount', 0),
                    'date': r.get('date', '')
                })
            
            # Create messages for the chat
            messages = [
                {"role": "system", "content": self.eval_system_prompt},
                {"role": "user", "content": self.eval_prompt.format(
                    query=query,
                    results=formatted_results
                )}
            ]
            
            # Get evaluation from LLM
            response = self.eval_llm.invoke(messages)  # Use eval_llm for JSON responses
            
            # Parse the JSON response
            if hasattr(response, 'content'):
                import json
                evaluation = json.loads(response.content)
                
                # Validate response format
                required_fields = ['satisfied', 'reason', 'suggested_queries']
                if all(field in evaluation for field in required_fields):
                    # Limit number of alternative queries
                    evaluation['suggested_queries'] = evaluation['suggested_queries'][:3]
                    return evaluation
                
                logger.error("Invalid response format from LLM")
                
            return {
                "satisfied": True,
                "reason": "Could not properly evaluate results",
                "suggested_queries": []
            }
            
        except Exception as e:
            logger.error(f"Failed to evaluate results: {str(e)}")
            return {
                "satisfied": True,
                "reason": f"Error in evaluation: {str(e)}",
                "suggested_queries": []
            }
    
    def search(self, query: str, max_results: int = 10) -> list:
        """
        Perform an agent-based search for YouTube podcasts.
        First tries normal search, then refines if needed.
        
        Args:
            query (str): The search query
            max_results (int): Maximum number of results to return
            
        Returns:
            list: List of search results
        """
        try:
            # First, try normal search
            initial_results = apify_service.search_youtube_podcasts(query, max_results)
            if not initial_results:
                logger.warning("No initial results found")
                return []
            
            # Evaluate the results
            evaluation = self.evaluate_results(query, initial_results)
            
            # If satisfied with initial results, return them
            if evaluation["satisfied"]:
                logger.info(f"Satisfied with initial results for query: {query}")
                return initial_results
            
            # If not satisfied and we have suggested queries, try them
            if evaluation["suggested_queries"]:
                logger.info(f"Trying alternative queries: {evaluation['suggested_queries']}")
                
                # Collect all results from different queries
                all_results = []
                for alt_query in evaluation["suggested_queries"]:
                    try:
                        results = apify_service.search_youtube_podcasts(alt_query, max_results)
                        if results:
                            all_results.extend(results)
                    except Exception as e:
                        logger.error(f"Error searching with query '{alt_query}': {str(e)}")
                
                if all_results:
                    # Remove duplicates based on video ID
                    seen_ids = set()
                    unique_results = []
                    for result in all_results:
                        if result.get('id') not in seen_ids:
                            seen_ids.add(result.get('id'))
                            unique_results.append(result)
                    
                    # Return top results up to max_results
                    return unique_results[:max_results]
                else:
                    logger.warning("No results found with alternative queries")
                    return initial_results
            
            # If no suggested queries, return initial results
            return initial_results
            
        except Exception as e:
            logger.error(f"Search failed: {str(e)}")
            return [] 