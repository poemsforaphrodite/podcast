import streamlit as st
import pandas as pd
from datetime import datetime
from supabase import create_client
from apify_client import ApifyClient
from dotenv import load_dotenv
import os
import requests
import time
import json
import tempfile
from openai import OpenAI
import logging

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    filename='logs.txt',
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Define color codes for console output
class LogColors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# Page configuration
st.set_page_config(
    page_title="Podcast Trend Finder",
    page_icon="🎙️",
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

# -------------------------------
# Core Service Clients
# -------------------------------

def get_supabase_client():
    """Initialize Supabase client with error handling."""
    try:
        return create_client(os.getenv("SUPABASE_URL"), os.getenv("SUPABASE_KEY"))
    except Exception as e:
        st.error(f"Supabase connection failed: {str(e)}")
        return None

supabase = get_supabase_client()
apify_client = ApifyClient(os.getenv("APIFY_API_TOKEN"))

# -------------------------------
# Search Functions
# -------------------------------

def search_youtube_podcasts(query, max_results=10):
    """
    Search for YouTube podcasts with enhanced error handling.
    """
    actor_input = {
        "searchQueries": [query],
        "maxResults": max_results,
        "videoType": "video",
        "sortingOrder": "relevance",
        "dateFilter": "month"
    }
    
    try:
        run = apify_client.actor("h7sDV53CddomktSi5").call(run_input=actor_input)
        items = apify_client.dataset(run["defaultDatasetId"]).list_items().items
        
        for item in items:
            if 'url' not in item:
                video_id = item.get('id', '')
                item['url'] = f"https://www.youtube.com/watch?v={video_id}"
        
        return items
    except Exception as e:
        st.error(f"YouTube search failed: {str(e)}")
        return []

def search_instagram_posts(username, max_results=10):
    """
    Search for Instagram posts with enhanced error handling.
    """
    actor_input = {
        "directUrls": [f"https://www.instagram.com/{username}"],
        "resultsType": "stories",
        "resultsLimit": max_results
    }
    
    try:
        st.write(f"Calling Apify for username: {username}")  # Log the API call
        run = apify_client.actor("shu8hvrXbJbY3Eb9W").call(run_input=actor_input)
        return apify_client.dataset(run["defaultDatasetId"]).list_items().items
    except Exception as e:
        st.error(f"Instagram search failed: {str(e)}")
        return []

# -------------------------------
# AI Processing Functions
# -------------------------------

def download_video(url, max_size_mb=50):
    """
    Download video with size limit and error handling.
    """
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        content_length = int(response.headers.get('content-length', 0))
        file_size_mb = content_length / (1024 * 1024)
        
        if file_size_mb > max_size_mb:
            return None, f"Video size ({file_size_mb:.1f}MB) exceeds limit ({max_size_mb}MB)"
        
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as tmp_file:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    tmp_file.write(chunk)
            return tmp_file.name, None
            
    except Exception as e:
        return None, str(e)

def perplexity_search(input_text, prompt_template):
    """
    Call Perplexity API with enhanced error handling and debugging.
    """
    print(input_text)
    api_key = os.getenv("PERPLEXITY_API_KEY")
    
    try:
        if not input_text or not prompt_template:
            return {
                "error": "Missing required input",
                "details": "Both input_text and prompt_template are required"
            }
        
        response = requests.post(
            "https://api.perplexity.ai/chat/completions",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "model": "sonar-pro",
                "messages": [
                    {"role": "system", "content": "Return JSON response"},
                    {"role": "user", "content": prompt_template.format(input_text)}
                ]
            },
            timeout=60
        )
        
        response.raise_for_status()
        
        if not response.text.strip():
            return {
                "error": "Empty API response",
                "details": "The API returned an empty response",
                "status_code": response.status_code
            }
        
        # Return raw response for debugging
        result = response.json()
        print("Raw API Response:", result)
        raw_text = result["choices"][0]["message"]["content"]
        
        # Display the raw response without any processing
        st.markdown("### Raw API Response")
        st.markdown("**Complete API Response:**")
        st.code(str(result), language="json")
        st.markdown("**Message Content:**")
        st.code(raw_text)
        
        # Return the raw text without any parsing
        return {
            "raw_response": raw_text
        }
    
    except requests.exceptions.Timeout:
        return {
            "error": "API timeout",
            "details": "The request to Perplexity API timed out after 60 seconds"
        }
    except requests.exceptions.RequestException as e:
        return {
            "error": "API request failed",
            "details": str(e)
        }
    except Exception as e:
        # Log the raw response if available
        if 'response' in locals():
            error_msg = f"Unexpected error: {str(e)}\nRaw response: {response.text}"
            st.error(error_msg)
            print(error_msg)
        else:
            error_msg = f"Unexpected error: {str(e)}"
            st.error(error_msg)
            print(error_msg)
        return {
            "error": "Unexpected error",
            "details": str(e),
            "raw_response": response.text if 'response' in locals() else None
        }

