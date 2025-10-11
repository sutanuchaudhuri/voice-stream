from flask import request, jsonify, render_template, Response, send_file
from app import app, socketio
from flask_socketio import emit
import io
import requests
import os
import sqlite3
import base64
import time
import json
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Database initialization
def init_annotation_db():
    conn = sqlite3.connect('audio_annotations.db')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_name TEXT UNIQUE NOT NULL,
            description TEXT,
            workspace_path TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS annotations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            project_id INTEGER NOT NULL,
            audio_filename TEXT NOT NULL,
            audio_path TEXT NOT NULL,
            transcript TEXT NOT NULL,
            original_transcript TEXT,
            recording_mode TEXT NOT NULL,
            language TEXT DEFAULT 'en',
            duration REAL,
            deleted TEXT DEFAULT 'N',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects (id)
        )
    ''')

    # Add deleted column to existing tables if it doesn't exist
    try:
        conn.execute('ALTER TABLE annotations ADD COLUMN deleted TEXT DEFAULT "N"')
        conn.commit()
    except sqlite3.OperationalError:
        # Column already exists
        pass

    conn.commit()
    conn.close()

# Initialize database on startup
init_annotation_db()

def transcribe_audio(audio_file, language='en'):
    url = 'https://api.openai.com/v1/audio/transcriptions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    files = {
        'file': ('audio.wav', audio_file, 'audio/wav'),
        'model': (None, 'whisper-1'),
        'language': (None, language)
    }
    r = requests.post(url, headers=headers, files=files)
    return r.json()

# Audio Annotation API Endpoints
@app.route('/api/annotation/projects', methods=['GET'])
def get_projects():
    try:
        conn = sqlite3.connect('audio_annotations.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT p.id, p.project_name, p.description, p.workspace_path, p.created_at,
                   COUNT(CASE WHEN a.deleted IS NULL OR a.deleted = 'N' THEN a.id END) as annotation_count
            FROM projects p
            LEFT JOIN annotations a ON p.id = a.project_id
            GROUP BY p.id, p.project_name, p.description, p.workspace_path, p.created_at
            ORDER BY p.created_at DESC
        ''')
        projects = []
        for row in cursor.fetchall():
            projects.append({
                'id': row[0],
                'project_name': row[1],
                'description': row[2],
                'workspace_path': row[3],
                'created_at': row[4],
                'annotation_count': row[5]
            })
        conn.close()
        return jsonify({'success': True, 'projects': projects})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/annotation/create-project', methods=['POST'])
