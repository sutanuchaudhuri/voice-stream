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

## 📤 Data Export System

The Audio Annotation System includes a comprehensive export functionality that allows you to download all your project data in a structured format. This feature is essential for data analysis, backup, sharing, and integration with other systems.

### Export Features

- **🗜️ ZIP Package Export**: Complete project data packaged in a single downloadable ZIP file
- **📊 CSV Data Export**: Structured annotation data in CSV format for easy analysis
- **🎵 Audio File Package**: All available audio files included in the export
- **📋 Detailed Documentation**: README file explaining the export contents
- **⚠️ Missing File Handling**: Graceful handling of missing audio files with status tracking
- **🔍 Comprehensive Metadata**: Full annotation history and project information

### How to Export Project Data

1. **Navigate to Audio Annotation System**: Go to `/audio-annotation` in your application
2. **Select a Project**: Load the project you want to export
3. **Click Export Data**: Use the "Export Data" button in the annotations section
4. **Download Automatically**: ZIP file downloads automatically with timestamped filename

### Export Package Contents

When you export a project, you receive a ZIP file containing:

```
project_name_export_YYYYMMDD_HHMMSS.zip
├── project_name_annotations.csv          # Complete annotation data
├── audio_files/                          # Folder containing audio files
│   ├── audio_1760145662474.wav          # Individual audio recordings
│   ├── audio_1760145711771.wav
│   └── ...
└── README.txt                           # Export documentation
```

### CSV Schema and Structure

The exported CSV file contains comprehensive annotation data with the following columns:

#### CSV Column Definitions

| Column Name | Data Type | Description | Example |
|-------------|-----------|-------------|---------|
| `audio_filename` | String | Name of the audio file | `audio_1760145662474.wav` |
| `transcription` | String | Current transcript text | `"My name is Sutanu Chaudhuri."` |
| `original_transcript` | String | Original transcript before any edits | `"My name is Sutanu Chaudhuri."` |
| `duration_seconds` | Float | Audio duration in seconds | `2.52` |
| `language` | String | Language code used for transcription | `en`, `hi`, `es` |
| `recording_mode` | String | How the audio was recorded | `start-stop`, `streaming`, `batch-audio` |
| `created_date` | DateTime | When annotation was first created | `2025-10-11 01:21:51` |
| `updated_date` | DateTime | When annotation was last modified | `2025-10-11 01:21:59` |
| `file_status` | String | Audio file availability status | `found`, `missing` |

#### Sample CSV Data

```csv
audio_filename,transcription,original_transcript,duration_seconds,language,recording_mode,created_date,updated_date,file_status
audio_1760145662474.wav,"Let's create an annotation","Let's create an annotation",2.34,en,start-stop,2025-10-11 01:21:02,2025-10-11 03:52:27,found
audio_1760145711771.wav,"My name is Sutanu Chaudhuri.","My name is Sutanu Chaudhuri.",2.52,en,start-stop,2025-10-11 01:21:51,2025-10-11 01:21:59,missing
audio_1760145775610.wav,"My wife's name is Sutapa Chaudhuri.","My wife's name is Sutapa Chaudhuri.",8.34,en,start-stop,2025-10-11 01:22:55,2025-10-11 02:42:54,found
```

### File Status Tracking

The export system intelligently handles missing audio files:

- **`found`**: Audio file successfully located and included in export
- **`missing`**: Audio file referenced in database but not found on filesystem

#### Missing File Scenarios

Audio files may be missing due to:
- Manual file deletion from filesystem
- Storage migration or cleanup
- Corrupted file systems
- Network storage disconnection

**Important**: Even if audio files are missing, their annotation data and transcriptions are preserved and included in the CSV export.

### Export Processing Details

#### Audio File Resolution Process

1. **Storage Manager Lookup**: First attempts to load via configured storage system (local/S3)
2. **Local Filesystem Fallback**: Searches local project directories if storage manager fails
3. **Path Resolution**: Handles both absolute and relative file paths
4. **Status Logging**: Detailed logging of found vs missing files

#### Export Statistics

Each export includes a summary in the README.txt file:

```
Audio Annotation Export - project_name
=================================================

Export Date: 2025-10-11 14:30:25
Project: test_project
Total Annotations: 4
Audio Files Found: 2
Audio Files Missing: 2

Contents:
- test_project_annotations.csv: All annotation data with transcriptions
- audio_files/: Audio files that were found and successfully copied

Note: Some audio files may be missing from the file system but their
annotations and transcriptions are still included in the CSV file.
```

### API Endpoint

The export functionality is available via REST API:

```bash
GET /api/annotation/export-project/<project_id>
```

**Response**: ZIP file download with content-type `application/zip`

### Data Integration

The exported CSV format is designed for easy integration with:

- **📊 Data Analysis Tools**: Excel, Google Sheets, R, Python pandas
- **🤖 Machine Learning Pipelines**: Training data for speech recognition models
- **📈 Business Intelligence**: Tableau, Power BI, or custom dashboards
- **🔄 Data Migration**: Moving data between Voice Stream instances
- **📋 Audit and Compliance**: Complete audit trail of annotation activities

### Export Best Practices

#### For Data Analysis
- Use `duration_seconds` to calculate total audio content
- Filter by `language` for language-specific analysis
- Track `recording_mode` to understand data collection methods
- Compare `created_date` vs `updated_date` to identify edited annotations

#### For Backup and Migration
- Export regularly to ensure data backup
- Verify `file_status` to identify missing audio files before migration
- Use timestamps to track data freshness
- Store exports in version control or backup systems

#### For Quality Assurance
- Review `original_transcript` vs `transcription` for editing patterns
- Monitor `file_status` for data integrity issues
- Track annotation creation patterns over time
- Identify frequently edited transcriptions for quality improvement

### Troubleshooting Export Issues

#### Common Issues and Solutions

1. **Empty ZIP File**: 
   - Check if project has annotations
   - Verify project ID is correct
   - Ensure database connectivity

2. **Missing Audio Files**:
   - Check file system permissions
   - Verify storage configuration
   - Review file paths in database

3. **Large Export Times**:
   - Export during low-usage periods
   - Consider chunked exports for large projects
   - Check available disk space

4. **CSV Encoding Issues**:
   - CSV files use UTF-8 encoding
   - Ensure proper encoding when opening in Excel
   - Use text import wizard for special characters

---
