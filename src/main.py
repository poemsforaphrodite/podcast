import streamlit as st
from src.config.settings import APP_TITLE, APP_ICON, DEFAULT_CHANNELS, ANALYSIS_METHODS
from src.config.logging_config import setup_logging
from src.api.apify_client import apify_service
from src.services.natural_agent_service import NaturalAgentService
from src.services.specific_agent_service import SpecificAgentService
from src.ui.components.youtube_results import render_youtube_results
from src.ui.components.instagram_posts import render_instagram_posts
from src.ui.components.analysis_results import render_analysis_results
from src.services.analysis_service import analyze_selected_posts

# Setup logging
logger = setup_logging()

# Initialize agent services
natural_agent = NaturalAgentService()
specific_agent = SpecificAgentService()

# Page configuration
st.set_page_config(
    page_title=APP_TITLE,
    page_icon=APP_ICON,
    layout="wide"
)

# Initialize session states
if 'selected_posts' not in st.session_state:
    st.session_state.selected_posts = {}
if 'current_posts' not in st.session_state:
    st.session_state.current_posts = []
if 'analysis_results' not in st.session_state:
    st.session_state.analysis_results = []
if 'analyze_clicked' not in st.session_state:
    st.session_state.analyze_clicked = False
if 'search_evaluation' not in st.session_state:
    st.session_state.search_evaluation = None
if 'channel_evaluation' not in st.session_state:
    st.session_state.channel_evaluation = None

def main():
    """
    Main application function.
    """
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    tab_natural, tab_specific = st.tabs(["Natural Search", "Channel Analysis"])
    
    with tab_natural:
        st.header("Discover Trending Content")
        query = st.text_input("Search terms", placeholder="Enter topic or keywords")
        
        col1, col2 = st.columns([1, 2])
        with col1:
            search_type = st.radio(
                "Search Type",
                ["Non-Agentic", "Agentic"],
                help="Agentic search uses AI to refine search queries for better results"
            )
        
        with col2:
            max_results = st.slider(
                "Number of results to show",
                min_value=1,
                max_value=50,
                value=10,
                key="natural_search_slider"
            )
        
        if st.button("Search", type="primary"):
            with st.spinner("Searching YouTube..."):
                if search_type == "Non-Agentic":
                    results = apify_service.search_youtube_podcasts(query, max_results)
                    st.session_state.search_evaluation = None
                else:
                    st.info("Using AI agent to find the most relevant podcasts...")
                    results = []
                    evaluation = None
                    
                    # First search
                    initial_results = apify_service.search_youtube_podcasts(query, max_results)
                    if initial_results:
                        evaluation = natural_agent.evaluate_results(query, initial_results)
                        
                        if evaluation["satisfied"]:
                            results = initial_results
                            st.success("🎯 AI is satisfied with the initial search results!")
                        else:
                            st.warning("🔄 Initial results weren't ideal. Trying alternative queries...")
                            results = natural_agent.search(query, max_results)
                    
                    st.session_state.search_evaluation = evaluation
                
                # Show evaluation details if available
                if st.session_state.search_evaluation:
                    with st.expander("Search Evaluation Details", expanded=True):
                        st.markdown("### AI Evaluation")
                        st.markdown(f"**Status**: {'✅ Satisfied' if st.session_state.search_evaluation['satisfied'] else '🔄 Required Refinement'}")
                        st.markdown(f"**Reason**: {st.session_state.search_evaluation['reason']}")
                        if st.session_state.search_evaluation['suggested_queries']:
                            st.markdown("**Alternative Queries Tried:**")
                            for query in st.session_state.search_evaluation['suggested_queries']:
                                st.markdown(f"- {query}")
                
                render_youtube_results(results)
    
    with tab_specific:
        st.header("Channel-Specific Analysis")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            channel = st.selectbox("Select channel", DEFAULT_CHANNELS)
            instagram_usernames = st.text_input(
                "Enter Instagram usernames (comma-separated)",
                placeholder="username1, username2"
            )
        with col2:
            search_type = st.radio(
                "Analysis Type",
                ["Non-Agentic", "Agentic"],
                help="Agentic analysis uses AI to find the best content and suggest related accounts"
            )
            method = st.radio("Analysis method", ANALYSIS_METHODS, horizontal=True)
        
        num_posts = st.slider("Number of posts to load", min_value=1, max_value=50, value=10)

        if st.button("Load Posts", type="primary"):
            with st.spinner("Loading Instagram posts..."):
                if search_type == "Non-Agentic":
                    usernames_list = [username.strip() for username in instagram_usernames.split(',') if username.strip()]
                    if not usernames_list:
                        usernames_list = [channel]
                    
                    st.session_state.current_posts = []
                    for username in usernames_list:
                        st.write(f"Searching posts for username: {username}")
                        posts = apify_service.search_instagram_posts(username, num_posts)
                        st.write(f"Found {len(posts)} posts for {username}")
                        st.session_state.current_posts.extend(posts)
                    st.session_state.selected_posts = {}
                    st.session_state.channel_evaluation = None
                else:
                    st.info("Using AI agent to find the most relevant posts...")
                    username = instagram_usernames.strip() or channel
                    
                    # Use the channel agent
                    all_posts, analysis_results, evaluation = specific_agent.analyze_channel(username, num_posts)
                    
                    if evaluation:
                        st.session_state.current_posts = all_posts
                        st.session_state.analysis_results = analysis_results
                        st.session_state.channel_evaluation = evaluation
                        
                        if evaluation["satisfied"]:
                            st.success("🎯 AI found relevant podcast content!")
                        else:
                            st.warning("🔄 Looking for more posts from this account...")
                            
                        # Show evaluation details
                        with st.expander("Analysis Evaluation Details", expanded=True):
                            st.markdown("### AI Evaluation")
                            st.markdown(f"**Status**: {'✅ Satisfied' if evaluation['satisfied'] else '🔄 Required Refinement'}")
                            st.markdown(f"**Reason**: {evaluation['reason']}")
                            if evaluation['selected_posts']:
                                st.markdown(f"**Selected {len(evaluation['selected_posts'])} relevant posts for analysis**")
                    else:
                        st.error("No posts found or error in analysis")
                        st.session_state.current_posts = []
                        st.session_state.channel_evaluation = None
        
        if st.session_state.current_posts:
            if search_type == "Non-Agentic":
                selected = render_instagram_posts(st.session_state.current_posts)
                
                if selected:
                    if st.button("Analyze Selected Posts", type="primary"):
                        with st.spinner("Analyzing posts..."):
                            st.session_state.analysis_results = analyze_selected_posts(
                                st.session_state.current_posts,
                                selected,
                                method
                            )
            
            if st.session_state.analysis_results:
                render_analysis_results(st.session_state.analysis_results)

if __name__ == "__main__":
    main() 