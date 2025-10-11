# Voice Stream Application - Troubleshooting Guide

## Audio Annotation System Issues

### Problem: Audio files in Project Annotations appear disabled/unclickable

**Symptoms:**
- Navigate to `http://localhost:5050/audio-annotation`
- Select a project with existing recordings
- Audio files are displayed in the annotations grid but appear disabled
- Cannot click to play or download audio files

### Root Cause Analysis:

This issue typically occurs when the backend API endpoints for serving audio files are missing or not properly configured. The frontend expects specific endpoints to be available for audio playback and download functionality.

### Required Backend Endpoints:

The audio annotation system requires these API endpoints to function properly:

1. **Audio Serving Endpoint**: `/api/annotation/audio/<filename>`
   - Purpose: Serves audio files for browser playback and download
   - Expected Response: Audio file with proper MIME type (`audio/wav`)

2. **Project Management Endpoints**:
   - `/api/annotation/projects` (GET) - Lists all projects
   - `/api/annotation/project/<id>/annotations` (GET) - Lists annotations for a project

### Verification Steps:

1. **Check if server is running:**
   ```bash
   curl -i http://localhost:5050/api/annotation/projects
   ```
   Expected: HTTP 200 response with JSON containing projects list

2. **Test audio endpoint directly:**
   ```bash
   curl -i http://localhost:5050/api/annotation/audio/[FILENAME]
   ```
   Replace `[FILENAME]` with an actual audio filename from your database
   Expected: HTTP 200 response with audio file content

3. **Check browser developer console:**
   - Open browser dev tools (F12)
   - Go to Network tab
   - Try clicking on an audio file
   - Look for failed requests (404, 500 errors)

### Common Solutions:

#### Solution 1: Restart the Flask Server
```bash
cd /Users/sutanuchaudhuri/Developer/Python/voice-stream
python run.py
```

#### Solution 2: Verify Database and File Structure
Check that your annotation workspaces exist:
```bash
ls -la annotation_workspaces/
ls -la annotation_workspaces/[PROJECT_NAME]/audio/
```

#### Solution 3: Check Audio File Paths
Verify that audio file paths in the database match actual file locations:
- Open `audio_annotations.db` 
- Check the `annotations` table for correct `audio_path` values
- Ensure files exist at those paths

#### Solution 4: Browser Cache Issues
- Clear browser cache and cookies
- Try opening in incognito/private browsing mode
- Hard refresh the page (Ctrl+F5 or Cmd+Shift+R)

### Advanced Debugging:

#### Check Flask Routes Registration
If the server starts but endpoints don't work, verify routes are registered:
```python
# In your Flask app, you can list all routes:
from flask import Flask
app = Flask(__name__)
print(app.url_map)
```

#### Database Connection Issues
```bash
# Check if database file exists and is accessible
ls -la audio_annotations.db
sqlite3 audio_annotations.db "SELECT * FROM annotations LIMIT 5;"
```

#### File Permissions
```bash
# Ensure proper file permissions
chmod 644 audio_annotations.db
chmod -R 755 annotation_workspaces/
```

### Expected Behavior:

When working correctly:
1. Audio files in the grid should be clickable
2. Clicking an audio file should start playback in the browser
3. Right-click should offer download option
4. Browser's built-in audio controls should appear
5. No 404 or 500 errors in browser console

### Error Patterns to Look For:

#### In Browser Console:
- `404 Not Found` for `/api/annotation/audio/*` requests
- `500 Internal Server Error` responses
- CORS errors
- Network timeout errors

#### In Flask Server Logs:
- `AssertionError: View function mapping is overwriting an existing endpoint function`
- Database connection errors
- File not found errors for audio files

### Prevention:

1. **Regular Backups**: Keep backups of your `audio_annotations.db` file
2. **File Organization**: Maintain consistent workspace folder structure
3. **Server Monitoring**: Check server logs regularly for errors
4. **Testing**: Test audio playback after each new recording

### Related Files:

- `app/routes.py` - Contains API endpoint definitions
- `audio_annotations.db` - SQLite database with project and annotation metadata
- `annotation_workspaces/*/audio/` - Actual audio file storage
- `app/templates/audio_annotation.html` - Frontend interface

### Getting Help:

If these solutions don't resolve the issue:
1. Check the Flask server terminal output for error messages
2. Examine browser developer console for JavaScript errors
3. Verify all required Python dependencies are installed
4. Ensure FFmpeg is properly installed and accessible

---

## Other Common Issues

### Server Won't Start
- Check if port 5050 is already in use
- Verify Python virtual environment is activated
- Install missing dependencies: `pip install -r requirements.txt`

### Recording Issues
- Check microphone permissions in browser
- Verify FFmpeg is installed and in PATH
- Test with different browsers (Chrome, Firefox, Safari)

### Transcription Failures
- Verify OpenAI API key is set in `.env` file
- Check internet connectivity
- Ensure audio files are in supported formats

---

*Last updated: October 2025*
