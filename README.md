# Journal LLM

A Python tool that automatically transcribes and summarizes video content, with optional Notion integration for knowledge management.

## Features

- **Multi-source video support**: Process YouTube videos, local files, or remote URLs
- **Automatic transcription**: High-quality audio-to-text using OpenAI Whisper
- **AI summarization**: Generate structured summaries with Google Gemini
- **Notion integration**: Optionally save summaries to your Notion knowledge base
- **Smart file management**: Auto-cleanup of temporary files after processing
- **Progress tracking**: Visual feedback with spinners and detailed logging

## Quick Start

### Prerequisites

- Python 3.8 or higher
- FFmpeg installed on your system ([Download FFmpeg](https://ffmpeg.org/download.html))
- Google Gemini API key ([Get API Key](https://makersuite.google.com/app/apikey))
- (Optional) Notion API key and database ID for Notion integration

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/journal-llm.git
cd journal-llm

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Linux/Mac
# venv\Scripts\activate  # On Windows

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy the environment template:
   ```bash
   cp .env.example .env
   ```

2. Edit `.env` and add your API keys:
   ```env
   # Required for AI summarization
   GEMINI_API_KEY=your_gemini_api_key_here
   
   # Optional: Notion integration
   NOTION_API_KEY=your_notion_api_key_here
   NOTION_DATABASE_ID=your_notion_database_id_here
   
   # Optional: Auto-cleanup downloaded files (1 = yes, 0 = no)
   DELETE_UNNEEDED_FILES=1
   ```

### Usage

```bash
# Process a YouTube video
python main.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"

# Process a local video file
python main.py --local "/path/to/video.mp4"

# Process a remote video URL
python main.py --url "https://example.com/video.mp4"

# Force reprocessing (skip cache)
python main.py --youtube "URL" --force

# Verbose output for debugging
python main.py --youtube "URL" --verbose
```

## How It Works

1. **Video Input**: Accepts YouTube URLs, local files, or remote video URLs
2. **Audio Extraction**: Uses FFmpeg to extract audio track from video
3. **Transcription**: OpenAI Whisper converts audio to text locally
4. **Summarization**: Google Gemini generates structured summary
5. **Output**: Displays in console or saves to Notion database

## Output Example

![Diagram](imgs/diagram.png)

The tool generates structured summaries including:
- **Title**: Auto-generated descriptive title
- **Summary**: Comprehensive overview of the content
- **Key Points**: Bullet-point list of main topics
- **Action Items**: Actionable takeaways and next steps
- **Metadata**: Video duration, processing time, source URL

## Project Structure

```
journal-llm/
├── main.py             # Simple entry point wrapper
├── cli.py              # Main CLI application with argument parsing
├── src/
│   └── modules/
│       ├── AI/
│       │   └── main.py      # Transcription (Whisper) and summarization (Gemini)
│       ├── videos/
│       │   └── main.py      # Video downloading and audio extraction
│       ├── notion/
│       │   └── main.py      # Notion database integration
│       ├── config.py        # Configuration management
│       ├── formatters.py    # Output formatting utilities
│       ├── exceptions.py    # Custom exception classes
│       └── logger.py        # Centralized logging setup
├── downloads/          # Temporary video storage (auto-created)
├── audio/              # Extracted audio files (auto-created)
├── .env.example        # Environment variables template
├── .env                # Your API keys (create from .env.example)
└── requirements.txt    # Python dependencies
```

## License

This project is part of a series of weekend projects - built for learning and experimentation.

Copyright 2025 ej-east

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
