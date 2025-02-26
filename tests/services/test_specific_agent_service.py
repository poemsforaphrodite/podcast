import pytest
from unittest.mock import Mock, patch
from src.services.channel_agent_service import SpecificAgentService, create_instagram_search_tool, create_analysis_tool

# Sample test data
SAMPLE_POSTS = [
    {
        'id': 'post1',
        'caption': 'New podcast episode out now! Check the link in bio',
        'likesCount': 1000,
        'commentsCount': 50,
        'timestamp': '2024-02-01T12:00:00Z',
        'videoUrl': 'https://example.com/video1.mp4'
    },
    {
        'id': 'post2',
        'caption': 'Behind the scenes of today\'s podcast recording',
        'likesCount': 2000,
        'commentsCount': 100,
        'timestamp': '2024-02-02T12:00:00Z',
        'videoUrl': None
    }
]

SAMPLE_EVALUATION_SATISFIED = {
    "satisfied": True,
    "reason": "Posts contain relevant podcast content with good engagement",
    "suggested_usernames": [],
    "selected_posts": ["post1"]
}

SAMPLE_EVALUATION_UNSATISFIED = {
    "satisfied": False,
    "reason": "Limited podcast-related content",
    "suggested_usernames": ["better_podcaster1", "better_podcaster2"],
    "selected_posts": []
}

@pytest.fixture
def mock_apify_service():
    with patch('src.services.channel_agent_service.apify_service') as mock:
        mock.search_instagram_posts.return_value = SAMPLE_POSTS
        yield mock

@pytest.fixture
def mock_analysis_service():
    with patch('src.services.channel_agent_service.analyze_selected_posts') as mock:
        mock.return_value = [{"post_id": "post1", "analysis": "Found podcast reference"}]
        yield mock

@pytest.fixture
def mock_openai():
    with patch('src.services.channel_agent_service.ChatOpenAI') as mock:
        # Create mock instances for both LLMs
        eval_llm_mock = Mock()
        analysis_llm_mock = Mock()
        
        # Configure the eval_llm mock
        eval_response = Mock()
        eval_response.content = '{"satisfied": true, "reason": "Good posts", "suggested_usernames": [], "selected_posts": ["post1"]}'
        eval_llm_mock.invoke.return_value = eval_response
        
        # Configure the analysis_llm mock
        analysis_response = Mock()
        analysis_response.content = str([{"post_id": "post1", "analysis": "Found podcast reference"}])
        analysis_llm_mock.invoke.return_value = analysis_response
        
        # Make the mock return different instances for different configurations
        def mock_init(*args, **kwargs):
            if kwargs.get('response_format', {}).get('type') == 'json_object':
                return eval_llm_mock
            return analysis_llm_mock
        
        mock.side_effect = mock_init
        yield mock

