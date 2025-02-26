import streamlit as st
import pandas as pd

def render_analysis_results(results):
    """
    Render analysis results with all details for each post.
    
    Args:
        results (list): List of analysis results
    """
    if not results:
        st.warning("No analysis results available")
        return
    
    st.markdown("### 📊 Analysis Results")
    
    for i, result in enumerate(results):
        with st.expander(f"Post {i+1}: {result.get('post_id', 'Unknown ID')}", expanded=True):
            col1, col2 = st.columns([1, 1])
            
            # Instagram post details
            with col1:
                post_data = result.get('instagram_post', {})
                st.markdown("#### 📱 Instagram Post")
                st.markdown(f"**Username:** {post_data.get('username', 'Unknown')}")
                
                caption = post_data.get('caption', 'No caption')
                st.markdown(f"**Caption:** {caption[:200]}..." if len(caption) > 200 else f"**Caption:** {caption}")
                
                metrics_col1, metrics_col2 = st.columns(2)
                with metrics_col1:
                    st.metric("Likes", post_data.get('likesCount', 0))
                with metrics_col2:
                    st.metric("Comments", post_data.get('commentsCount', 0))
                
                st.markdown(f"**Posted:** {post_data.get('timestamp', 'Unknown date')}")
                
                if post_data.get('url'):
                    st.markdown(f"[View on Instagram]({post_data.get('url')})")
                
                if post_data.get('videoUrl'):
                    st.markdown("#### 🎬 Video")
                    st.markdown(f"[Watch Video]({post_data.get('videoUrl')})")
                    st.video(post_data.get('videoUrl'))
            
            # Analysis results
            with col2:
                st.markdown("#### 🔍 Analysis Results")
                
                # Display podcast information if available
                if result.get('podcast_name'):
                    st.markdown(f"**🎙️ Podcast:** {result.get('podcast_name')}")
                if result.get('episode_title'):
                    st.markdown(f"**📝 Episode:** {result.get('episode_title')}")
                if result.get('podcast_url'):
                    st.markdown(f"[Listen to Podcast]({result.get('podcast_url')})")
                if result.get('youtube_channel'):
                    st.markdown(f"**YouTube Channel:** {result.get('youtube_channel')}")
                
                # Display tabs for different analysis types
                tab_caption, tab_transcript, tab_gemini = st.tabs(["Caption Analysis", "Transcription", "Gemini Analysis"])
                
                with tab_caption:
                    caption_analysis = result.get('caption_analysis', 'No caption analysis available')
                    st.markdown(f"**Caption Analysis:**\n{caption_analysis}")
                
                with tab_transcript:
                    transcript = result.get('transcription_analysis', 'No transcript available')
                    st.markdown(f"**Transcription Analysis:**\n{transcript}")
                
                with tab_gemini:
                    gemini = result.get('gemini_analysis', 'No Gemini analysis available')
                    st.markdown(f"**Gemini Analysis:**\n{gemini}")
            
            # If there's a combined/overall analysis
            if result.get('analysis'):
                st.markdown("#### 📋 Overall Analysis")
                st.markdown(result.get('analysis'))
            
            # YouTube Links Table - add this at the end of each post analysis
            st.markdown("#### 🔗 Podcast YouTube Links")
            youtube_links = result.get('youtube_links', [])
            
            if youtube_links:
                # Create a dataframe from the YouTube links
                df_links = pd.DataFrame(youtube_links)
                
                # Rename columns for better display
                column_mapping = {
                    'title': 'Title',
                    'channel': 'Channel',
                    'channelLink': 'Channel Link',
                    'url': 'Video URL'
                }
                
                # Rename columns if they exist
                df_links = df_links.rename(columns={col: new_col for col, new_col in column_mapping.items() if col in df_links.columns})
                
                # Display as a table with clickable links
                st.dataframe(
                    df_links,
                    column_config={
                        "Title": st.column_config.TextColumn("Title", width="large"),
                        "Channel": st.column_config.TextColumn("Channel Name"),
                        "Channel Link": st.column_config.LinkColumn("Channel Link"),
                        "Video URL": st.column_config.LinkColumn("Video Link")
                    },
                    use_container_width=True
                )
            else:
                st.info("No YouTube links found for this post")
            
            st.markdown("---") 