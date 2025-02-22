import os
import requests
import time

# Set up configuration and API endpoints
API_KEY = "AIzaSyAiMOlsAZ5W0CU4iC6RAQfeQNUDKH4Z_6w"
BASE_URL = "https://generativelanguage.googleapis.com"
UPLOAD_ENDPOINT = f"{BASE_URL}/upload/v1beta/files?key={API_KEY}"
GENERATE_ENDPOINT = f"{BASE_URL}/v1beta/models/gemini-1.5-flash:generateContent?key={API_KEY}"

# Video file settings
video_path = "video.mp4"
mime_type = "video/mp4"
display_name = "My Video for Summarization"
num_bytes = os.path.getsize(video_path)

# === Step 1: Start the resumable upload session ===
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
    raise Exception("Failed to initiate upload session. Response: " + response.text)
print("Upload session started. URL:", upload_url)

# === Step 2: Upload the video bytes ===
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
print("Uploaded video URI:", file_uri)

# === Optional: Wait for video processing (if necessary) ===
# Depending on the file size and processing time, you may need to poll for status.
# For simplicity, we pause for 10 seconds.
print("Waiting for video processing...")
time.sleep(10)

# === Step 3: Call generateContent to summarize the video ===
prompt = "Can you tell who is the person in this video?"
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

# Extract the summary text from the response
summary_text = (gen_result.get("candidates", [{}])[0]
                          .get("content", {})
                          .get("parts", [{}])[0]
                          .get("text", "No summary returned"))
print("\nVideo Summary:\n", summary_text)
