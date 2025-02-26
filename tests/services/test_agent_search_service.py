import pytest
from unittest.mock import Mock, patch
from src.services.agent_search_service import AgentSearchService, create_youtube_search_tool

# Sample test data
SAMPLE_RESULTS = [
    {
        'id': '1',
        'title': 'Sleep Science Explained',
        'channelName': 'Health Podcast',
        'viewCount': 10000,
        'date': '2024-02-01'
    },
    {
        'id': '2',
        'title': 'Understanding Sleep Cycles',
        'channelName': 'Science Channel',
        'viewCount': 20000,
        'date': '2024-02-02'
    }
]

SAMPLE_EVALUATION_SATISFIED = {
    "satisfied": True,
    "reason": "Results are highly relevant and from credible sources",
    "suggested_queries": []
}

SAMPLE_EVALUATION_UNSATISFIED = {
    "satisfied": False,
    "reason": "Results lack variety",
    "suggested_queries": ["better query 1", "better query 2"]
}

@pytest.fixture
def mock_apify_service():
    with patch('src.services.agent_search_service.apify_service') as mock:
        mock.search_youtube_podcasts.return_value = SAMPLE_RESULTS
        yield mock

@pytest.fixture
def mock_openai():
    with patch('src.services.agent_search_service.ChatOpenAI') as mock:
        # Create mock instances for both LLMs
        eval_llm_mock = Mock()
        search_llm_mock = Mock()
        
        # Configure the eval_llm mock
        eval_response = Mock()
        eval_response.content = '{"satisfied": true, "reason": "Good results", "suggested_queries": []}'
        eval_llm_mock.invoke.return_value = eval_response
        
        # Configure the search_llm mock
        search_response = Mock()
        search_response.content = str(SAMPLE_RESULTS)
        search_llm_mock.invoke.return_value = search_response
        
        # Make the mock return different instances for different configurations
        def mock_init(*args, **kwargs):
            if kwargs.get('response_format', {}).get('type') == 'json_object':
                return eval_llm_mock
            return search_llm_mock
        
        mock.side_effect = mock_init
        yield mock

class TestAgentSearchService:
    def test_initialization(self, mock_openai):
        """Test that the service initializes correctly"""
        service = AgentSearchService()
        assert service.tools is not None
        assert len(service.tools) == 1
        assert service.tools[0].name == "search_youtube"
    
    def test_evaluate_results_satisfied(self, mock_openai):
        """Test evaluation when results are satisfactory"""
        service = AgentSearchService()
        
        # Configure mock response
        eval_response = Mock()
        eval_response.content = '{"satisfied": true, "reason": "Good results", "suggested_queries": []}'
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        result = service.evaluate_results("test query", SAMPLE_RESULTS)
        assert result["satisfied"] is True
        assert "reason" in result
        assert "suggested_queries" in result
        assert len(result["suggested_queries"]) == 0
    
    def test_evaluate_results_unsatisfied(self, mock_openai):
        """Test evaluation when results are unsatisfactory"""
        service = AgentSearchService()
        
        # Configure mock response
        eval_response = Mock()
        eval_response.content = '''
        {
            "satisfied": false,
            "reason": "Results lack variety",
            "suggested_queries": ["query1", "query2", "query3", "query4"]
        }
        '''
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        result = service.evaluate_results("test query", SAMPLE_RESULTS)
        assert result["satisfied"] is False
        assert "reason" in result
        assert len(result["suggested_queries"]) <= 3  # Should be limited to 3 queries
    
    def test_evaluate_results_error_handling(self, mock_openai):
        """Test evaluation error handling"""
        service = AgentSearchService()
        
        # Configure mock to raise an exception
        service.eval_llm.invoke = Mock(side_effect=Exception("Test error"))
        
        result = service.evaluate_results("test query", SAMPLE_RESULTS)
        assert result["satisfied"] is True  # Default to satisfied on error
        assert "Error in evaluation" in result["reason"]
        assert result["suggested_queries"] == []
    
    def test_search_satisfied_with_initial_results(self, mock_apify_service, mock_openai):
        """Test search when satisfied with initial results"""
        service = AgentSearchService()
        
        # Configure evaluation to be satisfied
        eval_response = Mock()
        eval_response.content = '{"satisfied": true, "reason": "Good results", "suggested_queries": []}'
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        results = service.search("test query")
        assert results == SAMPLE_RESULTS
        mock_apify_service.search_youtube_podcasts.assert_called_once()
    
    def test_search_with_alternative_queries(self, mock_apify_service, mock_openai):
        """Test search with alternative queries"""
        service = AgentSearchService()
        
        # Configure evaluation to be unsatisfied
        eval_response = Mock()
        eval_response.content = '''
        {
            "satisfied": false,
            "reason": "Need more variety",
            "suggested_queries": ["query1", "query2"]
        }
        '''
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        # Configure different results for different queries
        alt_results = [
            {'id': '3', 'title': 'New Result 1'},
            {'id': '4', 'title': 'New Result 2'}
        ]
        mock_apify_service.search_youtube_podcasts.side_effect = [
            SAMPLE_RESULTS,  # Initial search
            alt_results,     # First alternative query
            alt_results      # Second alternative query
        ]
        
        results = service.search("test query")
        assert len(results) > 0
        assert mock_apify_service.search_youtube_podcasts.call_count > 1
    
    def test_search_error_handling(self, mock_apify_service, mock_openai):
        """Test search error handling"""
        service = AgentSearchService()
        
        # Configure mock to raise an exception
        mock_apify_service.search_youtube_podcasts.side_effect = Exception("Test error")
        
        results = service.search("test query")
        assert results == []
    
    def test_search_no_initial_results(self, mock_apify_service, mock_openai):
        """Test search when no initial results are found"""
        service = AgentSearchService()
        
        # Configure mock to return empty results
        mock_apify_service.search_youtube_podcasts.return_value = []
        
        results = service.search("test query")
        assert results == []
        assert mock_apify_service.search_youtube_podcasts.call_count == 1
    
    def test_search_duplicate_removal(self, mock_apify_service, mock_openai):
        """Test that duplicate results are removed when using alternative queries"""
        service = AgentSearchService()
        
        # Configure evaluation to be unsatisfied
        eval_response = Mock()
        eval_response.content = '''
        {
            "satisfied": false,
            "reason": "Need more variety",
            "suggested_queries": ["query1", "query2"]
        }
        '''
        service.eval_llm.invoke = Mock(return_value=eval_response)
        
        # Create results with duplicates
        duplicate_results = [
            {'id': '1', 'title': 'Result 1'},
            {'id': '1', 'title': 'Result 1'},  # Duplicate
            {'id': '2', 'title': 'Result 2'}
        ]
        
        mock_apify_service.search_youtube_podcasts.side_effect = [
            SAMPLE_RESULTS,      # Initial search
            duplicate_results,   # Alternative query results
            duplicate_results    # More alternative query results
        ]
        
        results = service.search("test query")
        
        # Check that duplicates were removed
        ids = [r.get('id') for r in results]
        assert len(ids) == len(set(ids))  # No duplicate IDs 