# Flask Speech-to-Text Transcription App

This is a simple Flask web application that allows users to upload audio files and transcribe them using OpenAI's Whisper API.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenAI API key as an environment variable:
   ```bash
   export OPENAI_API_KEY=your_openai_api_key
   ```
3. Run the app:
   ```bash
   python run.py
   ```

## Usage
- Open your browser and go to `http://127.0.0.1:5000/`
- Upload an audio file and get the transcription result.