def create_project():
    try:
        data = request.get_json()
        project_name = data.get('project_name', '').strip()
        description = data.get('description', '').strip()

        if not project_name:
            return jsonify({'success': False, 'error': 'Project name is required'})

        # Create workspace directory
        workspace_path = f"annotation_workspaces/{project_name}"
        os.makedirs(workspace_path, exist_ok=True)
        os.makedirs(f"{workspace_path}/audio", exist_ok=True)

        conn = sqlite3.connect('audio_annotations.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO projects (project_name, description, workspace_path)
            VALUES (?, ?, ?)
        ''', (project_name, description, workspace_path))
        project_id = cursor.lastrowid
        conn.commit()
        conn.close()

        return jsonify({
            'success': True,
            'project_id': project_id,
            'workspace_path': workspace_path
        })
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'error': 'Project name already exists'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/annotation/project/<int:project_id>/annotations', methods=['GET'])
def get_project_annotations(project_id):
    try:
        conn = sqlite3.connect('audio_annotations.db')
        cursor = conn.cursor()
        cursor.execute('''
            SELECT id, audio_filename, transcript, original_transcript, recording_mode,
                   language, duration, created_at, updated_at
            FROM annotations
            WHERE project_id = ? AND (deleted IS NULL OR deleted = 'N')
            ORDER BY created_at DESC
        ''', (project_id,))

        annotations = []
        for row in cursor.fetchall():
            annotations.append({
                'id': row[0],
                'audio_filename': row[1],
                'transcript': row[2],
                'original_transcript': row[3],
                'recording_mode': row[4],
                'language': row[5],
                'duration': row[6],
                'created_at': row[7],
                'updated_at': row[8]
            })
        conn.close()
        return jsonify({'success': True, 'annotations': annotations})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/annotation/save-annotation', methods=['POST'])
def save_annotation():
    try:
        data = request.get_json()
        project_id = data.get('project_id')
        audio_data = data.get('audio_data')  # base64 encoded
        transcript = data.get('transcript')
        recording_mode = data.get('recording_mode', 'start-stop')
        language = data.get('language', 'en')
        duration = data.get('duration', 0)

        if not all([project_id, audio_data, transcript]):
            return jsonify({'success': False, 'error': 'Missing required fields'})

        # Get project workspace path
        conn = sqlite3.connect('audio_annotations.db')
        cursor = conn.cursor()
        cursor.execute('SELECT workspace_path FROM projects WHERE id = ?', (project_id,))
        project = cursor.fetchone()

        if not project:
            conn.close()
            return jsonify({'success': False, 'error': 'Project not found'})

        workspace_path = project[0]

        # Generate unique filename
        timestamp = int(time.time() * 1000)
        audio_filename = f"audio_{timestamp}.wav"
        audio_path = f"{workspace_path}/audio/{audio_filename}"

        # Save audio file
        audio_bytes = base64.b64decode(audio_data)
        with open(audio_path, 'wb') as f:
            f.write(audio_bytes)

        # Save to database
        cursor.execute('''
            INSERT INTO annotations (project_id, audio_filename, audio_path, transcript,
                                   original_transcript, recording_mode, language, duration)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (project_id, audio_filename, audio_path, transcript, transcript,
              recording_mode, language, duration))

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'annotation_id': cursor.lastrowid})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/annotation/audio/<filename>')
def serve_annotation_audio(filename):
    import sys
    try:
        print(f"[DEBUG] Serving audio file: {filename}", file=sys.stderr)

        # Security: ensure filename doesn't contain directory traversal
        if '..' in filename or '/' in filename or '\\' in filename:
            print(f"[ERROR] Invalid filename: {filename}", file=sys.stderr)
            return jsonify({'error': 'Invalid filename'}), 400

        # Find the audio file in any project workspace
        conn = sqlite3.connect('audio_annotations.db')
        cursor = conn.cursor()
        cursor.execute('SELECT audio_path, project_id FROM annotations WHERE audio_filename = ?', (filename,))
        result = cursor.fetchone()
        conn.close()

        if not result:
            print(f"[ERROR] Audio file not found in database: {filename}", file=sys.stderr)
            # Fallback: try to find file in workspace directories
            # Get the project root directory (parent of app directory)
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            annotation_workspaces_path = os.path.join(project_root, 'annotation_workspaces')

            if os.path.exists(annotation_workspaces_path):
                for workspace in os.listdir(annotation_workspaces_path):
                    workspace_path = os.path.join(annotation_workspaces_path, workspace, 'audio')
                    audio_path = os.path.join(workspace_path, filename)
                    if os.path.exists(audio_path):
                        print(f"[INFO] Found audio file in workspace: {audio_path}", file=sys.stderr)
                        return send_file(audio_path, as_attachment=False, mimetype='audio/wav')
            return jsonify({'error': 'Audio file not found'}), 404

        audio_path = result[0]
        print(f"[DEBUG] Audio path from database: {audio_path}", file=sys.stderr)

        # If the path is relative, make it relative to the project root
        if not os.path.isabs(audio_path):
            project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            audio_path = os.path.join(project_root, audio_path)

        if not os.path.exists(audio_path):
            print(f"[ERROR] Audio file not found on disk: {audio_path}", file=sys.stderr)
            return jsonify({'error': 'Audio file not found on disk'}), 404

        print(f"[INFO] Successfully serving audio file: {audio_path}", file=sys.stderr)
        return send_file(audio_path, as_attachment=False, mimetype='audio/wav')

    except Exception as e:
        print(f"[ERROR] Error serving audio: {str(e)}", file=sys.stderr)
        return jsonify({'error': str(e)}), 500

