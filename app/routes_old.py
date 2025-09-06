from flask import request, jsonify, render_template
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

@app.route('/', methods=['GET', 'POST'])

@app.route('/', methods=['GET'])
def index():
    return render_template('index.html')



# One-time audio upload and transcription



def register_socketio_events(socketio):
    @socketio.on('audio_blob')
    def handle_audio_blob(data):
        import base64
        import sys
        sid = request.sid
        print(f"[DEBUG] Received audio_blob event for session: {sid}", file=sys.stderr)
        try:
            audio_bytes = io.BytesIO(base64.b64decode(data))
            # Save raw webm for debugging
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
                transcription = transcribe_audio(wav_file)
            print(f"[DEBUG] Transcription result: {transcription}", file=sys.stderr)
            question = transcription.get('text', '')
            answer = ""
            if question:
                try:
                    from langchain_openai import OpenAI
                    llm = OpenAI(openai_api_key=OPENAI_API_KEY, model_name="gpt-3.5-turbo-instruct")
                    prompt = f"Answer in English: {question}"
                    answer = llm.invoke(prompt)
                except Exception as llm_error:
                    print(f"[ERROR] LangChain/OpenAI error: {llm_error}", file=sys.stderr)
                    answer = "Error generating answer."
            socketio.emit('transcription_update', {'question': question, 'answer': answer}, room=sid)
        except Exception as e:
            print(f"[ERROR] Error handling audio_blob: {e}", file=sys.stderr)
            emit('transcription_update', {'text': 'Error processing audio.'})


def transcribe_audio(audio_file):
    url = 'https://api.openai.com/v1/audio/transcriptions'
    headers = {
        'Authorization': f'Bearer {OPENAI_API_KEY}'
    }
    files = {
        'file': ('audio.wav', audio_file, 'audio/wav'),
        'model': (None, 'whisper-1'),
        'language': (None, 'en')
    }
    r = requests.post(url, headers=headers, files=files)
    return r.json()
