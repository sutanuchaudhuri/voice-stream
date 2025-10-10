# Flask Speech-to-Text Transcription App

This is a full-stack Flask web application for real-time and batch speech-to-text transcription and text-to-speech (TTS) using OpenAI's Whisper and TTS APIs. It supports both streaming (real-time) and non-streaming (upload-and-process) modes, with a modern web UI and real-time feedback.

---

## Features
- **Voice and Text Input:** Record audio or type your question.
- **Streaming Mode:** Real-time transcription as you speak, with pause detection and auto-stop.
- **Non-Streaming Mode:** Record and manually stop, then process the full audio.
- **Language Selection:** Supports English, Hindi, and Spanish.
- **TTS Playback:** Listen to the answer using OpenAI TTS.
- **Live Timer:** Shows time left before pause triggers auto-stop in streaming mode.
- **Modern UI:** Built with Bootstrap, responsive and user-friendly.

---

## Project Structure

```
voice-stream/
│
├── add_ffmpeg_to_path.sh         # Script to add ffmpeg to PATH
├── INSTALLATION.md               # Installation instructions
├── README.md                     # (This file)
├── requirements.txt              # Python dependencies
├── run.py                        # App entry point
├── test_env.py                   # Environment test script
│
├── app/
│   ├── __init__.py               # Flask app initialization
│   ├── routes.py                 # Main backend logic and endpoints
│   ├── routes_old.py             # (Legacy) Old routes for reference
│   ├── static/
│   │   └── stream.js             # Main frontend JS (audio, streaming, UI)
│   └── templates/
│       └── index.html            # Main frontend UI (Bootstrap)
│
└── uploads/                      # Temporary audio file storage
```

---

## How It Works

### 1. User Interface (index.html + stream.js)
- User selects input mode (voice/text), language, and optionally enables streaming.
- If streaming is enabled:
  - User sets pause detection interval.
  - On "Start Recording", audio is captured and sent in real time to `/tts/stream`.
  - Silence detection auto-stops recording after the specified interval.
  - Partial transcriptions are shown live.
- If streaming is not enabled:
  - User can manually stop recording.
  - The full audio is sent to the backend for transcription after recording ends.
- The transcribed question is sent to the backend, which generates an answer using OpenAI.
- The answer is displayed, and TTS audio can be played.

### 2. Backend (routes.py)
- `/tts/stream`: Receives audio chunks, converts to wav, transcribes with Whisper, returns partial text.
- `/tts`: Receives text, synthesizes speech with OpenAI TTS, streams audio back.
- SocketIO: Handles real-time events for full audio upload and answer generation.
- Manages file conversion, cleanup, and error handling.

---

## Conceptual Diagram

```
+-------------------+         HTTP/SocketIO         +-------------------+
|    Browser (UI)   | <---------------------------> |     Flask App     |
|  index.html,      |                               |   (routes.py)     |
|  stream.js        |                               |                   |
+-------------------+                               +-------------------+
        |                                                    |
        | 1. User clicks "Start Recording"                   |
        |--------------------------------------------------->|
        |                                                    |
        | 2. Audio captured (MediaRecorder)                  |
        |                                                    |
        | 3a. [Streaming]                                    |
        |    - Chunks sent to /tts/stream (POST)             |
        |    - Partial text returned (JSON)                  |
        |<-------------------------------------------------->| 
        |                                                    |
        | 3b. [Non-Streaming]                                |
        |    - Full audio sent via SocketIO                  |
        |    - Transcription result via SocketIO             |
        |<-------------------------------------------------->| 
        |                                                    |
        | 4. Display question, get answer from OpenAI        |
        |    - Answer returned via SocketIO                  |
        |<---------------------------------------------------|
        |                                                    |
        | 5. User clicks "🔊" for TTS                        |
        |    - /tts endpoint returns audio                   |
        |<-------------------------------------------------->| 
        |                                                    |
        | 6. Audio playback in browser                       |
        |                                                    |
+-------------------+                               +-------------------+
```

---

## File-by-File Explanation

### Top-Level Files
- **add_ffmpeg_to_path.sh**: Shell script to add ffmpeg to your system path, required for audio format conversion.
- **INSTALLATION.md**: Instructions for installing dependencies and setting up the environment.
- **README.md**: Project overview, setup, and usage instructions.
- **requirements.txt**: Python dependencies (Flask, Flask-SocketIO, requests, python-dotenv, etc.).
- **run.py**: Entry point for running the Flask app. Typically imports the app and starts the server.
- **test_env.py**: Likely a script to test the environment or dependencies.

### The `app/` Directory
- **__init__.py**: Initializes the Flask app and (optionally) Flask-SocketIO. Loads configuration and environment variables.
- **routes.py**: Main backend logic. Defines Flask routes and SocketIO event handlers. Handles audio file conversion, transcription, TTS, and file cleanup.
- **routes_old.py**: Presumably an older version of the routes, kept for reference or backup.

### The `app/static/` Directory
- **stream.js**: Main frontend JavaScript. Handles audio recording, streaming, silence detection, UI updates, and SocketIO communication.

### The `app/templates/` Directory
- **index.html**: Main frontend UI. Bootstrap-based layout. Controls for input mode, language, recording, streaming, pause detection, and TTS playback.

### The `uploads/` Directory
- Temporary storage for uploaded/converted audio files during processing.

---

## How Pause Detection Works

- In streaming mode, the app uses the Web Audio API to monitor the audio signal in real time.
- When the RMS (root mean square) value of the audio falls below a threshold, it is considered silence.
- The user can set the pause detection interval (in seconds) in the UI.
- If silence is detected for longer than this interval, recording automatically stops and the last chunk is processed.
- A live timer in the UI shows how much time is left before auto-stop triggers.
- In non-streaming mode, pause detection is not used; the user must manually stop recording.

---

## FFmpeg Installation

FFmpeg is required for audio format conversion (webm to wav) before transcription. You must have ffmpeg installed and available in your system PATH.

### macOS
```bash
brew install ffmpeg
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

### Windows
- Download from https://ffmpeg.org/download.html
- Add the ffmpeg `bin` directory to your system PATH.

You can use the provided `add_ffmpeg_to_path.sh` script to help set up ffmpeg on Unix-like systems.

---

## Python Libraries Used

- **Flask**: Web framework for the backend.
- **Flask-SocketIO**: Real-time communication between browser and server.
- **requests**: For making HTTP requests to OpenAI APIs.
- **python-dotenv**: Loads environment variables from a `.env` file.
- **OpenAI**: For Whisper (ASR) and TTS APIs.
- **Bootstrap**: For responsive frontend UI (via CDN).

All Python dependencies are listed in `requirements.txt`.

---

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

---

## Usage
- Open your browser and go to `http://127.0.0.1:5000/`
- Select input mode (voice or text), language, and optionally enable streaming.
- If streaming, set the pause detection interval and start recording. The app will transcribe in real time and auto-stop on pause.
- If not streaming, start and manually stop recording. The app will transcribe after you stop.
- View the question and answer, and click the speaker icon to listen to the answer.

---

## Extensibility
- Add more languages, change the TTS/ASR provider, or enhance the UI for more features.
- The modular structure (separate static, templates, and backend logic) makes it easy to maintain and extend.

---

## License
MIT License