@app.route('/api/annotation/update-transcript', methods=['POST'])
def update_transcript():
    try:
        data = request.get_json()
        annotation_id = data.get('annotation_id')
        transcript = data.get('transcript')

        if not all([annotation_id, transcript]):
            return jsonify({'success': False, 'error': 'Missing required fields'})

        conn = sqlite3.connect('audio_annotations.db')
        cursor = conn.cursor()
        cursor.execute('''
            UPDATE annotations 
            SET transcript = ?, updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (transcript, annotation_id))
        conn.commit()
        conn.close()

        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/annotation/delete-annotation', methods=['POST'])
def delete_annotation():
    try:
        data = request.get_json()
        annotation_id = data.get('annotation_id')

        if not annotation_id:
            return jsonify({'success': False, 'error': 'Annotation ID is required'})

        conn = sqlite3.connect('audio_annotations.db')
        cursor = conn.cursor()

        # Soft delete by setting deleted flag to 'Y'
        cursor.execute('''
            UPDATE annotations 
            SET deleted = 'Y', updated_at = CURRENT_TIMESTAMP
            WHERE id = ?
        ''', (annotation_id,))

        if cursor.rowcount == 0:
            conn.close()
            return jsonify({'success': False, 'error': 'Annotation not found'})

        conn.commit()
        conn.close()

        return jsonify({'success': True, 'message': 'Annotation deleted successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

# TTS endpoint using OpenAI API
@app.route('/tts', methods=['POST'])
def tts():
    text = request.form.get('text')
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    try:
        url = 'https://api.openai.com/v1/audio/speech'
        headers = {
            'Authorization': f'Bearer {OPENAI_API_KEY}',
        }
        data = {
            'model': 'tts-1',
            'input': text,
            'voice': 'alloy',
            'response_format': 'mp3'
        }
        response = requests.post(url, headers=headers, json=data, stream=True)
        def generate():
            for chunk in response.iter_content(chunk_size=4096):
                if chunk:
                    yield chunk
        return Response(generate(), mimetype='audio/mpeg')
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/tts/stream', methods=['POST'])
def tts_stream():
    try:
        data = request.get_json()
        audio_b64 = data.get('audio')
        language = data.get('language', 'en')
        noise_cancellation = data.get('noise_cancellation', False)
        denoised_wav_path = None
        if not audio_b64:
            return jsonify({'error': 'No audio provided'}), 400
        import tempfile
        audio_bytes = base64.b64decode(audio_b64)
        with tempfile.NamedTemporaryFile(suffix='.webm', delete=False) as temp_audio:
            temp_audio.write(audio_bytes)
            temp_audio.flush()
            webm_path = temp_audio.name
        wav_path = webm_path.replace('.webm', '.wav')
        import subprocess
        with open(webm_path, 'rb') as webm_in, open(wav_path, 'wb') as wav_out:
            subprocess.run([
                'ffmpeg', '-y', '-i', 'pipe:0', '-ar', '16000', '-ac', '1', '-f', 'wav', 'pipe:1'
            ], input=webm_in.read(), stdout=wav_out)
        if noise_cancellation:
            denoised_wav_path = wav_path.replace('.wav', '_denoised.wav')
            try:
                import noisereduce as nr
                import librosa
                import soundfile as sf
                audio_data, sample_rate = librosa.load(wav_path, sr=None)
                reduced_noise = nr.reduce_noise(y=audio_data, sr=sample_rate)
                sf.write(denoised_wav_path, reduced_noise, sample_rate)
                wav_path = denoised_wav_path
            except Exception as e:
                print(f"[WARN] Denoising failed: {e}")
        with open(wav_path, 'rb') as wav_file:
            transcription = transcribe_audio(wav_file, language)
        try:
            os.remove(webm_path)
            os.remove(wav_path)
            if noise_cancellation and denoised_wav_path:
                os.remove(denoised_wav_path)
        except Exception:
            pass
        return jsonify({'partial_text': transcription.get('text', '')})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# Speaker diarization utility functions
import torch
import torchaudio
import warnings

warnings.filterwarnings("ignore", message=".*torchaudio._backend.list_audio_backends has been deprecated.*")
warnings.filterwarnings("ignore", message=".*torch.cuda.amp.custom_fwd.*")
warnings.filterwarnings("ignore", message=".*torchaudio.load_with_torchcodec.*")
warnings.filterwarnings("ignore", message=".*torchaudio.save_with_torchcodec.*")
warnings.filterwarnings("ignore", category=FutureWarning, module="speechbrain")
warnings.filterwarnings("ignore", category=UserWarning, module="torchaudio")

from speechbrain.inference import SpeakerRecognition

def diarize_and_transcribe(wav_path, language='en'):
    try:
        verification = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="tmpdir_spkrec"
        )
        waveform, sample_rate = torchaudio.load(wav_path)
        segment_duration = 10.0
        total_duration = waveform.shape[1] / sample_rate
        results = []
        current_speaker_id = 0

        for start_time in range(0, int(total_duration), int(segment_duration)):
            end_time = min(start_time + segment_duration, total_duration)
            segment_wav = f"{wav_path}_segment_{start_time:.2f}_{end_time:.2f}.wav"
            start_sample = int(start_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            segment_audio = waveform[:, start_sample:end_sample]
            torchaudio.save(segment_wav, segment_audio, sample_rate)
            speaker_label = f"SPEAKER_{current_speaker_id % 2}"

            with open(segment_wav, 'rb') as seg_file:
                transcription = transcribe_audio(seg_file, language)
            text = transcription.get('text', '')

            if text.strip():
                results.append({
                    'speaker': speaker_label,
                    'start': start_time,
                    'end': end_time,
                    'text': text
                })

            try:
                os.remove(segment_wav)
            except Exception:
                pass
            current_speaker_id += 1

        return results
    except Exception as e:
        print(f"[WARN] SpeechBrain diarization failed: {e}")
        return simple_segmentation_fallback(wav_path, language)

def simple_segmentation_fallback(wav_path, language='en'):
    try:
        import librosa
        audio_data, sample_rate = librosa.load(wav_path, sr=None)
        total_duration = len(audio_data) / sample_rate
        segment_duration = 15.0
        results = []

        for start_time in range(0, int(total_duration), int(segment_duration)):
            end_time = min(start_time + segment_duration, total_duration)
            start_sample = int(start_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            segment_audio = audio_data[start_sample:end_sample]
            segment_wav = f"{wav_path}_fallback_segment_{start_time:.2f}_{end_time:.2f}.wav"

            import soundfile as sf
            sf.write(segment_wav, segment_audio, sample_rate)

            with open(segment_wav, 'rb') as seg_file:
                transcription = transcribe_audio(seg_file, language)
            text = transcription.get('text', '')

            if text.strip():
                results.append({
                    'speaker': 'SPEAKER_UNKNOWN',
                    'start': start_time,
                    'end': end_time,
                    'text': text
                })

            try:
                os.remove(segment_wav)
            except Exception:
                pass

        return results
    except Exception as e:
        print(f"[ERROR] Fallback segmentation failed: {e}")
        return None

def diarize_and_transcribe_streaming(wav_path, language='en', segment_offset=0):
    try:
        verification = SpeakerRecognition.from_hparams(
            source="speechbrain/spkrec-ecapa-voxceleb",
            savedir="tmpdir_spkrec"
        )
        waveform, sample_rate = torchaudio.load(wav_path)
        chunk_duration = 5.0
        overlap_duration = 2.0
        results = []
        current_time = segment_offset

        while current_time < (waveform.shape[1] / sample_rate):
            end_time = min(current_time + chunk_duration, waveform.shape[1] / sample_rate)
            start_sample = int(current_time * sample_rate)
            end_sample = int(end_time * sample_rate)
            audio_chunk = waveform[:, start_sample:end_sample]

            if audio_chunk.numel() == 0:
                current_time = end_time
                continue

            chunk_wav = f"{wav_path}_chunk_{current_time:.2f}_{end_time:.2f}.wav"
            torchaudio.save(chunk_wav, audio_chunk, sample_rate)

            with open(chunk_wav, 'rb') as wav_file:
                transcription = transcribe_audio(wav_file, language)
            text = transcription.get('text', '')

            speaker_label = f"SPEAKER_{len(results) % 2}"

            if text.strip():
                results.append({
                    'speaker': speaker_label,
                    'start': current_time,
                    'end': end_time,
                    'text': text
                })

            try:
                os.remove(chunk_wav)
            except Exception:
                pass

            current_time += chunk_duration - overlap_duration

        return results
    except Exception as e:
        print(f"[ERROR] Streaming diarization failed: {e}")
        return None

@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

@app.route('/diarization')
def diarization():
    return render_template('diarization.html')

@app.route('/audio-annotation')
def audio_annotation():
    return render_template('audio_annotation.html')

# Server-side flag to control voice upload persistence
VOICE_UPLOAD_PERSIST = os.getenv('VOICE_UPLOAD_PERSIST', 'no').lower() == 'yes'

def register_socketio_events(socketio):
    # Session-based streaming state management
    streaming_sessions = {}

    @socketio.on('audio_blob')
    def handle_audio_blob(data):
        import base64
        import sys
        import os
        import json
        import time
        from flask import request as flask_request
        sid = flask_request.sid if hasattr(flask_request, 'sid') else None
        print(f"[DEBUG] Received audio_blob event for session: {sid}", file=sys.stderr)
        try:
            # Parse JSON payload
            try:
                payload = json.loads(data)
            except Exception:
                payload = None

            language = 'en'
            question = ''
            webm_filename = None
            wav_filename = None
            denoised_wav_filename = None
            is_webm = False
            noise_cancellation = False
            diarization_results = None

            # Check for streaming diarization mode
            streaming_diarization = False
            diarization_only = False
            segment_offset = 0

            if payload:
                language = payload.get('language', 'en')
                noise_cancellation = payload.get('noise_cancellation', False)
                streaming_diarization = payload.get('streaming_diarization', False)
                diarization_only = payload.get('diarization_only', False)
                segment_offset = payload.get('segment_offset', 0)

                print(f"[DEBUG] Mode - streaming: {streaming_diarization}, diarization_only: {diarization_only}", file=sys.stderr)

                if 'audio' in payload:
                    # Audio input
                    audio_bytes = io.BytesIO(base64.b64decode(payload['audio']))
                    header = audio_bytes.getbuffer()[:4]
                    is_webm = header == b'\x1A\x45\xDF\xA3'
                    if is_webm:
                        # Use timestamp for unique filenames in streaming mode
                        timestamp = int(time.time() * 1000)
                        webm_filename = f"uploads/{sid}_{timestamp}.webm"
                        with open(webm_filename, "wb") as f:
                            f.write(audio_bytes.getbuffer())
                        print(f"[DEBUG] Saved webm file: {webm_filename}", file=sys.stderr)

                        # Convert webm to wav using ffmpeg for OpenAI transcription with better Opus handling
                        import subprocess
                        wav_filename = f"uploads/{sid}_{timestamp}.wav"

                        # Use more robust FFmpeg command to handle Opus codec issues
                        ffmpeg_cmd = [
                            "ffmpeg", "-y", "-i", "pipe:0",
                            "-vn",  # No video
                            "-acodec", "pcm_s16le",  # Explicit audio codec
                            "-ar", "16000",  # Sample rate
                            "-ac", "1",  # Mono
                            "-f", "wav",  # Output format
                            "-loglevel", "error",  # Reduce FFmpeg output noise
                            "pipe:1"
                        ]

                        with open(webm_filename, "rb") as webm_in:
                            with open(wav_filename, "wb") as wav_out:
                                result = subprocess.run(
                                    ffmpeg_cmd,
                                    input=webm_in.read(),
                                    stdout=wav_out,
                                    stderr=subprocess.PIPE
                                )
                                if result.returncode != 0:
                                    print(f"[WARN] FFmpeg conversion warning: {result.stderr.decode()}", file=sys.stderr)

                        # Verify the WAV file was created and has content
                        if not os.path.exists(wav_filename) or os.path.getsize(wav_filename) < 1000:
                            print(f"[ERROR] WAV file creation failed or too small", file=sys.stderr)
                            socketio.emit('transcription_update', {'error': 'Audio conversion failed'}, room=sid)
                            return

                        print(f"[DEBUG] Saved wav file: {wav_filename} ({os.path.getsize(wav_filename)} bytes)", file=sys.stderr)

                        # If noise cancellation is requested, run denoising using noisereduce
                        if noise_cancellation:
                            denoised_wav_filename = wav_filename.replace('.wav', '_denoised.wav')
                            try:
                                import noisereduce as nr
                                import librosa
                                import soundfile as sf

                                # Load audio file
                                audio_data, sample_rate = librosa.load(wav_filename, sr=None)

                                # Apply noise reduction
                                reduced_noise = nr.reduce_noise(y=audio_data, sr=sample_rate)

                                # Save denoised audio
                                sf.write(denoised_wav_filename, reduced_noise, sample_rate)
                                wav_filename = denoised_wav_filename
                                print(f"[DEBUG] Audio denoised and saved: {denoised_wav_filename}", file=sys.stderr)
                            except Exception as e:
                                print(f"[WARN] Denoising failed: {e}", file=sys.stderr)

                        # Transcribe wav file - always try transcription first
                        if wav_filename and os.path.exists(wav_filename):
                            try:
                                with open(wav_filename, "rb") as wav_file:
                                    transcription = transcribe_audio(wav_file, language)
                                print(f"[DEBUG] Transcription result: {transcription}", file=sys.stderr)

                                # Extract text from transcription response
                                if transcription and 'text' in transcription:
                                    question = transcription['text'].strip()
                                    print(f"[DEBUG] Extracted transcription text: '{question}'", file=sys.stderr)
                                else:
                                    print(f"[WARN] No text in transcription response: {transcription}", file=sys.stderr)
                                    question = ""

                            except Exception as transcription_error:
                                print(f"[ERROR] Transcription failed: {transcription_error}", file=sys.stderr)
                                question = ""

                        # Try speaker diarization if requested or if we have text
                        if question.strip() and (diarization_only or streaming_diarization):
                            try:
                                diarization_results = diarize_and_transcribe_streaming(wav_filename, language, segment_offset)
                                if diarization_results:
                                    print(f"[DEBUG] Diarization results: {len(diarization_results)} segments", file=sys.stderr)

                                    # For streaming mode, emit specific streaming event
                                    if streaming_diarization:
                                        # Initialize or update session state
                                        if sid not in streaming_sessions:
                                            streaming_sessions[sid] = []

                                        # Add new segments to session
                                        streaming_sessions[sid].extend(diarization_results)

                                        socketio.emit('streaming_diarization_update', {
                                            'diarization': diarization_results,
                                            'accumulated_diarization': streaming_sessions[sid]
                                        }, room=sid)

                                        # Clean up files immediately for streaming
                                        try:
                                            if webm_filename and os.path.exists(webm_filename):
                                                os.remove(webm_filename)
                                            if wav_filename and os.path.exists(wav_filename):
                                                os.remove(wav_filename)
                                            if denoised_wav_filename and os.path.exists(denoised_wav_filename):
                                                os.remove(denoised_wav_filename)
                                        except Exception as del_err:
                                            print(f"[ERROR] Could not delete streaming files: {del_err}", file=sys.stderr)

                                        return  # Exit early for streaming mode

                                    # For file upload diarization-only mode
                                    elif diarization_only:
                                        socketio.emit('transcription_update', {
                                            'question': '',
                                            'answer': '',
                                            'diarization': diarization_results
                                        }, room=sid)

                                        # Clean up files for diarization-only mode
                                        try:
                                            if webm_filename and os.path.exists(webm_filename):
                                                os.remove(webm_filename)
                                            if wav_filename and os.path.exists(wav_filename):
                                                os.remove(wav_filename)
                                            if denoised_wav_filename and os.path.exists(denoised_wav_filename):
                                                os.remove(denoised_wav_filename)
                                        except Exception as del_err:
                                            print(f"[ERROR] Could not delete diarization files: {del_err}", file=sys.stderr)

                                        return  # Exit early for diarization-only mode
                                else:
                                    print(f"[WARN] No diarization results obtained", file=sys.stderr)
                                    if diarization_only:
                                        socketio.emit('transcription_update', {
                                            'error': 'No speakers detected in audio',
                                            'question': '',
                                            'answer': '',
                                            'diarization': []
                                        }, room=sid)
                                        return
                            except Exception as e:
                                print(f"[WARN] Diarization failed: {e}", file=sys.stderr)
                                if diarization_only or streaming_diarization:
                                    socketio.emit('transcription_update', {
                                        'error': f'Diarization failed: {str(e)}',
                                        'question': '',
                                        'answer': '',
                                        'diarization': []
                                    }, room=sid)
                                    return

                        # Regular processing for main app (not diarization-only)
                        if not diarization_only and not streaming_diarization:
                            # Try regular diarization for context
                            if question.strip():
                                try:
                                    diarization_results = diarize_and_transcribe(wav_filename, language)
                                    if diarization_results:
                                        # Compose speaker-labeled transcript
                                        speaker_question = '\n'.join([f"{seg['speaker']}: {seg['text']}" for seg in diarization_results])
                                        print(f"[DEBUG] Using diarization results", file=sys.stderr)
                                        question = speaker_question
                                except Exception as e:
                                    print(f"[WARN] Diarization failed, using basic transcription: {e}", file=sys.stderr)

                            # If we still don't have any question text, that's an error
                            if not question.strip():
                                print(f"[ERROR] No transcription text obtained from audio", file=sys.stderr)
                                socketio.emit('transcription_update', {
                                    'error': 'No speech detected in audio',
                                    'question': '',
                                    'answer': ''
                                }, room=sid)
                                return
                elif 'text' in payload:
                    # Text input
                    question = payload['text']
            else:
                # Fallback: treat as base64 text
                try:
                    question = base64.b64decode(data).decode('utf-8')
                except Exception:
                    question = ''

            # Skip LLM processing for diarization-only or streaming modes
            if diarization_only or streaming_diarization:
                return

            print(f"[DEBUG] Received question: {question} (lang={language})", file=sys.stderr)

            answer = ""
            if question:
                try:
                    from langchain_openai import OpenAI
                    llm = OpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo-instruct")
                    # Insist on answer in the same language as the question
                    if language == 'en':
                        prompt = f"Answer ONLY in English: {question}"
                    elif language == 'hi':
                        prompt = f"उत्तर केवल हिंदी में दें: {question}"
                    elif language == 'es':
                        prompt = f"Responde SOLO en español: {question}"
                    else:
                        prompt = f"Answer in {language}: {question}"
                    answer = llm.invoke(prompt)
                except Exception as llm_error:
                    print(f"[ERROR] LangChain/OpenAI error: {llm_error}", file=sys.stderr)
                    answer = "Error generating answer."
            socketio.emit('transcription_update', {'question': question, 'answer': answer, 'diarization': diarization_results}, room=sid)

            # Delete files after processing unless persistence is enabled
            if is_webm and not VOICE_UPLOAD_PERSIST:
                try:
                    if webm_filename and os.path.exists(webm_filename):
                        os.remove(webm_filename)
                    if wav_filename and os.path.exists(wav_filename):
                        os.remove(wav_filename)
                    if noise_cancellation and denoised_wav_filename and os.path.exists(denoised_wav_filename):
                        os.remove(denoised_wav_filename)
                    print(f"[DEBUG] Deleted files for session: {sid}", file=sys.stderr)
                except Exception as del_err:
                    print(f"[ERROR] Could not delete files: {del_err}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Error handling audio_blob: {e}", file=sys.stderr)
            emit('transcription_update', {'text': 'Error processing audio.'})

    # Audio Annotation System Events
    @socketio.on('annotation_audio_blob')
    def handle_annotation_audio(data):
        import base64
        import sys
        import json
        import time
        from flask import request as flask_request

        sid = flask_request.sid if hasattr(flask_request, 'sid') else None
        print(f"[DEBUG] Received annotation audio for session: {sid}", file=sys.stderr)

        try:
            payload = json.loads(data) if isinstance(data, str) else data

            project_id = payload.get('project_id')
            audio_data = payload.get('audio')
            recording_mode = payload.get('recording_mode', 'start-stop')
            language = payload.get('language', 'en')
            pause_duration = payload.get('pause_duration', 2)

            if not all([project_id, audio_data]):
                socketio.emit('annotation_error', {'error': 'Missing required data'}, room=sid)
                return

            # Convert audio and transcribe
            audio_bytes = io.BytesIO(base64.b64decode(audio_data))
            timestamp = int(time.time() * 1000)
            temp_webm = f"uploads/annotation_temp_{sid}_{timestamp}.webm"
            temp_wav = f"uploads/annotation_temp_{sid}_{timestamp}.wav"

            # Save WebM
            with open(temp_webm, "wb") as f:
                f.write(audio_bytes.getbuffer())

            # Convert to WAV
            import subprocess
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", temp_webm,
                "-acodec", "pcm_s16le", "-ar", "16000", "-ac", "1",
                temp_wav
            ]

            result = subprocess.run(ffmpeg_cmd, capture_output=True)
            if result.returncode != 0:
                socketio.emit('annotation_error', {'error': 'Audio conversion failed'}, room=sid)
                return

            # Transcribe
            with open(temp_wav, 'rb') as wav_file:
                transcription = transcribe_audio(wav_file, language)

            transcript = transcription.get('text', '') if transcription else ''

            # Calculate duration
            duration = 0
            try:
                import librosa
                audio_data_lib, sample_rate = librosa.load(temp_wav, sr=None)
                duration = len(audio_data_lib) / sample_rate
            except Exception:
                duration = 0

            # Emit results back to client
            socketio.emit('annotation_transcription_result', {
                'transcript': transcript,
                'duration': duration,
                'audio_data': base64.b64encode(open(temp_wav, 'rb').read()).decode('utf-8'),
                'recording_mode': recording_mode,
                'language': language
            }, room=sid)

            # Clean up temp files
            try:
                os.remove(temp_webm)
                os.remove(temp_wav)
            except Exception:
                pass

        except Exception as e:
            print(f"[ERROR] Annotation audio processing failed: {e}", file=sys.stderr)
            socketio.emit('annotation_error', {'error': str(e)}, room=sid)

    @socketio.on('disconnect')
    def handle_disconnect(reason=None):
        # Clean up streaming session state on disconnect
        import sys
        from flask import request as flask_request
        sid = flask_request.sid if hasattr(flask_request, 'sid') else None
        if sid and sid in streaming_sessions:
            del streaming_sessions[sid]
            print(f"[DEBUG] Cleaned up streaming session: {sid} (reason: {reason})", file=sys.stderr)
        else:
            print(f"[DEBUG] Disconnect event for session: {sid} (reason: {reason})", file=sys.stderr)

# Socket.IO handlers for audio annotation
@socketio.on('annotation_audio_blob')
def handle_audio_blob(data):
    try:
        data = json.loads(data)
        audio_data = data.get('audio')
        project_id = data.get('project_id')
        recording_mode = data.get('recording_mode', 'start-stop')
        language = data.get('language', 'en')

        if not audio_data:
            emit('annotation_error', {'error': 'No audio data received'})
            return

        # Decode audio data
        audio_bytes = base64.b64decode(audio_data)

        # Transcribe audio
        try:
            result = transcribe_audio(io.BytesIO(audio_bytes), language)
            transcript = result.get('text', 'No transcription available')

            # Calculate duration (rough estimate)
            duration = len(audio_bytes) / (44100 * 2)  # Assuming 44.1kHz, 16-bit

            emit('annotation_transcription_result', {
                'transcript': transcript,
                'audio_data': audio_data,
                'duration': duration,
                'recording_mode': recording_mode,
                'language': language
            })
        except Exception as e:
            emit('annotation_error', {'error': f'Transcription failed: {str(e)}'})

    except Exception as e:
        emit('annotation_error', {'error': f'Processing failed: {str(e)}'})

# Register all SocketIO events
register_socketio_events(socketio)