def transcribe_video_content(video_url):
    """
    Transcribe video content using OpenAI's Whisper API.
    """
    try:
        video_path, error = download_video(video_url)
        if error:
            return f"Error downloading video: {error}"
            
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        with open(video_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                file=audio_file,
                model="whisper-1",
                response_format="text"
            )
            
        os.unlink(video_path)
        return transcript
        
    except Exception as e:
        if 'video_path' in locals() and video_path:
            try:
                os.unlink(video_path)
            except:
                pass
        return f"Transcription failed: {str(e)}"

def gemini_process_video(video_url):
    """
    Process video content using Google's Gemini API.
    """
    try:
        video_path, error = download_video(video_url)
        if error:
            return {"error": f"Error downloading video: {error}"}

        API_KEY = os.getenv("GEMINI_API_KEY")
        BASE_URL = "https://generativelanguage.googleapis.com"
        UPLOAD_ENDPOINT = f"{BASE_URL}/upload/v1beta/files?key={API_KEY}"
        GENERATE_ENDPOINT = f"{BASE_URL}/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

        mime_type = "video/mp4"
        display_name = "Podcast Analysis Video"
        num_bytes = os.path.getsize(video_path)

        headers = {
            "X-Goog-Upload-Protocol": "resumable",
            "X-Goog-Upload-Command": "start",
            "X-Goog-Upload-Header-Content-Length": str(num_bytes),
            "X-Goog-Upload-Header-Content-Type": mime_type,
            "Content-Type": "application/json"
        }
        metadata = {"file": {"display_name": display_name}}

        response = requests.post(UPLOAD_ENDPOINT, headers=headers, json=metadata)
        upload_url = response.headers.get("x-goog-upload-url")
        if not upload_url:
            raise Exception("Failed to initiate upload session")

        with open(video_path, "rb") as f:
            video_data = f.read()

        upload_headers = {
            "Content-Length": str(num_bytes),
            "X-Goog-Upload-Offset": "0",
            "X-Goog-Upload-Command": "upload, finalize"
        }
        upload_response = requests.post(upload_url, headers=upload_headers, data=video_data)
        upload_response.raise_for_status()
        upload_result = upload_response.json()
        file_uri = upload_result["file"]["uri"]

        time.sleep(10)  # Wait for processing

        prompt = """Please analyze this video and return the information in the following JSON format:
        {
            "title": "The title of the YouTube video",
            "channel": "The name of the YouTube channel",
            "channelLink": "The link to the YouTube channel",
            "url": "The direct URL to the YouTube video"
        }
        
        If any field cannot be determined, use an empty string."""

        payload = {
            "contents": [
                {
                    "parts": [
                        {"text": prompt},
                        {"file_data": {"file_uri": file_uri, "mime_type": mime_type}}
                    ]
                }
            ],
            "generation_config": {
                "maxOutputTokens": 1024,
                "temperature": 0.5,
                "topP": 0.8
            }
        }
        generate_headers = {"Content-Type": "application/json"}
        gen_response = requests.post(GENERATE_ENDPOINT, headers=generate_headers, json=payload)
        gen_response.raise_for_status()
        gen_result = gen_response.json()

        analysis_text = (gen_result.get("candidates", [{}])[0]
                                .get("content", {})
                                .get("parts", [{}])[0]
                                .get("text", "No analysis returned"))

        os.unlink(video_path)
        return {"raw_response": analysis_text}

    except Exception as e:
        if 'video_path' in locals() and video_path:
            try:
                os.unlink(video_path)
            except:
                pass
        return {"error": str(e)}