class TestSpecificAgentService:
    def test_initialization(self, mock_openai):
        """Test that the service initializes correctly"""
        service = SpecificAgentService()
        assert service.tools is not None
        assert len(service.tools) == 4  # Instagram search + 3 analysis methods
        assert any(tool.name == "search_instagram" for tool in service.tools)
        assert any(tool.name == "analyze_caption" for tool in service.tools)
    
    def test_evaluate_posts_satisfied(self, mock_openai):
        """Test evaluation when posts are satisfactory"""
        service = SpecificAgentService()
        
        # Configure mock response
        eval_response = Mock()
        eval_response.content = '{"satisfied": true, "reason": "Good posts", "suggested_usernames": [], "selected_posts": ["post1"]}'
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        result = service.evaluate_posts("test_user", SAMPLE_POSTS)
        assert result["satisfied"] is True
        assert "reason" in result
        assert "suggested_usernames" in result
        assert "selected_posts" in result
        assert len(result["suggested_usernames"]) == 0
        assert len(result["selected_posts"]) > 0
    
    def test_evaluate_posts_unsatisfied(self, mock_openai):
        """Test evaluation when posts are unsatisfactory"""
        service = SpecificAgentService()
        
        # Configure mock response
        eval_response = Mock()
        eval_response.content = '''
        {
            "satisfied": false,
            "reason": "Need better content",
            "suggested_usernames": ["user1", "user2", "user3", "user4"],
            "selected_posts": []
        }
        '''
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        result = service.evaluate_posts("test_user", SAMPLE_POSTS)
        assert result["satisfied"] is False
        assert "reason" in result
        assert len(result["suggested_usernames"]) <= 3  # Should be limited to 3 usernames
    
    def test_evaluate_posts_error_handling(self, mock_openai):
        """Test evaluation error handling"""
        service = SpecificAgentService()
        
        # Configure mock to raise an exception
        service.eval_llm.invoke = Mock(side_effect=Exception("Test error"))
        
        result = service.evaluate_posts("test_user", SAMPLE_POSTS)
        assert result["satisfied"] is True  # Default to satisfied on error
        assert "Error in evaluation" in result["reason"]
        assert result["suggested_usernames"] == []
        assert result["selected_posts"] == []
    
    def test_analyze_channel_satisfied(self, mock_apify_service, mock_openai, mock_analysis_service):
        """Test channel analysis when satisfied with initial posts"""
        service = SpecificAgentService()
        
        # Configure evaluation to be satisfied
        eval_response = Mock()
        eval_response.content = '{"satisfied": true, "reason": "Good posts", "suggested_usernames": [], "selected_posts": ["post1"]}'
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        all_posts, analysis_results, evaluation = service.analyze_channel("test_user")
        assert all_posts == SAMPLE_POSTS
        assert len(analysis_results) > 0
        assert evaluation["satisfied"] is True
        mock_apify_service.search_instagram_posts.assert_called_once()
    
    def test_analyze_channel_with_alternatives(self, mock_apify_service, mock_openai, mock_analysis_service):
        """Test channel analysis with alternative usernames"""
        service = SpecificAgentService()
        
        # Configure evaluation to be unsatisfied initially
        eval_response_unsatisfied = Mock()
        eval_response_unsatisfied.content = '''
        {
            "satisfied": false,
            "reason": "Need better content",
            "suggested_usernames": ["better_user1", "better_user2"],
            "selected_posts": []
        }
        '''
        
        # Configure evaluation to be satisfied after trying alternatives
        eval_response_satisfied = Mock()
        eval_response_satisfied.content = '''
        {
            "satisfied": true,
            "reason": "Found good content",
            "suggested_usernames": [],
            "selected_posts": ["post1"]
        }
        '''
        
        service.eval_llm.invoke = Mock(side_effect=[
            eval_response_unsatisfied,  # First evaluation
            eval_response_satisfied     # Second evaluation after alternatives
        ])
        
        # Configure different results for different usernames
        alt_posts = [
            {'id': 'post3', 'caption': 'Great podcast content'},
            {'id': 'post4', 'caption': 'More podcast stuff'}
        ]
        mock_apify_service.search_instagram_posts.side_effect = [
            SAMPLE_POSTS,  # Initial search
            alt_posts,     # First alternative
            alt_posts      # Second alternative
        ]
        
        all_posts, analysis_results, evaluation = service.analyze_channel("test_user")
        assert len(all_posts) > len(SAMPLE_POSTS)  # Should include posts from alternatives
        assert evaluation["satisfied"] is True
        assert mock_apify_service.search_instagram_posts.call_count > 1
    
    def test_analyze_channel_error_handling(self, mock_apify_service, mock_openai):
        """Test channel analysis error handling"""
        service = SpecificAgentService()
        
        # Configure mock to raise an exception
        mock_apify_service.search_instagram_posts.side_effect = Exception("Test error")
        
        all_posts, analysis_results, evaluation = service.analyze_channel("test_user")
        assert all_posts == []
        assert analysis_results == []
        assert evaluation is None
    
    def test_analyze_channel_no_initial_posts(self, mock_apify_service, mock_openai):
        """Test channel analysis when no initial posts are found"""
        service = SpecificAgentService()
        
        # Configure mock to return empty results
        mock_apify_service.search_instagram_posts.return_value = []
        
        all_posts, analysis_results, evaluation = service.analyze_channel("test_user")
        assert all_posts == []
        assert analysis_results == []
        assert evaluation is None
        assert mock_apify_service.search_instagram_posts.call_count == 1 