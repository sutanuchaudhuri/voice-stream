# Flask Speech-to-Text Transcription App with Advanced Audio Processing

This is a full-stack Flask web application for real-time and batch speech-to-text transcription and text-to-speech (TTS) using OpenAI's Whisper and TTS APIs. It supports both streaming (real-time) and non-streaming (upload-and-process) modes, with a modern web UI, real-time feedback, advanced audio denoising, and speaker diarization capabilities.

## 🚀 Recent Updates & Improvements (Latest Version)

### ✅ **Progress Bar & User Feedback System - NEW!**
- **ADDED**: Real-time progress indicators for all question submission scenarios
- **FEATURE**: Animated progress bars with contextual messages ("Processing your voice...", "Auto-submitting to AI model...")
- **IMPROVEMENT**: Clear visual feedback eliminates user uncertainty about processing status
- **BENEFIT**: Users always know when their questions are being processed vs when the system is waiting

### ✅ **Smart Auto-Submission Timer - NEW!**
- **INTELLIGENT**: 2-second auto-submission timer triggers after transcription updates
- **CANCELLATION**: Timer automatically cancels if user starts speaking again
- **RESPONSIVE**: No more waiting for long pause intervals - questions submit quickly when ready
- **CONTROL**: Works seamlessly with existing auto-submit toggle for user choice

### ✅ **Configurable Recording Timeout - NEW!**
- **USER CONTROL**: Recording timeout now configurable via UI slider (10 seconds to 5 minutes)
- **FLEXIBLE**: Replace hardcoded limits with user-defined maximum recording duration
- **VISUAL**: Real-time slider value display shows current timeout setting
- **DEFAULT**: Sensible 60-second default with easy adjustment

### ✅ **Audio Denoising Compatibility Fixed**
- **RESOLVED**: Replaced incompatible `demucs` with `noisereduce` library
- **BENEFIT**: Full compatibility with numpy >=2.0 and modern Python environments
- **NEW FEATURE**: Pure Python implementation for better reliability and performance

### ✅ **Speaker Diarization System Upgraded**
- **RESOLVED**: Fixed torchcodec/FFmpeg library loading issues
- **REPLACED**: `pyannote.audio` → `speechbrain` for better compatibility
- **IMPROVED**: More robust speaker identification with fallback mechanisms
- **NO MORE WARNINGS**: Eliminated FFmpeg library path errors

### ✅ **Enhanced Audio Processing Pipeline**
- **ADDED**: `librosa` and `soundfile` for professional audio handling
- **IMPROVED**: Better error handling and graceful degradation
- **OPTIMIZED**: More efficient audio format conversion and processing

### ✅ **Dependency Management Modernized**
- **UPDATED**: All dependencies are now compatible with latest Python versions
- **REMOVED**: Problematic packages that caused version conflicts
- **TESTED**: Full compatibility verified with numpy >=2.2.2

### ✅ **Audio Annotation System & Data Management**
- **NEW**: Complete audio annotation workspace with project management
- **ADDED**: Soft delete functionality for data preservation and audit trails
- **FEATURE**: Multi-project audio annotation with persistent storage
- **IMPROVEMENT**: Audio file path resolution for cross-platform compatibility

---

## Features

### Core Features
- **Voice and Text Input:** Record audio or type your question.
- **Streaming Mode:** Real-time transcription as you speak, with pause detection and auto-stop.
- **Non-Streaming Mode:** Record and manually stop, then process the full audio.
- **Language Selection:** Supports English, Hindi, and Spanish.
- **TTS Playback:** Listen to the answer using OpenAI TTS.
- **Live Timer:** Shows time left before pause triggers auto-stop in streaming mode.
- **Modern UI:** Built with Bootstrap, responsive and user-friendly.

### Audio Annotation System Features
- **📁 Project Management:** Create and manage multiple annotation projects
- **🎙️ Audio Recording:** Record and transcribe audio directly in the browser
- **📝 Transcript Editing:** Edit and update transcriptions manually
- **🗂️ Workspace Organization:** Organized file structure with project-based audio storage
- **🔄 Data Persistence:** Annotations saved to SQLite database with metadata
- **🗑️ Soft Delete:** Non-destructive deletion preserving data for audit and recovery
- **📊 Project Statistics:** Track annotation counts and project progress

### Advanced Audio Features
- **🔇 Audio Denoising:** Remove background noise using advanced AI algorithms
- **👥 Speaker Diarization:** Identify and separate different speakers in conversations
- **🎵 High-Quality Processing:** Professional-grade audio handling with librosa
- **⚡ Real-time Processing:** Optimized for low-latency audio processing

---

## 📸 Audio Annotation System Screenshots

The Audio Annotation System provides a comprehensive interface for managing audio recordings and transcriptions. Here are key screenshots showing the system in action:

