# Podcast Trend Finder - Project Structure

## Overview
This document provides a detailed explanation of each component in the project structure.

## Root Directory
```
podcast/
├── .env                 # Active environment variables
├── .env.example         # Template for environment variables
├── requirements.txt     # Python package dependencies
├── setup.py            # Package installation configuration
├── pyproject.toml      # Project metadata and build configuration
├── run.py              # Streamlit run script with Python path setup
├── README.md           # Project documentation and setup instructions
└── STRUCTURE.md        # This file - detailed project structure
```

## Source Code (`src/`)

### Main Application
```
src/
├── __init__.py        # Package initialization and version info
└── main.py            # Entry point of the application
                      # - Configures Streamlit interface
                      # - Sets up session state
                      # - Implements main UI tabs
                      # - Coordinates between components
```

### Configuration (`src/config/`)
```
src/config/
├── __init__.py        # Package exports
├── settings.py        # Central configuration file
                      # - Environment variables
                      # - Application constants
                      # - API configurations
                      # - Default values
└── logging_config.py  # Logging configuration
                      # - Log file setup
                      # - Console output formatting
                      # - Color coding for logs
```

### API Clients (`src/api/`)
```
src/api/
├── __init__.py        # Package exports
├── supabase_client.py # Supabase database client
                      # - Database connection
                      # - Error handling
├── apify_client.py    # Apify integration
                      # - YouTube search functionality
                      # - Instagram post retrieval
                      # - Result processing
├── perplexity_api.py # Perplexity API integration
                      # - Natural language processing
                      # - Content analysis
├── openai_client.py   # OpenAI/Whisper integration
                      # - Video transcription
                      # - GPT processing
└── gemini_client.py   # Google Gemini integration
                      # - Video content analysis
```

### Services (`src/services/`)
```
src/services/
├── __init__.py        # Package exports
├── video_service.py   # Video processing service
                      # - Video downloading
                      # - Size validation
                      # - Error handling
└── analysis_service.py # Content analysis
                      # - Caption analysis
                      # - Transcription processing
                      # - AI-powered analysis
```

### UI Components (`src/ui/`)
```
src/ui/
├── __init__.py
└── components/
    ├── __init__.py
    ├── youtube_results.py  # YouTube results display
    │                      # - Data formatting
    │                      # - Interactive table
    ├── instagram_posts.py  # Instagram posts display
    │                      # - Post rendering
    │                      # - Selection interface
    └── analysis_results.py # Analysis results display
                          # - JSON formatting
                          # - Table rendering
```

## Tests (`tests/`)
```
tests/
├── __init__.py
├── conftest.py           # Test configuration and fixtures
├── api/                  # API client tests
│   ├── __init__.py
│   ├── test_apify_client.py
│   └── test_openai_client.py
└── services/            # Service tests
    ├── __init__.py
    ├── test_video_service.py
    └── test_analysis_service.py
```

## Key Features and Functionality

### 1. Natural Search
- YouTube podcast search using keywords
- Results sorting and filtering
- Interactive results display

### 2. Channel Analysis
- Instagram post retrieval
- Multiple analysis methods:
  - Caption-based analysis
  - Video transcription
  - AI-powered content analysis
- Cross-platform content linking

### 3. Data Processing
- Video download and processing
- Content transcription
- AI-powered analysis
- Result aggregation and formatting

### 4. User Interface
- Clean, intuitive design
- Interactive components
- Real-time feedback
- Progress indicators

### 5. Error Handling
- Comprehensive logging
- User-friendly error messages
- Graceful failure handling
- Debug information

### 6. Testing
- Comprehensive test suite
- Mock fixtures and utilities
- API client testing
- Service layer testing

### 7. Project Configuration
- Environment variables management
- Dependency management
- Build configuration
- Development tools setup

## Development Guidelines

1. **Code Organization**
   - Keep related functionality together
   - Use appropriate abstraction levels
   - Follow single responsibility principle

2. **Error Handling**
   - Log all errors appropriately
   - Provide user-friendly error messages
   - Implement proper error recovery

3. **Testing**
   - Write unit tests for all components
   - Use fixtures for common test data
   - Test edge cases and error conditions
   - Implement integration tests

4. **Documentation**
   - Keep inline documentation updated
   - Document API changes
   - Update README for new features
   - Maintain STRUCTURE.md