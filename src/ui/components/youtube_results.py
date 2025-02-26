import streamlit as st
import pandas as pd

def render_youtube_results(items):
    """
    Render YouTube search results in a dataframe.
    
    Args:
        items (list): List of YouTube video items to display
    """
    if not items:
        return st.info("No YouTube results found")
    
    # Create DataFrame with selected columns
    df = pd.DataFrame(items)[['title', 'channelName', 'viewCount', 'duration', 'date', 'url']]
    df.columns = ['Title', 'Channel', 'Views', 'Duration', 'Published', 'URL']
    
    # Convert views to numeric for sorting
    df['Views'] = pd.to_numeric(df['Views'], errors='coerce')
    
    # Display the dataframe with custom column configurations
    st.dataframe(
        df.sort_values('Views', ascending=False),
        column_config={
            "Title": st.column_config.TextColumn(width="large"),
            "Channel": st.column_config.TextColumn("Channel"),
            "Views": st.column_config.NumberColumn(format="%d"),
            "URL": st.column_config.LinkColumn("Video Link")
        },
        height=600,
        use_container_width=True
    ) 