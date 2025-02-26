import streamlit as st
import pandas as pd

def render_analysis_results(results):
    """
    Render analysis results showing video information in a table format.
    
    Args:
        results (list): List of analysis results to display
    """
    st.subheader("Analysis Results")
    
    # Prepare data for the DataFrame
    data = []
    for result in results:
        if 'raw_response' in result:
            # Show the cleaned JSON for each result
            st.markdown(f"### Post ID: {result['post_id']}")
            st.markdown("**Cleaned JSON Response:**")
            st.json(result['raw_response'])
            st.markdown("---")
            
            # Extract data for the table
            raw_response = result['raw_response']
            if isinstance(raw_response, dict):
                row_data = {
                    "Post ID": result['post_id'],
                    "Title": raw_response.get('title', ''),
                    "Channel": raw_response.get('channel', ''),
                    "Channel Link": raw_response.get('channelLink', ''),
                    "URL": raw_response.get('url', '')
                }
                data.append(row_data)
    
    if data:
        # Create a DataFrame
        df = pd.DataFrame(data)
        
        # Display the DataFrame with clickable links
        st.markdown("### Analysis Table")
        st.dataframe(
            df,
            column_config={
                "URL": st.column_config.LinkColumn("YouTube Link"),
                "Channel Link": st.column_config.LinkColumn("Channel Link"),
                "Title": st.column_config.TextColumn("Video Title", width="large"),
                "Channel": st.column_config.TextColumn("Channel Name", width="medium"),
                "Post ID": st.column_config.TextColumn("Post ID", width="small")
            },
            hide_index=True
        )
    else:
        st.info("No analysis results available.") 