import streamlit as st
from src.config.settings import APP_TITLE, APP_ICON, DEFAULT_CHANNELS, ANALYSIS_METHODS
from src.config.logging_config import setup_logging
from src.api.apify_client import apify_service
from src.ui.components.youtube_results import render_youtube_results
from src.ui.components.instagram_posts import render_instagram_posts
from src.ui.components.analysis_results import render_analysis_results
from src.services.analysis_service import analyze_selected_posts

# Setup logging
logger = setup_logging()

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

def main():
    """
    Main application function.
    """
    st.title(f"{APP_ICON} {APP_TITLE}")
    
    tab_natural, tab_specific = st.tabs(["Natural Search", "Channel Analysis"])
    
    with tab_natural:
        st.header("Discover Trending Content")
        query = st.text_input("Search terms", placeholder="Enter topic or keywords")
        
        max_results = st.slider(
            "Number of results to show",
            min_value=1,
            max_value=50,
            value=10,
            key="natural_search_slider"
        )
        
        if st.button("Search", type="primary"):
            with st.spinner("Searching YouTube..."):
                results = apify_service.search_youtube_podcasts(query, max_results)
                render_youtube_results(results)
    
    with tab_specific:
        st.header("Channel-Specific Analysis")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            channel = st.selectbox("Select channel", DEFAULT_CHANNELS)
        with col2:
            method = st.radio("Analysis method", ANALYSIS_METHODS, horizontal=True)
        
        instagram_usernames = st.text_input(
            "Enter Instagram usernames (comma-separated)",
            placeholder="username1, username2"
        )
        
        num_posts = st.slider("Number of posts to load", min_value=1, max_value=50, value=10)

        if st.button("Load Posts", type="primary"):
            with st.spinner("Loading Instagram posts..."):
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
        
        if st.session_state.current_posts:
            selected = render_instagram_posts(st.session_state.current_posts)
            
            if selected:
                if st.button("Analyze Selected Posts", type="primary"):
                    with st.spinner("Analyzing posts..."):
                        st.session_state.analysis_results = analyze_selected_posts(
                            st.session_state.current_posts,
                            selected,
                            method
                        )
                        render_analysis_results(st.session_state.analysis_results)

if __name__ == "__main__":
    main() 