# -------------------------------
# UI Rendering Functions
# -------------------------------

def render_youtube_results(items):
    """
    Render YouTube search results in a dataframe.
    """
    if not items:
        return st.info("No YouTube results found")
    
    df = pd.DataFrame(items)[['title', 'channelName', 'viewCount', 'duration', 'date', 'url']]
    df.columns = ['Title', 'Channel', 'Views', 'Duration', 'Published', 'URL']
    df['Views'] = pd.to_numeric(df['Views'], errors='coerce')
    
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

def handle_checkbox_change(post_id):
    """
    Handle checkbox state changes for post selection.
    """
    st.session_state.selected_posts[f"selected_{post_id}"] = not st.session_state.selected_posts.get(f"selected_{post_id}", False)

def render_instagram_posts(posts):
    """
    Render Instagram posts with selection checkboxes.
    """
    if not posts:
        return st.info("No Instagram posts found"), []
    
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
    
    st.write("### Instagram Posts")
    selected = []
    
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
                st.markdown(f"[Link]({row['Video Link']})")  # Make the link clickable
            else:
                st.write(row['Video Link'])  # Show 'No video' if applicable
    
    if selected:
        st.success(f"Selected {len(selected)} posts for analysis")
    
    return selected

def render_analysis_results(results):
    """
    Render analysis results showing video information in a table format.
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

def call_gpt_formatting(raw_response):
    """
    Call GPT to format the raw response into valid JSON.
    """
    try:
        client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        system_prompt = """You are a JSON formatting assistant. Extract the YouTube video information from the provided response and return it as a JSON object with these fields:
        - title: The title of the YouTube video
        - channel: The name of the YouTube channel
        - channelLink: The link to the YouTube channel
        - url: The direct URL to the YouTube video
        
        Look for this information in the entire response, including any thinking process or analysis. Return only the JSON object."""
        
        user_prompt = f"Here's the complete response. Please extract the video information and return it as JSON:\n{raw_response}"
        
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            response_format={ "type": "json_object" }
        )
        
        # Extract the JSON response
        formatted_response = json.loads(completion.choices[0].message.content)
        
        # Ensure all required fields are present
        required_fields = ['title', 'channel', 'channelLink', 'url']
        for field in required_fields:
            if field not in formatted_response:
                formatted_response[field] = ""
                
        return formatted_response
        
    except Exception as e:
        logging.error(f"Error in GPT formatting: {str(e)}")
        return {
            "title": "",
            "channel": "",
            "channelLink": "",
            "url": "",
            "error": str(e)
        }

def analyze_selected_posts(posts, selected_ids, method):
    """
    Analyze selected posts using the specified method.
    """
    results = []
    progress_bar = st.progress(0)
    processed = 0
    
    for post in posts:
        if post['id'] in selected_ids:
            processed += 1
            
            try:
                if method == "Caption":
                    logging.debug(f"Input text: {post.get('caption', '')}")
                    prompt = """
                    From this Instagram caption: '{}', find the exact YouTube podcast/channel and return the response in JSON format with the following fields: title, channel, channel link, the exact youtube url for the podcast/channel, we want full video of the podcast. 
                    """
                    result = perplexity_search(
                        post.get('caption', ''),
                        prompt
                    )
                    logging.debug(f"Post ID: {post['id']}, Result: {result}")
                    if 'raw_response' in result:
                        # Pass the complete response to GPT for formatting
                        formatted_info = call_gpt_formatting(str(result))
                        results.append({
                            "post_id": post['id'],
                            "raw_response": formatted_info
                        })
                    else:
                        results.append({
                            "post_id": post['id'],
                            "raw_response": {"error": "No valid response"}
                        })
                
                elif method == "Transcription" and post.get('videoUrl'):
                    transcript = transcribe_video_content(post['videoUrl'])
                    prompt = """
                    Given podcast transcription: '{}', find YouTube link/channel and return the response in JSON format with the following fields:
                    - title: The title of the YouTube video
                    - channel: The name of the YouTube channel
                    - channelLink: The link to the YouTube channel
                    - url: The direct URL to the YouTube video
                    
                    If any field cannot be determined, use an empty string.
                    """
                    result = perplexity_search(transcript, prompt)
                    logging.debug(f"Post ID: {post['id']}, Result: {result}")
                    formatted_info = call_gpt_formatting(str(result))
                    results.append({
                        "post_id": post['id'],
                        "raw_response": formatted_info
                    })
                
                elif method == "Gemini" and post.get('videoUrl'):
                    result = gemini_process_video(post['videoUrl'])
                    logging.debug(f"Post ID: {post['id']}, Result: {result}")
                    formatted_info = call_gpt_formatting(str(result))
                    results.append({
                        "post_id": post['id'],
                        "raw_response": formatted_info
                    })
                
            except Exception as e:
                st.error(f"Error processing post {post['id']}: {str(e)}")
                results.append({
                    "post_id": post['id'],
                    "raw_response": {
                        "error": str(e)
                    }
                })
            
            progress_bar.progress(processed / len(selected_ids))
    
    return results

# -------------------------------
# Main Application
# -------------------------------

def main():
    """
    Main application function.
    """
    st.title("🎙️ Podcast Trend Finder")
    
    tab_natural, tab_specific = st.tabs(["Natural Search", "Channel Analysis"])
    
    with tab_natural:
        st.header("Discover Trending Content")
        query = st.text_input("Search terms", placeholder="Enter topic or keywords")
        
        # Add slider for number of results
        max_results = st.slider("Number of results to show", min_value=1, max_value=50, value=10, key="natural_search_slider")
        
        if st.button("Search", type="primary"):
            with st.spinner("Searching YouTube..."):
                results = search_youtube_podcasts(query, max_results)
                render_youtube_results(results)
    
    with tab_specific:
        st.header("Channel-Specific Analysis")
        
        col1, col2 = st.columns([2, 1])
        with col1:
            channel = st.selectbox("Select channel", [
                "neuroglobe",
                "biohackyourselfmedia",
                "longevity2.0"
            ])
        with col2:
            method = st.radio("Analysis method", 
                            ["Caption", "Transcription", "Gemini"], 
                            horizontal=True)
        
        # New input field for Instagram usernames
        instagram_usernames = st.text_input("Enter Instagram usernames (comma-separated)", placeholder="username1, username2")
        
        # Add a slider for the number of posts
        num_posts = st.slider("Number of posts to load", min_value=1, max_value=50, value=10)

        if st.button("Load Posts", type="primary"):
            with st.spinner("Loading Instagram posts..."):
                # Split the input into a list of usernames
                usernames_list = [username.strip() for username in instagram_usernames.split(',') if username.strip()]
                
                # If the input is empty, use the selected channel as the username
                if not usernames_list:
                    usernames_list = [channel]  # Use the selected channel as the username
                
                st.session_state.current_posts = []
                for username in usernames_list:
                    st.write(f"Searching posts for username: {username}")  # Log the username being searched
                    posts = search_instagram_posts(username, num_posts)  # Use the slider value
                    st.write(f"Found {len(posts)} posts for {username}")  # Log the number of posts found
                    st.session_state.current_posts.extend(posts)
                st.session_state.selected_posts = {}  # Reset selections
        
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