### Initial Annotation Grid View
![Audio Annotation Grid View](README-resources/Audio_Annotation_-_in%20grid.png)
*The main annotation grid showing project annotations with audio players, transcripts, and management controls*

### Before Editing Transcripts
![Audio Annotation Before Edit](README-resources/Audio_Annotation_-_BEFORE-EDIT.png)
*Clean annotation display with audio controls and read-only transcript view*

### Alternative Before Edit View
![Audio Annotation Before Edit Alt](README-resources/Audio_Annotation_BEFORE-EDIt.png)
*Another view of the annotation interface in its default state*

### During Transcript Editing
![Audio Annotation On Edit](README-resources/Audio_Annotation_-_ON-EDIT.png)
*Active editing mode showing the transcript editor and save functionality*

### Edit and Save Interface
![Audio Annotation Edit and Save](README-resources/Audio_Annotation_-_EDIT%20and%20save.png)
*Complete edit interface with save and delete options for transcript management*

### Key Interface Features Shown:
- **🎵 Audio Players**: Built-in audio controls for each annotation
- **📝 Editable Transcripts**: Click-to-edit transcript functionality
- **💾 Save Controls**: Individual save buttons for transcript updates
- **🗑️ Delete Options**: Soft delete functionality preserving data integrity
- **📊 Metadata Display**: Creation and update timestamps for each annotation
- **🏷️ Recording Info**: Duration, recording mode, and language indicators

---

## Technical Architecture

### Audio Processing Pipeline
```
Raw Audio (WebM) → FFmpeg Conversion → WAV Format
                                        ↓
                               Optional Denoising (noisereduce)
                                        ↓
                               Speaker Diarization (speechbrain)
                                        ↓
                               OpenAI Whisper Transcription
                                        ↓
                               LangChain + OpenAI Answer Generation
```

### New Library Stack
- **Audio Denoising**: `noisereduce` (numpy >=2.0 compatible)
- **Speaker Recognition**: `speechbrain` (replacing pyannote.audio)
- **Audio Processing**: `librosa` + `soundfile` (professional audio handling)
- **Fallback Support**: Robust error handling with multiple processing paths

---

## Project Structure

```
voice-stream/
│
├── add_ffmpeg_to_path.sh         # Script to add ffmpeg to PATH
├── audio_annotations.db          # SQLite database for annotations (auto-created)
├── INSTALLATION.md               # Installation instructions
├── README.md                     # (This file)
├── requirements.txt              # Python dependencies (UPDATED)
├── run.py                        # App entry point
├── test_env.py                   # Environment test script
├── TROUBLESHOOT.md               # Troubleshooting guide
│
├── annotation_workspaces/        # Project-based audio storage
│   └── project_name/
│       └── audio/                # Audio files for each project
│           ├── audio_timestamp1.wav
│           └── audio_timestamp2.wav
│
├── app/
│   ├── __init__.py               # Flask app initialization
│   ├── routes.py                 # Main backend logic and endpoints (UPDATED)
│   ├── routes_old.py             # (Legacy) Old routes for reference
│   ├── .env                      # Environment variables (OpenAI API key)
│   ├── static/
│   │   └── stream.js             # Main frontend JS (audio, streaming, UI)
│   └── templates/
│       ├── index.html            # Main voice processing UI
│       ├── diarization.html      # Speaker diarization interface
│       └── audio_annotation.html # Audio annotation workspace
│
├── tmpdir_spkrec/                # SpeechBrain model cache
└── uploads/                      # Temporary audio file storage
```

---

## How It Works

### 1. User Interface (index.html + stream.js) - UPDATED
- User selects input mode (voice/text), language, and optionally enables streaming.
- **NEW**: Option to enable noise cancellation for cleaner audio
- **NEW**: Enhanced streaming mode with editable transcription and submission controls

#### Streaming Mode Features:
- **Editable Question Box**: Transcribed text appears in an editable textarea, allowing users to modify the question before submission
- **Auto Submit Option**: Users can choose between automatic and manual submission:
  - **Auto Submit ON**: Questions are automatically sent to LLM after pause detection
  - **Auto Submit OFF**: Users must manually click "Submit Question" button after transcription
- **Real-time Transcription**: Audio chunks are processed in real-time and populate the question box
- **Pause Detection**: Configurable silence detection (0.1-10 seconds) automatically stops recording
- **Manual Control**: Users can edit transcribed text and decide when to submit questions

#### Streaming Workflow:
1. Enable "Use streaming" checkbox
2. Choose Auto Submit behavior (automatic vs manual submission)
3. Set pause detection interval
4. Start recording - real-time transcription populates editable question box
5. On pause detection:
   - **Auto Submit ON**: Question automatically sent to LLM for processing
   - **Auto Submit OFF**: "Submit Question" button appears for manual submission
6. Users can edit transcribed text before submission
7. Answer is generated and displayed with TTS playback option

