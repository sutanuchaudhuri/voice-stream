
from flask import request, jsonify, render_template, Response
from app import app
from flask_socketio import emit
import io
import wave
import uuid
import requests
import os
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

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

@app.route('/', methods=['GET', 'POST'])

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')




# Server-side flag to control voice upload persistence
VOICE_UPLOAD_PERSIST = os.getenv('VOICE_UPLOAD_PERSIST', 'no').lower() == 'yes'

def register_socketio_events(socketio):
    @socketio.on('audio_blob')
    def handle_audio_blob(data):
        import base64
        import sys
        import os
        import json
        sid = request.sid
        print(f"[DEBUG] Received audio_blob event for session: {sid}", file=sys.stderr)
        try:
            # Parse JSON payload
            try:
                payload = json.loads(data)
            except Exception:
                payload = None

            language = 'en'
            question = ''
            is_webm = False
            if payload:
                language = payload.get('language', 'en')
                if 'audio' in payload:
                    # Audio input
                    audio_bytes = io.BytesIO(base64.b64decode(payload['audio']))
                    header = audio_bytes.getbuffer()[:4]
                    is_webm = header == b'\x1A\x45\xDF\xA3'
                    if is_webm:
                        webm_filename = f"uploads/{sid}.webm"
                        with open(webm_filename, "wb") as f:
                            f.write(audio_bytes.getbuffer())
                        print(f"[DEBUG] Saved webm file: {webm_filename}", file=sys.stderr)

                        # Convert webm to wav using ffmpeg for OpenAI transcription
                        import subprocess
                        wav_filename = f"uploads/{sid}.wav"
                        with open(webm_filename, "rb") as webm_in:
                            with open(wav_filename, "wb") as wav_out:
                                subprocess.run([
                                    "ffmpeg", "-y", "-i", "pipe:0", "-ar", "16000", "-ac", "1", "-f", "wav", "pipe:1"
                                ], input=webm_in.read(), stdout=wav_out)
                        print(f"[DEBUG] Saved wav file: {wav_filename}", file=sys.stderr)

                        # Transcribe wav file
                        with open(wav_filename, "rb") as wav_file:
                            transcription = transcribe_audio(wav_file, language)
                        print(f"[DEBUG] Transcription result: {transcription}", file=sys.stderr)
                        question = transcription.get('text', '')
                elif 'text' in payload:
                    # Text input
                    question = payload['text']
            else:
                # Fallback: treat as base64 text
                try:
                    question = base64.b64decode(data).decode('utf-8')
                except Exception:
                    question = ''
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
            socketio.emit('transcription_update', {'question': question, 'answer': answer}, room=sid)

            # Delete files after processing unless persistence is enabled
            if is_webm and not VOICE_UPLOAD_PERSIST:
                try:
                    os.remove(webm_filename)
                    os.remove(wav_filename)
                    print(f"[DEBUG] Deleted files for session: {sid}", file=sys.stderr)
                except Exception as del_err:
                    print(f"[ERROR] Could not delete files: {del_err}", file=sys.stderr)
        except Exception as e:
            print(f"[ERROR] Error handling audio_blob: {e}", file=sys.stderr)
            emit('transcription_update', {'text': 'Error processing audio.'})


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
