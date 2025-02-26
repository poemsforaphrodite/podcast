 # 🎙️ Podcast Trend Finder

A Streamlit application that helps discover and analyze trending podcast content across YouTube and Instagram.

## Features

- **Natural Search**: Search for podcasts on YouTube using keywords
- **Channel Analysis**: Analyze specific podcast channels' Instagram posts
- **Multiple Analysis Methods**:
  - Caption Analysis
  - Video Transcription
  - Gemini AI Analysis
- **Cross-Platform Integration**: Connect Instagram posts with YouTube content

## Installation

1. Clone the repository:
```bash
git clone https://github.com/yourusername/podcast-trend-finder.git
cd podcast-trend-finder
```

2. Create a virtual environment and activate it:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
- Copy `.env.example` to `.env`
- Fill in your API keys and credentials

## Required API Keys

- Supabase URL and Key
- Apify API Token
- OpenAI API Key
- Perplexity API Key
- Google Gemini API Key

## Usage

1. Start the Streamlit application:
```bash
streamlit run src/main.py
```

2. Open your browser and navigate to `http://localhost:8501`

## Project Structure

```
podcast/
├── src/
│   ├── api/          # External API clients
│   ├── config/       # Configuration files
│   ├── services/     # Business logic
│   └── ui/           # Streamlit UI components
├── tests/            # Test files
├── .env              # Environment variables
└── requirements.txt  # Python dependencies
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.