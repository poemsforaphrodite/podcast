import os
from dotenv import load_dotenv
import requests
import json

# Load environment variables from .env file
load_dotenv()

# Get the Perplexity API key
perplexity_api_key = os.getenv('PERPLEXITY_API_KEY')

# Define the API endpoint
api_url = 'https://api.perplexity.ai/chat/completions'

# Function to test the Perplexity Sonar API

def test_perplexity_sonar_api(query):
    headers = {
        'Authorization': f'Bearer {perplexity_api_key}',
        'Content-Type': 'application/json'
    }
    
    data = {
        "model": "sonar-reasoning-pro",
        "messages": [
            {
                "role": "user",
                "content": query
            }
        ]
    }
    
    try:
        response = requests.post(api_url, headers=headers, json=data)
        if response.status_code == 200:
            result = response.json()
            print('API Response:', json.dumps(result, indent=2))
        else:
            print(f'Error: {response.status_code}')
            print('Response:', response.text)
    except Exception as e:
        print('Exception occurred:', str(e))

# Run the test function with a specific query
if __name__ == '__main__':
    test_perplexity_sonar_api('who is the prime minister of india')
