import streamlit as st
from datetime import datetime
import pandas as pd

def handle_checkbox_change(post_id):
    """
    Handle checkbox state changes for post selection.
    """
    st.session_state.selected_posts[f"selected_{post_id}"] = not st.session_state.selected_posts.get(f"selected_{post_id}", False)

def render_instagram_posts(posts):
    """
    Render Instagram posts with selection checkboxes.
    
    Args:
        posts (list): List of Instagram posts to display
        
    Returns:
        list: List of selected post IDs
    """
    if not posts:
        st.info("No Instagram posts found")
        return []
    
    # Initialize session state for selected posts if not exists
    if 'selected_posts' not in st.session_state:
        st.session_state.selected_posts = {}
    
    # Prepare data for display
    df_data = []
    for post in posts:
        iso_ts = post.get('timestamp', '1970-01-01T00:00:00').replace('Z', '+00:00')
        try:
            formatted_date = datetime.fromisoformat(iso_ts).strftime('%Y-%m-%d %H:%M')
        except Exception:
            formatted_date = "Invalid date"
            
        df_data.append({
            'ID': post['id'],
            'Date': formatted_date,
            'Caption': post.get('caption', 'No caption')[:100] + '...' if post.get('caption') else 'No caption',
            'Likes': post.get('likesCount', 0),
            'Comments': post.get('commentsCount', 0),
            'Video Link': post.get('videoUrl', 'No video')
        })
    
    df = pd.DataFrame(df_data)
    selected = []
    
    st.write("### Instagram Posts")
    
    # Display each post with checkbox and details
    for index, row in df.iterrows():
        checkbox_key = f"selected_{row['ID']}"
        cols = st.columns([0.5, 1.5, 4, 1, 1, 2])
        
        with cols[0]:
            if st.checkbox("Select", key=checkbox_key, 
                         value=st.session_state.selected_posts.get(checkbox_key, False),
                         on_change=handle_checkbox_change,
                         args=(row['ID'],)):
                selected.append(row['ID'])
        
        with cols[1]:
            st.write(row['Date'])
        
        with cols[2]:
            st.markdown(f"**{row['Date']}**")
            st.write(row['Caption'])
        
        with cols[3]:
            st.write(f"👍 {row['Likes']}")
        
        with cols[4]:
            st.write(f"💬 {row['Comments']}")
        
        with cols[5]:
            if row['Video Link'] != 'No video':
                st.markdown(f"[Link]({row['Video Link']})")
            else:
                st.write(row['Video Link'])
    
    if selected:
        st.success(f"Selected {len(selected)} posts for analysis")
    
    return selected 