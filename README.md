# Journal LLM

A Python tool that automatically transcribes and summarizes video content, with optional Notion integration for knowledge management.

## Features

- Download videos from YouTube URLs or process local video files
- Automatic audio extraction and transcription using OpenAI Whisper
- AI-powered summarization with Google Gemini
- Optional Notion database integration for organizing summaries
- CLI interface for easy usage

## Quick Start

### Installation

```bash
# Clone the repository
git clone https://github.com/yourusername/journal-llm.git
cd journal-llm

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # On Windows
# source venv/bin/activate  # On Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### Configuration

1. Copy `.env.example` to `.env`
2. Add your API keys:
   - `GEMINI_API_KEY` - Required for AI summarization
   - `NOTION_API_KEY` - Optional for Notion integration
   - `NOTION_DATABASE_ID` - Optional for Notion integration

### Usage

```bash
# Process a YouTube video
python main.py --youtube "https://www.youtube.com/watch?v=VIDEO_ID"

# Process a local video file
python main.py --local "/path/to/video.mp4"
```

## Output Example

![Diagram](imgs/diagram.png)

The tool generates structured summaries including:
- **Title**: Concise content title
- **Summary**: Brief overview of the content
- **Key Points**: Main topics discussed
- **Action Items**: Tasks or next steps identified

## Requirements

- Python 3.8+
- FFmpeg (for audio extraction)
- API keys for Gemini and optionally Notion

## License

This project is part of a series of weekend projects - built for learning and experimentation.

Copyright 2025 ej-east

Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
