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

### 🗄️ Dual Database Architecture

The application supports **dual database modes** for flexible deployment across different environments:

#### Database Modes
- **SQLite Mode (Default)**: Perfect for development, small deployments, and local testing
- **DynamoDB Mode**: Scalable cloud database for production AWS deployments

#### Database Configuration
```bash
# SQLite Configuration (Default)
DATABASE_MODE=sqlite
SQLITE_DB_PATH=audio_annotations.db

# DynamoDB Configuration
DATABASE_MODE=dynamodb
DYNAMODB_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
DYNAMODB_PROJECTS_TABLE=voice_stream_projects
DYNAMODB_ANNOTATIONS_TABLE=voice_stream_annotations
```

#### Automatic Fallback System
- **Smart Error Handling**: If DynamoDB is configured but fails (credentials, network), automatically falls back to SQLite
- **Seamless Operation**: Same API methods work for both database types
- **Zero Downtime**: Application continues running even if cloud database is unavailable

#### Database Schema (Both SQLite & DynamoDB)
**Projects Table:**
- `id` (Primary Key)
- `name` (Project name)
- `description` (Project description)
- `workspace_path` (File system path)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

**Annotations Table:**
- `id` (Primary Key)
- `project_id` (Foreign Key to Projects)
- `filename` (Audio filename)
- `file_path` (Full audio file path)
- `transcript` (Transcribed text)
- `duration` (Audio duration in seconds)
- `recording_mode` (streaming/non-streaming)
- `language` (Audio language)
- `is_deleted` (Soft delete flag)
- `created_at` (Timestamp)
- `updated_at` (Timestamp)

### 💾 Dual Storage Architecture

The application supports **dual storage modes** for flexible file management:

#### Storage Modes
- **Local Storage (Default)**: Files stored on local filesystem
- **AWS S3 Storage**: Cloud storage for scalable, distributed deployments

#### Storage Configuration
```bash
# Local Storage (Default)
STORAGE_MODE=local
LOCAL_STORAGE_PATH=/path/to/storage  # Optional: defaults to current directory

# AWS S3 Storage
STORAGE_MODE=s3
S3_BUCKET_NAME=your-voice-stream-bucket
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_access_key
AWS_SECRET_ACCESS_KEY=your_secret_key
```

#### Storage Features
**Local Storage Benefits:**
- ✅ No cloud dependencies
- ✅ Instant file access
- ✅ No bandwidth costs
- ✅ Perfect for development

**AWS S3 Storage Benefits:**
- ✅ Unlimited scalability
- ✅ Built-in redundancy
- ✅ Global accessibility
- ✅ Automatic backups
- ✅ Cost-effective for large deployments

#### Automatic Storage Management
- **Intelligent Path Resolution**: Handles both local and S3 paths seamlessly
- **Temporary File Handling**: Automatic cleanup of processing files
- **Error Recovery**: Graceful handling of storage failures
- **Cross-Platform Compatibility**: Works on Windows, macOS, and Linux

### 🔄 Deployment Flexibility

#### Development Setup (Recommended)
```bash
# .env configuration for local development
DATABASE_MODE=sqlite
STORAGE_MODE=local
SQLITE_DB_PATH=audio_annotations.db
LOCAL_STORAGE_PATH=./annotation_workspaces
```

#### Production AWS Setup
```bash
# .env configuration for AWS production
DATABASE_MODE=dynamodb
STORAGE_MODE=s3
DYNAMODB_REGION=us-east-1
S3_BUCKET_NAME=voice-stream-production
S3_REGION=us-east-1
AWS_ACCESS_KEY_ID=your_production_key
AWS_SECRET_ACCESS_KEY=your_production_secret
```

#### Hybrid Setup (Database in Cloud, Storage Local)
```bash
# .env configuration for hybrid deployment
DATABASE_MODE=dynamodb
STORAGE_MODE=local
DYNAMODB_REGION=us-east-1
LOCAL_STORAGE_PATH=/mnt/shared/audio
```

---