#### Non-Streaming Mode:
- User can manually stop recording
- The full audio is sent to the backend for transcription after recording ends
- Question box remains read-only until transcription completes
- Automatic submission to LLM for answer generation

### 2. Backend (routes.py) - UPDATED
- `/tts/stream`: Receives audio chunks, converts to wav, **applies denoising**, transcribes with Whisper, returns partial text.
- `/tts`: Receives text, synthesizes speech with OpenAI TTS, streams audio back.
- SocketIO: Handles real-time events for full audio upload and answer generation.
- **NEW**: Advanced audio processing with speaker diarization support
- **NEW**: Intelligent fallback mechanisms for robust processing
- Manages file conversion, cleanup, and error handling.

### 3. Audio Processing Features

#### Noise Cancellation
```python
# Using noisereduce for audio denoising
audio_data, sample_rate = librosa.load(wav_filename, sr=None)
reduced_noise = nr.reduce_noise(y=audio_data, sr=sample_rate)
sf.write(denoised_wav_filename, reduced_noise, sample_rate)
```

#### Speaker Diarization
```python
# Using speechbrain (modern API) for speaker recognition
from speechbrain.inference import SpeakerRecognition

verification = SpeakerRecognition.from_hparams(
    source="speechbrain/spkrec-ecapa-voxceleb", 
    savedir="tmpdir_spkrec"
)
# Process audio segments and identify speakers
```

---

## Installation & Setup

### Prerequisites
- Python 3.8+ (tested with Python 3.13)
- FFmpeg (for audio conversion)
- OpenAI API key

### 1. Install System Dependencies

#### macOS
```bash
brew install ffmpeg
```

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### Windows
- Download from https://ffmpeg.org/download.html
- Add the ffmpeg `bin` directory to your system PATH.

### 2. Install Python Dependencies
```bash
# Clone the repository
git clone https://github.com/sutanuchaudhuri/voice-stream
cd voice-stream

# Create virtual environment (recommended)
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

### 3. Environment Configuration

**IMPORTANT**: You must configure your OpenAI API key before running the application.

#### Option 1: Create .env File (Recommended)
Create a `.env` file in the `app/` directory:
```bash
# app/.env
OPENAI_API_KEY=your_openai_api_key_here
VOICE_UPLOAD_PERSIST=no  # Optional: Set to 'yes' to keep audio files
DIARIZATION_SEGMENT_LENGTH=10  # Optional: Default segment length (seconds)
MAX_SPEAKERS=10  # Optional: Maximum number of speakers to detect
ENABLE_SPEAKER_CLUSTERING=yes  # Optional: Enable advanced speaker clustering
```

#### Option 2: System Environment Variable
Alternatively, set the API key as a system environment variable:

**macOS/Linux:**
```bash
# Add to ~/.bashrc, ~/.zshrc, or ~/.profile
export OPENAI_API_KEY="your_openai_api_key_here"

# Or set for current session only
export OPENAI_API_KEY="your_openai_api_key_here"
python run.py
```

**Windows:**
```cmd
# Command Prompt
set OPENAI_API_KEY=your_openai_api_key_here
python run.py

# PowerShell
$env:OPENAI_API_KEY="your_openai_api_key_here"
python run.py

# Or add permanently via System Properties > Environment Variables
```

#### How the Application Reads the API Key

The application uses the following code to load the OpenAI API key:

```python
# In app/routes.py
from dotenv import load_dotenv, find_dotenv
import os

# Load environment variables from .env file
load_dotenv(find_dotenv())

# Get API key from environment (works with both .env file and system env vars)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

if not OPENAI_API_KEY:
    raise ValueError(
        "OpenAI API key not found! Please either:\n"
        "1. Create app/.env file with OPENAI_API_KEY=your_key_here\n"
        "2. Set OPENAI_API_KEY environment variable\n"
        "3. Get your API key from https://platform.openai.com/api-keys"
    )
```

#### Getting Your OpenAI API Key

1. Visit [OpenAI Platform](https://platform.openai.com/api-keys)
2. Sign in to your OpenAI account (create one if needed)
3. Click "Create new secret key"
4. Copy the key (starts with `sk-proj-` or `sk-`)
5. Add it to your `.env` file or environment variables

**Security Note**: 
- Never commit your `.env` file to version control
- The `.env` file is already in `.gitignore` to prevent accidental commits
- Keep your API key secure and don't share it publicly

#### Verifying Your Setup

Test your API key configuration:
```bash
# Quick test to verify API key is loaded correctly
python -c "
from dotenv import load_dotenv, find_dotenv
import os
load_dotenv(find_dotenv())
key = os.getenv('OPENAI_API_KEY')
if key:
    print(f'✅ API key loaded: {key[:20]}...')
else:
    print('❌ API key not found!')
"
```
````
